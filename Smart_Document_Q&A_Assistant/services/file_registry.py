"""文件注册表 -- 保留原始文件和 MD5 哈希值，以便进行重复文件的识别"""
import json
import hashlib
from pathlib import Path


REGISTRY_PATH = Path(__file__).resolve().parent.parent / "faiss_index" / "file_registry.json"


class FileRegistry:
    """ 上传文件的注册信息：将 UUID 标识的文件名与原始名称即MD5哈希值进行关联。
    将这些信息保存到 faiss_index/file_registry.json文件中，以便在服务器重启后仍然能够保持可用
    """

    def __init__(self):
        self._data = {}
        self._load()

    # Persistence
    def _load(self):
        """如果存在 JSON 文件，则从该文件加载注册表信息 """
        if REGISTRY_PATH.exists():
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                self._data = json.load(f)

    def _save(self):
        """保存注册表 JSON 文件"""
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    # MD5
    @staticmethod
    def compute_md5(file_path: str) -> str:
        """计算文件的MD5哈希值，对大文件进行分块处理"""
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    # Dedup
    def is_duplicate(self, md5_hash: str):
        """ 如果文件的 MD5 哈希值已经存在
        如果存在重复项，则返回原始文件的文件名，否则返回 None
        """
        for uuid_name, info in self._data.items():
            if info.get("md5") == md5_hash:
                return info.get("original_name", uuid_name)
        return None

    # Register
    def register(self, uuid_name: str, original_name: str, md5_hash: str):
        """注册新上传的文件 """
        self._data[uuid_name] = {
            "original_name": original_name,
            "md5": md5_hash,
        }
        self._save()

    # Query
    def get_all_files(self):
        """ 返回所有已注册文件的 uuid名和原始文件的名称列表 """
        return [(uuid, info["original_name"]) for uuid, info in self._data.items()]

    def get_original_name(self, uuid_name: str) -> str:
        """获取UUID文件名的原始文件"""
        info = self._data.get(uuid_name)
        return info["original_name"] if info else uuid_name

    # Clear
    def remove(self, uuid_name):
        self._data.pop(uuid_name, None)
        self._save()

    def clear(self):
        """取消所有注册"""
        self._data = {}
        self._save()
