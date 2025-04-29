import json
import os

class FileView:
    @staticmethod
    def write_json(path: str, data):
        dirpath = os.path.dirname(path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def write_text(path: str, content: str):
        dirpath = os.path.dirname(path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
            
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)