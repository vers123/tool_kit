import os
from abc import ABC, abstractmethod
from typing import List, Callable, Any
from loguru import logger
from models import ScrapedData


class PipelineStep(ABC):
    @abstractmethod
    def execute(self, data: List[ScrapedData]) -> List[ScrapedData]:
        pass


class Pipeline:
    def __init__(self):
        self.steps: List[PipelineStep] = []

    def add_step(self, step: PipelineStep) -> "Pipeline":
        self.steps.append(step)
        return self

    def execute(self, data: List[ScrapedData]) -> List[ScrapedData]:
        result = data
        for step in self.steps:
            result = step.execute(result)
        return result


class DeduplicationStep(PipelineStep):
    def execute(self, data: List[ScrapedData]) -> List[ScrapedData]:
        if not data:
            return data

        seen = set()
        deduplicated = []
        for item in data:
            key = item.get_unique_key()
            if key not in seen:
                seen.add(key)
                deduplicated.append(item)

        removed_count = len(data) - len(deduplicated)
        if removed_count > 0:
            logger.info(f"去重完成，移除 {removed_count} 条重复数据")

        return deduplicated


class SortingStep(PipelineStep):
    def __init__(self, key: Callable[[ScrapedData], Any] = None, reverse: bool = False):
        self.key = key or (lambda x: x.index)
        self.reverse = reverse

    def execute(self, data: List[ScrapedData]) -> List[ScrapedData]:
        return sorted(data, key=self.key, reverse=self.reverse)


class IndexingStep(PipelineStep):
    def execute(self, data: List[ScrapedData]) -> List[ScrapedData]:
        for idx, item in enumerate(data, 1):
            item.index = idx
        return data


class BackupStep(PipelineStep):
    def __init__(self, file_path: str, backup_dir: str = "data/backups", max_backups: int = 10):
        self.file_path = file_path
        self.backup_dir = backup_dir
        self.max_backups = max_backups

    def execute(self, data: List[ScrapedData]) -> List[ScrapedData]:
        from tool_kit.utils.backup import BackupManager
        backup_manager = BackupManager(self.backup_dir, self.max_backups)
        backup_manager.create_backup(self.file_path)
        return data


class IncrementalMergeStep(PipelineStep):
    def __init__(self, existing_data: List[ScrapedData]):
        self.existing_data = existing_data

    def execute(self, data: List[ScrapedData]) -> List[ScrapedData]:
        merged = {item.get_unique_key(): item for item in self.existing_data}
        for item in data:
            merged[item.get_unique_key()] = item
        return list(merged.values())


class DataValidationStep(PipelineStep):
    def __init__(self, validators: List[Callable[[ScrapedData], bool]] = None):
        self.validators = validators or []

    def execute(self, data: List[ScrapedData]) -> List[ScrapedData]:
        if not self.validators:
            return data

        valid = []
        for item in data:
            if all(validator(item) for validator in self.validators):
                valid.append(item)
            else:
                logger.warning(f"数据验证失败: {item.to_line()}")

        removed_count = len(data) - len(valid)
        if removed_count > 0:
            logger.info(f"验证完成，移除 {removed_count} 条无效数据")

        return valid


def create_default_pipeline(output_file: str) -> Pipeline:
    from tool_kit.core.config import config_manager

    pipeline = Pipeline()
    pipeline.add_step(DeduplicationStep())
    pipeline.add_step(SortingStep(reverse=True))
    pipeline.add_step(IndexingStep())

    if config_manager.get("backup.enabled", True):
        backup_dir = config_manager.get("backup.directory", "data/backups")
        max_backups = config_manager.get("backup.max_backups", 10)
        pipeline.add_step(BackupStep(output_file, backup_dir, max_backups))

    return pipeline