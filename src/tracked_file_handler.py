import os
import hashlib
from typing import List


class TrackedFileHandler:
    def __init__(self, tracked_file_path: str):
        self.tracked_file_path = tracked_file_path
        if not os.path.exists(self.tracked_file_path):
            open(self.tracked_file_path, "w").close()

        self.tracked_files = self._load_tracked_files()

    def _load_tracked_files(self) -> List[str]:
        with open(self.tracked_file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f]

    def _save_tracked_files(self) -> None:
        with open(self.tracked_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(self.tracked_files)))

    def get_dangling_files(self) -> List[str]:
        """Cleanup tracked files that do not exist anymore"""
        tracked_files = self._load_tracked_files()
        files = [f.split("@")[0] for f in tracked_files]

        return [f for f in files if not os.path.exists(f)]

    def should_skip(self, file: str) -> bool:
        # check if file exists (in case its not yet committed etc.)
        if not os.path.exists(file):
            return True

        hash = self.get_file_hash(file)
        return f"{file}@{hash}" in self.tracked_files

    def upsert_tracked_file(self, file: str) -> str | None:
        if self.should_skip(file):
            return

        # tracked file needs to update -> delete old tracked file
        old_tracked_file = self.delete_tracked_file(file)

        # update internal list and sync to files
        self.tracked_files.append(f"{file}@{self.get_file_hash(file)}")
        self._save_tracked_files()

        return old_tracked_file

    def delete_tracked_file(self, file: str) -> str | None:
        for file_with_track in self.tracked_files:
            if file_with_track.startswith(f"{file}@"):
                # updated internal list and sync to files
                self.tracked_files.remove(file_with_track)
                self._save_tracked_files()

                # return old tracked file for others to use
                return file_with_track.split("@")[1]

    @staticmethod
    def get_file_hash(file_path: str) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)

        return hasher.hexdigest()
