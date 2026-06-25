import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from loguru import logger


@dataclass
class BackupInfo:
    filename: str
    filepath: str
    created_at: datetime
    size: int


class BackupManager:
    def __init__(self, backup_dir: str = "data/backups", max_backups: int = 10):
        self.backup_dir = backup_dir
        self.max_backups = max_backups
        self._ensure_backup_dir()

    def _ensure_backup_dir(self) -> None:
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)

    def _get_backup_subdir(self, filename: str) -> str:
        base_name = Path(filename).stem
        subdir = os.path.join(self.backup_dir, base_name)
        Path(subdir).mkdir(parents=True, exist_ok=True)
        return subdir

    def create_backup(self, source_file: str, backup_name: Optional[str] = None) -> Optional[str]:
        if not os.path.exists(source_file):
            logger.info(f"源文件不存在，无需备份: {source_file}")
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            source_filename = os.path.basename(source_file)
            base_name = Path(source_filename).stem
            ext = Path(source_filename).suffix

            if backup_name:
                backup_filename = f"{base_name}_{backup_name}{ext}"
            else:
                backup_filename = f"{base_name}_{timestamp}{ext}"

            backup_subdir = self._get_backup_subdir(source_filename)
            backup_path = os.path.join(backup_subdir, backup_filename)

            shutil.copy2(source_file, backup_path)
            logger.info(f"已创建备份: {backup_path}")

            self._cleanup_old_backups(backup_subdir, base_name)
            return backup_path

        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return None

    def _cleanup_old_backups(self, backup_subdir: str, base_name: str) -> None:
        try:
            backups = []
            for file in os.listdir(backup_subdir):
                if file.startswith(base_name):
                    filepath = os.path.join(backup_subdir, file)
                    stat = os.stat(filepath)
                    backups.append((filepath, stat.st_mtime))

            backups.sort(key=lambda x: x[1], reverse=True)

            if len(backups) > self.max_backups:
                for filepath, _ in backups[self.max_backups:]:
                    os.remove(filepath)
                    logger.info(f"已清理旧备份: {filepath}")

        except Exception as e:
            logger.warning(f"清理旧备份失败: {e}")

    def list_backups(self, filename: str) -> List[BackupInfo]:
        backup_subdir = self._get_backup_subdir(filename)
        backups = []

        try:
            base_name = Path(filename).stem
            for file in os.listdir(backup_subdir):
                if file.startswith(base_name):
                    filepath = os.path.join(backup_subdir, file)
                    stat = os.stat(filepath)
                    created_at = datetime.fromtimestamp(stat.st_mtime)
                    backups.append(BackupInfo(
                        filename=file,
                        filepath=filepath,
                        created_at=created_at,
                        size=stat.st_size
                    ))

            backups.sort(key=lambda x: x.created_at, reverse=True)

        except Exception as e:
            logger.error(f"列出备份失败: {e}")

        return backups

    def restore_backup(self, backup_path: str, target_path: str) -> bool:
        if not os.path.exists(backup_path):
            logger.error(f"备份文件不存在: {backup_path}")
            return False

        try:
            if os.path.exists(target_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_backup = f"{target_path}.before_restore_{timestamp}"
                shutil.copy2(target_path, temp_backup)
                logger.info(f"当前文件已临时备份到: {temp_backup}")

            shutil.copy2(backup_path, target_path)
            logger.info(f"已从备份恢复: {backup_path} -> {target_path}")
            return True

        except Exception as e:
            logger.error(f"恢复备份失败: {e}")
            return False

    def get_latest_backup(self, filename: str) -> Optional[str]:
        backups = self.list_backups(filename)
        if backups:
            return backups[0].filepath
        return None

    def get_backup_size_mb(self, filename: str) -> float:
        backups = self.list_backups(filename)
        total_size = sum(b.size for b in backups)
        return total_size / (1024 * 1024)