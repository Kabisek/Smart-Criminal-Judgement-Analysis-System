# Deploy the backend on Hugging Face Spaces (Docker, free tier)

This guide deploys **only the FastAPI backend** (`backend/`). Your Expo/React Native frontend stays separate: point it at the Space URL (see step 7).

## What you need before you start

- A [Hugging Face](https://huggingface.co) account.
- Your **Google Drive** zip links and **MongoDB Atlas** URI (or another reachable MongoDB).
- API keys you already use locally (`GOOGLE_API_KEY`, `LLM_PROVIDER`, etc.) — set them as **Secrets** in the Space, not in Git.

## Architecture on HF

1. User or your mobile app calls `https://YOUR_USERNAME-YOUR_SPACE.hf.space/...`
2. The container starts `uvicorn` on port **7860** (required by Spaces).
3. On first run, `runtime_artifacts.py` may **download** your Drive zips (if `FETCH_RUNTIME_ARTIFACTS` and `GDRIVE_URL_*` are set) and unzip into `/app/backend/...`.
4. The API behaves like your local server (`/health`, `/api/v1/...`, `/comp4/...`).

**Cold start:** The first boot after a deploy can take **many minutes** while large files download. Later restarts are faster if the platform keeps disk (see limitations below).

---

## Step 1 — Put this repo on GitHub (or GitLab)

HF Spaces can build from a GitHub repo.

1. Commit the **`Dockerfile`**, **`.dockerignore`**, and **`backend/`** code.
2. Do **not** commit `.env` or large model folders (they are in `.gitignore`).

---

## Step 2 — Create a new Space on Hugging Face

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2. **Space name:** e.g. `criminal-judgement-api`.
3. **SDK:** choose **Docker** (not Gradio).
4. **Visibility:** Public (free) or Private (if your plan allows).
5. **Hardware:** CPU basic (free). For heavier loads, upgrade later.
6. Create the Space, then connect it to your GitHub repository and select the branch that contains the `Dockerfile` at the **repository root** (same layout as this project: `Dockerfile` next to `backend/`).

HF will build from the **`Dockerfile`** in the repo root.

---

## Step 3 — Configure environment variables (Secrets)

In the Space: **Settings → Variables and secrets**.

Add **Repository secrets** (values hidden) for anything sensitive:

| Name | Purpose |
|------|--------|
| `FETCH_RUNTIME_ARTIFACTS` | `1` to download Drive zips when markers are missing |
| `GDRIVE_URL_CHROMA_COMP1` | (and other `GDRIVE_URL_*` you use) |
| `MONGODB_URI` | MongoDB Atlas connection string |
| `GOOGLE_API_KEY` | Gemini / Google APIs for comp1/comp2 |
| `GOOGLE_API_KEY_COMP2` | If you split keys |
| `LLM_PROVIDER` | e.g. `google` |
| `GROQ_API_KEY` | If you use Groq |
| `OPENROUTER_API_KEY` | If used |

Copy the same names from your local `backend/.env.example` and your working `.env`.

**Important:** Do not paste secrets into the Dockerfile or into public files.

---

## Step 4 — MongoDB Atlas network access

Atlas must allow connections from the internet. For development you often use **Network Access → Allow access from anywhere** (`0.0.0.0/0`). Hugging Face egress IPs are not a single fixed IP on the free tier, so restricting by IP is awkward until you use a fixed egress product.

---

## Step 5 — Build and logs

1. After you push to the connected branch, HF builds the Docker image (first time can take **10–20+ minutes** because of PyTorch and dependencies).
2. Open **Logs** on the Space. When the container runs, you should see `[runtime_artifacts]` lines if downloads start, then uvicorn listening on `7860`.

**If the build fails:** open the **Build** log; often it is out-of-memory during `pip install`. Retry, or use a smaller base image / fewer deps only if you refactor (not required for a first try).

**If the app crashes on import:** check that all required env vars are set and that Drive links are still “anyone with the link can view”.

---

## Step 6 — Test the API

Your public API root is roughly:

`https://<YOUR_HF_USERNAME>-<YOUR_SPACE_NAME>.hf.space`

Examples:

- Health: `GET https://<...>.hf.space/health`
- OpenAPI docs: `https://<...>.hf.space/docs`

Use curl or a browser for `/health` first.

---

## Step 7 — Point the frontend at the Space

In `frontend/api.ts` you currently use `http://127.0.0.1:8000`. For production, use your Space URL with **HTTPS**:

```text
https://<YOUR_HF_USERNAME>-<YOUR_SPACE_NAME>.hf.space
```

Build the app with that base URL (environment variable or build-time config). Enable CORS if the browser blocks calls — your `main.py` already uses `allow_origins=["*"]` for development; tighten for production if needed.

---

## Limitations and tips (free tier)

1. **Disk:** Ephemeral storage may reset; you might **re-download** Drive zips after sleeps or redeploys unless you use persistent add-ons or cache elsewhere.
2. **RAM / CPU:** Large models are tight on free CPU; inference can be slow or OOM. Monitor Logs.
3. **Startup time:** `ensure_runtime_artifacts()` runs **before** the app finishes loading modules; a very long download can delay the process appearing “up”. If HF kills the process, consider smaller artifacts, fewer components, or hosting heavy models on HF Hub + `huggingface_hub` instead of Drive.
4. **Whisper / GPU:** Free CPU only unless you select a GPU Space (paid).

---

## Optional: README card on Hugging Face

The root `README.md` includes YAML **frontmatter** so the Space card shows a title and emoji. Edit the `title` / `emoji` fields if you like.

---

## Quick checklist

- [ ] `Dockerfile` and `.dockerignore` at repo root  
- [ ] `backend/` committed without secrets or huge binaries  
- [ ] Space = Docker SDK, port **7860**  
- [ ] All secrets set in Space settings  
- [ ] MongoDB allows your deployment’s connections  
- [ ] `/health` returns 200  
- [ ] Frontend `API_BASE` updated to `https://...hf.space`  
