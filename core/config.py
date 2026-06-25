import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError
from loguru import logger
from .exceptions import ConfigError


class BrowserConfig(BaseModel):
    headless: bool = False
    wait_seconds: int = 3
    timeout: int = 120000
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    args: list = Field(default_factory=lambda: ["--no-sandbox", "--disable-gpu"])


class ScrollConfig(BaseModel):
    delay: float = 2.0
    max_attempts: int = 50


class RetryConfig(BaseModel):
    max_attempts: int = 3
    delay: float = 2.0


class IncrementalConfig(BaseModel):
    enabled: bool = True
    stop_on_existing: bool = True
    merge_data: bool = True


class BackupConfig(BaseModel):
    enabled: bool = True
    max_backups: int = 10
    directory: str = "data/backups"


class OutputDirectories(BaseModel):
    html: str = "data/html"
    images: str = "data/images"
    data: str = "data/results"
    logs: str = "logs"


class OutputConfig(BaseModel):
    directories: OutputDirectories = Field(default_factory=OutputDirectories)


class SourceConfig(BaseModel):
    name: str
    url: Optional[str] = None
    url_template: Optional[str] = None
    html_file: Optional[str] = None
    html_file_template: Optional[str] = None
    data_file: Optional[str] = None
    data_file_template: Optional[str] = None
    extractor: str
    url_pattern: Optional[str] = None
    default_params: Dict[str, Any] = Field(default_factory=dict)


class ConfigModel(BaseModel):
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    scroll: ScrollConfig = Field(default_factory=ScrollConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    incremental: IncrementalConfig = Field(default_factory=IncrementalConfig)
    backup: BackupConfig = Field(default_factory=BackupConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    sources: Dict[str, SourceConfig] = Field(default_factory=dict)


class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        self._config_path = config_path or self._find_config()
        self._config: Optional[ConfigModel] = None
        self._base_dir = Path(__file__).parent.parent.parent
        self.load_config()

    def _find_config(self) -> str:
        candidates = ["config.yaml", "config.yml", "tool_kit/config.yaml"]
        for candidate in candidates:
            path = Path(candidate)
            if path.exists():
                return str(path)
        return "config.yaml"

    def load_config(self) -> None:
        config_path = Path(self._config_path)
        if not config_path.is_absolute():
            config_path = self._base_dir / config_path

        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    raw_config = yaml.safe_load(f)
                self._config = ConfigModel(**raw_config)
                logger.info(f"配置文件加载成功: {config_path}")
            except (yaml.YAMLError, ValidationError) as e:
                logger.error(f"配置文件解析失败: {e}")
                raise ConfigError(f"配置文件解析失败: {e}")
        else:
            logger.warning(f"配置文件不存在，使用默认配置: {config_path}")
            self._config = ConfigModel()

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        for dir_path in self._config.output.directories.dict().values():
            full_path = self._base_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        if self._config is None:
            return default
        keys = key.split(".")
        value = self._config
        try:
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                elif isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        except Exception:
            return default

    def get_output_dir(self, dir_type: str) -> str:
        dir_path = getattr(self._config.output.directories, dir_type, dir_type)
        return str(self._base_dir / dir_path)

    def get_source_config(self, source_name: str) -> Optional[SourceConfig]:
        return self._config.sources.get(source_name)

    def format_source_url(self, source_name: str, **kwargs) -> str:
        source = self.get_source_config(source_name)
        if not source:
            raise ConfigError(f"源配置不存在: {source_name}")

        if source.url:
            return source.url

        if source.url_template:
            params = {**source.default_params, **kwargs}
            return source.url_template.format(**params)

        raise ConfigError(f"源 {source_name} 没有配置URL")

    def format_source_file(self, source_name: str, file_type: str, **kwargs) -> str:
        source = self.get_source_config(source_name)
        if not source:
            raise ConfigError(f"源配置不存在: {source_name}")

        if file_type == "html":
            if source.html_file:
                return source.html_file
            if source.html_file_template:
                params = {**source.default_params, **kwargs}
                return source.html_file_template.format(**params)
        elif file_type == "data":
            if source.data_file:
                return source.data_file
            if source.data_file_template:
                params = {**source.default_params, **kwargs}
                return source.data_file_template.format(**params)

        raise ConfigError(f"源 {source_name} 没有配置{file_type}文件")

    def save_config(self) -> None:
        config_path = Path(self._config_path)
        if not config_path.is_absolute():
            config_path = self._base_dir / config_path

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config.dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"配置文件已保存: {config_path}")
        except IOError as e:
            logger.error(f"保存配置文件失败: {e}")
            raise ConfigError(f"保存配置文件失败: {e}")


config_manager = ConfigManager()