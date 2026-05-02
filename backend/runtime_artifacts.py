"""
Download large runtime artifacts (models, ChromaDB stores) from Google Drive at deploy time.

GitHub-friendly workflow
------------------------
1. Zip each artifact locally (see layout below).
2. Upload each zip to Google Drive; set sharing to "Anyone with the link" (viewer).
3. Put the file link or raw id in backend/.env (see env var names below).
4. Set FETCH_RUNTIME_ARTIFACTS=1 before starting uvicorn (or rely on per-URL vars:
   any GDRIVE_URL_* set will fetch that artifact if its marker file is missing).

Zip layout
----------
Either:
  A) Zip the *contents* of the folder (recommended): e.g. inside chroma_db run
     zip -r ../chroma_comp1.zip .
  B) Zip a single top-level folder; this module unwraps one directory level automatically.
  C) Double-nested folders (e.g. all-MiniLM-L6-v2/all-MiniLM-L6-v2/config.json) are
     flattened automatically up to several levels.
  D) macOS zips often include __MACOSX next to the real folder; that junk is removed
     so unwrap still works.

Env vars (each optional; only used if the marker path is missing)
-----------------------------------------------------------------
  FETCH_RUNTIME_ARTIFACTS=1     Master switch: skip all downloads if unset/0 and no GDRIVE_URL_* set.

  GDRIVE_URL_CHROMA_COMP1       → backend/data/chroma_db/        (Component 1 API / main.py)
  GDRIVE_URL_CHROMA_COMP2       → backend/data/chroma_db_comp2/
  GDRIVE_URL_CHROMA_COMP1_BUILD → comp1/data/chroma_db/          (comp1/scripts/build_db.py output)
  GDRIVE_URL_SRI_LANKA_LEGAL_BERT → comp1/models/sri_lanka_legal_bert/
  GDRIVE_URL_NLLB_MERGED        → comp4/model_Component_ 4/nllb-merged/
  GDRIVE_URL_COMP4_EMBED        → comp4/model_Component_ 4/all-MiniLM-L6-v2/
  GDRIVE_URL_COMP4_DATA         → comp4/data_component_4/        (FAISS + jsonl; exclude cache.sqlite)
  GDRIVE_URL_COMP3_ARTIFACTS    → comp3/  (.pkl + .npy for AppealPredictor; CSVs stay in Git)

cache.sqlite is not downloaded; Component 4 creates it locally.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Callable, List, Optional

# backend/ directory (this file lives next to main.py)
BACKEND_ROOT = Path(__file__).resolve().parent


def _marker_exists(path: Path) -> bool:
    return path.is_file()


def _smart_extract_zip(zip_path: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_path)
        entries = list(tmp_path.iterdir())
        if len(entries) == 1 and entries[0].is_dir():
            root = entries[0]
            for child in root.iterdir():
                target = dest_dir / child.name
                if target.exists():
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                shutil.move(str(child), str(target))
        else:
            for child in entries:
                target = dest_dir / child.name
                if target.exists():
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                shutil.move(str(child), str(target))


def _remove_macosx_trees(root: Path) -> None:
    """Remove __MACOSX folders from ZIPs created on macOS (they break single-folder unwrap)."""
    root = root.resolve()
    if not root.is_dir():
        return
    to_remove = sorted(
        (p for p in root.rglob("__MACOSX") if p.is_dir()),
        key=lambda p: -len(p.parts),
    )
    for p in to_remove:
        shutil.rmtree(p, ignore_errors=True)


def _junk_name(name: str) -> bool:
    return name in (".", "..", "__MACOSX") or name.startswith("._")


def _visible_children(d: Path) -> List[Path]:
    return [p for p in d.iterdir() if not _junk_name(p.name)]


def _move_dir_contents_up(inner: Path, dest_dir: Path) -> None:
    for item in list(inner.iterdir()):
        if _junk_name(item.name):
            continue
        target = dest_dir / item.name
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        shutil.move(str(item), str(target))
    try:
        inner.rmdir()
    except OSError:
        shutil.rmtree(inner, ignore_errors=True)


def _promote_nested_single_dir(dest_dir: Path, marker: Path, max_rounds: int = 16) -> None:
    """
    If the marker file is still missing, repeatedly move contents out of a lone
    subdirectory. Skips __MACOSX / AppleDouble junk so Mac-made zips still unwrap.
    """
    dest_dir = dest_dir.resolve()
    marker = marker.resolve()
    for _ in range(max_rounds):
        if _marker_exists(marker):
            return
        if not dest_dir.is_dir():
            return
        _remove_macosx_trees(dest_dir)
        children = _visible_children(dest_dir)
        if len(children) != 1 or not children[0].is_dir():
            break
        _move_dir_contents_up(children[0], dest_dir)


def _relocate_sentence_transformer_bundle(dest_dir: Path, marker: Path) -> None:
    """
    If config.json lives under a subfolder (e.g. only nested bundle), move that
    folder's contents to dest_dir. Detects saved SentenceTransformer trees via modules.json.
    """
    dest_dir = dest_dir.resolve()
    marker = marker.resolve()
    if _marker_exists(marker):
        return
    _remove_macosx_trees(dest_dir)
    # Saved SentenceTransformer models always have modules.json next to config.json
    for modules_json in dest_dir.rglob("modules.json"):
        bundle = modules_json.parent
        if not (bundle / "config.json").is_file():
            continue
        if bundle.resolve() == dest_dir:
            return
        _move_dir_contents_up(bundle, dest_dir)
        if _marker_exists(marker):
            return
    # One-level subfolder with full model files (avoid rglob into 0_Transformer/, etc.)
    if not _marker_exists(marker):
        for sub in dest_dir.iterdir():
            if not sub.is_dir() or _junk_name(sub.name):
                continue
            if (sub / "config.json").is_file() and (
                (sub / "model.safetensors").is_file() or (sub / "pytorch_model.bin").is_file()
            ):
                _move_dir_contents_up(sub, dest_dir)
                return


def _download_gdrive(url: str, dest_file: Path) -> None:
    import gdown

    dest_file.parent.mkdir(parents=True, exist_ok=True)
    gdown.download(url, str(dest_file), quiet=False, fuzzy=True)


class Artifact:
    __slots__ = ("name", "env_url", "marker", "prepare_dest")

    def __init__(
        self,
        name: str,
        env_url: str,
        marker: Path,
        prepare_dest: Optional[Callable[[Path], None]] = None,
    ):
        self.name = name
        self.env_url = env_url
        self.marker = marker
        self.prepare_dest = prepare_dest


def _artifacts() -> List[Artifact]:
    m = BACKEND_ROOT
    comp4_model = m / "comp4" / "model_Component_ 4"
    return [
        Artifact(
            "chroma_db (Component 1 runtime)",
            "GDRIVE_URL_CHROMA_COMP1",
            m / "data" / "chroma_db" / "chroma.sqlite3",
            lambda p: (p.parent).mkdir(parents=True, exist_ok=True),
        ),
        Artifact(
            "chroma_db_comp2",
            "GDRIVE_URL_CHROMA_COMP2",
            m / "data" / "chroma_db_comp2" / "chroma.sqlite3",
            lambda p: (p.parent).mkdir(parents=True, exist_ok=True),
        ),
        Artifact(
            "chroma_db (comp1 build_db output)",
            "GDRIVE_URL_CHROMA_COMP1_BUILD",
            m / "comp1" / "data" / "chroma_db" / "chroma.sqlite3",
            lambda p: (p.parent).mkdir(parents=True, exist_ok=True),
        ),
        Artifact(
            "sri_lanka_legal_bert",
            "GDRIVE_URL_SRI_LANKA_LEGAL_BERT",
            m / "comp1" / "models" / "sri_lanka_legal_bert" / "model.safetensors",
            lambda p: (p.parent).mkdir(parents=True, exist_ok=True),
        ),
        Artifact(
            "nllb-merged (Component 4)",
            "GDRIVE_URL_NLLB_MERGED",
            comp4_model / "nllb-merged" / "model.safetensors",
            lambda p: (p.parent).mkdir(parents=True, exist_ok=True),
        ),
        Artifact(
            "comp4 sentence-transformers embed",
            "GDRIVE_URL_COMP4_EMBED",
            comp4_model / "all-MiniLM-L6-v2" / "config.json",
            lambda p: (p.parent).mkdir(parents=True, exist_ok=True),
        ),
        Artifact(
            "comp4 retrieval data (FAISS + metadata)",
            "GDRIVE_URL_COMP4_DATA",
            m / "comp4" / "data_component_4" / "index.faiss",
            lambda p: (p.parent).mkdir(parents=True, exist_ok=True),
        ),
        Artifact(
            "comp3 appeal models (.pkl + .npy; Hugging Face Git rejects binaries)",
            "GDRIVE_URL_COMP3_ARTIFACTS",
            m / "comp3" / "improved_ensemble_model.pkl",
            lambda p: (p.parent).mkdir(parents=True, exist_ok=True),
        ),
    ]


def ensure_runtime_artifacts() -> None:
    """
    For each artifact: if env URL is set and marker file is missing, download zip from Drive and extract.
    """
    master = os.getenv("FETCH_RUNTIME_ARTIFACTS", "").strip().lower() in ("1", "true", "yes")
    any_url = any(os.getenv(a.env_url, "").strip() for a in _artifacts())
    if not master and not any_url:
        return

    for art in _artifacts():
        url = os.getenv(art.env_url, "").strip()
        if not url:
            continue
        if _marker_exists(art.marker):
            print(f"[runtime_artifacts] OK {art.name} — present at {art.marker}")
            continue
        if art.prepare_dest:
            art.prepare_dest(art.marker)
        print(f"[runtime_artifacts] Fetching {art.name} …")
        with tempfile.TemporaryDirectory() as td:
            zpath = Path(td) / f"{art.env_url}.zip"
            _download_gdrive(url, zpath)
            if not zpath.is_file() or zpath.stat().st_size == 0:
                raise RuntimeError(f"[runtime_artifacts] Download failed or empty: {art.name}")
            dest = art.marker.parent
            _smart_extract_zip(zpath, dest)
            _remove_macosx_trees(dest)
            _promote_nested_single_dir(dest, art.marker)
            if art.env_url == "GDRIVE_URL_COMP4_EMBED":
                _relocate_sentence_transformer_bundle(dest, art.marker)
        if not _marker_exists(art.marker):
            raise RuntimeError(
                f"[runtime_artifacts] After extract, marker still missing: {art.marker} "
                f"(check zip layout for {art.name})"
            )
        print(f"[runtime_artifacts] Installed {art.name} → {dest}")


if __name__ == "__main__":
    os.environ.setdefault("FETCH_RUNTIME_ARTIFACTS", "1")
    ensure_runtime_artifacts()
