import shutil
import os

DB_PATH = "../data/chroma_db"

if os.path.exists(DB_PATH):
    try:
        shutil.rmtree(DB_PATH)
        print(f"✅ Successfully deleted old database at: {DB_PATH}")
        print("   You can now run 'python build_db.py' to rebuild it.")
    except Exception as e:
        print(f"❌ Error deleting database: {e}")
else:
    print(f"ℹ️  No database found at {DB_PATH}. Ready to build.")