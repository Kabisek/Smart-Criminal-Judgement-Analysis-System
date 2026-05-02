import os
from huggingface_hub import HfApi

# Configuration
REPO_ID = "Divanka/smart-criminal-judgement-api"
TOKEN = "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"
REPO_TYPE = "space"

api = HfApi(token=TOKEN)

def upload_folder_forced(local_path, path_in_repo):
    print(f"Uploading {local_path} to {path_in_repo}...")
    try:
        api.upload_folder(
            folder_path=local_path,
            path_in_repo=path_in_repo,
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            ignore_patterns=["__pycache__", "*.pyc", ".git", ".venv", ".env"] # Selective ignore
        )
        print(f"Successfully uploaded {local_path}")
    except Exception as e:
        print(f"Error uploading {local_path}: {e}")

if __name__ == "__main__":
    print("--- Starting Targeted Backup ---")

    
    # 4. Global Data (JSON sources / ChromaDB stores)
    if os.path.exists("data"):
        upload_folder_forced("data", "data")
    
    print("Individual folder restore complete!")
