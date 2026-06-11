"""File registry — persists original filenames and MD5 hashes for deduplication."""
import json
import hashlib
from pathlib import Path


REGISTRY_PATH = Path(__file__).resolve().parent.parent / "faiss_index" / "file_registry.json"


class FileRegistry:
    """Registers uploaded files: maps UUID filename → original name + MD5 hash.
    Persists to faiss_index/file_registry.json so data survives server restarts.
    """

    def __init__(self):
        self._data = {}
        self._load()

    # Persistence
    def _load(self):
        """Load registry from JSON file if it exists."""
        if REGISTRY_PATH.exists():
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                self._data = json.load(f)

    def _save(self):
        """Save registry to JSON file."""
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    # MD5
    @staticmethod
    def compute_md5(file_path: str) -> str:
        """Compute MD5 hash of a file (chunked for large files)."""
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    # Dedup
    def is_duplicate(self, md5_hash: str):
        """Check if a file with this MD5 already exists.
        Returns the original filename if duplicate, None otherwise.
        """
        for uuid_name, info in self._data.items():
            if info.get("md5") == md5_hash:
                return info.get("original_name", uuid_name)
        return None

    # Register
    def register(self, uuid_name: str, original_name: str, md5_hash: str):
        """Register a newly uploaded file."""
        self._data[uuid_name] = {
            "original_name": original_name,
            "md5": md5_hash,
        }
        self._save()

    # Query
    def get_all_files(self):
        """Return list of (uuid_name, original_name) for all registered files."""
        return [(uuid, info["original_name"]) for uuid, info in self._data.items()]

    def get_original_name(self, uuid_name: str) -> str:
        """Get the original name for a UUID filename."""
        info = self._data.get(uuid_name)
        return info["original_name"] if info else uuid_name

    # Clear
    def clear(self):
        """Remove all registrations."""
        self._data = {}
        self._save()
