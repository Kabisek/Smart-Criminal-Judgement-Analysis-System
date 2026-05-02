# Hugging Face Git: large / binary files

Hugging Face may **reject pushes** that contain **large blobs** and/or **binary artifacts** (`.pdf`, `.pkl`, `.npy`, `.faiss`, etc.), and suggest [Git Xet](https://huggingface.co/docs/hub/xet/using-xet-storage#git). This project instead keeps the **repo source-only** and loads weights via **`runtime_artifacts.py`** + Google Drive.

## Remove binaries from history (what this repo uses)

From the project root:

```powershell
pip install git-filter-repo

git filter-repo --force `
  --path backend/data/judgments --invert-paths `
  --path backend/data/features --invert-paths `
  --path backend/data/evaluation --invert-paths `
  --path backend/data/models --invert-paths `
  --path backend/comp4/data_component_4 --invert-paths `
  --path-regex "^backend/comp3/.*\.(npy|pkl|png)$" --invert-paths
```

`git filter-repo` **removes `origin`**. Restore remotes:

```powershell
git remote add origin https://github.com/Kabisek/Smart-Criminal-Judgement-Analysis-System.git
git remote add hf https://huggingface.co/spaces/Kabisek/Smart_criminal_judgement
```

Optional extra pass (older histories): `git filter-repo --strip-blobs-bigger-than 9M --force`

Then force-push **both** (history changed):

```powershell
git push origin main --force
git push hf main --force
```

## Runtime on HF

- Set **`FETCH_RUNTIME_ARTIFACTS=1`** and the **`GDRIVE_URL_*`** secrets in the Space (see `backend/runtime_artifacts.py`).
- **Component 3:** zip the `.pkl` / `.npy` files that lived under `backend/comp3/` (see `comp3/api/config.py`), upload to Drive, set **`GDRIVE_URL_COMP3_ARTIFACTS`**.

## Tokens

Never paste Hugging Face tokens in chat. Revoke leaked tokens and create a new one.
