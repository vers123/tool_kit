import os
from typing import Optional, Dict, Any
from loguru import logger
from core.config import config_manager
from strategies import create_scraper, create_extractor
from pipelines.base import create_default_pipeline
from core.exceptions import ConfigError, ScraperError, ExtractorError


class Workflow:
    def __init__(self, source_name: str, **kwargs):
        self.source_name = source_name
        self.source_config = config_manager.get_source_config(source_name)
        if not self.source_config:
            raise ConfigError(f"源配置不存在: {source_name}")

        self.kwargs = kwargs
        self.url = config_manager.format_source_url(source_name, **kwargs)
        self.html_file = config_manager.format_source_file(source_name, "html", **kwargs)
        self.data_file = config_manager.format_source_file(source_name, "data", **kwargs)

        self.html_path = os.path.join(config_manager.get_output_dir("html"), self.html_file)
        self.data_path = os.path.join(config_manager.get_output_dir("data"), self.data_file)

        self.incremental = kwargs.get("incremental", False)

    def scrape(self) -> str:
        existing_urls = set()
        if self.incremental and config_manager.get("incremental.enabled", True):
            extractor = self._create_extractor()
            existing_urls = extractor.get_existing_urls()
            logger.info(f"增量模式: 已存在 {len(existing_urls)} 条数据")

        strategy_type = "news" if self.source_name == "genshin_news" else "sync"
        scraper = create_scraper(
            self.url,
            self.html_file,
            strategy_type=strategy_type,
            incremental_mode=self.incremental,
            existing_urls=existing_urls
        )

        return scraper.scrape()

    def extract(self, html_content: Optional[str] = None) -> list:
        extractor = self._create_extractor()
        return extractor.extract(html_content=html_content, incremental=self.incremental)

    def save(self, data: list) -> bool:
        pipeline = create_default_pipeline(self.data_path)
        processed_data = pipeline.execute(data)

        extractor = self._create_extractor()
        return extractor.save_data(processed_data)

    def run(self) -> bool:
        logger.info(f"开始工作流: {self.source_config.name}")

        try:
            self.scrape()
            data = self.extract()

            if not data:
                logger.warning("未提取到数据")
                return False

            if self.save(data):
                logger.info(f"工作流完成: {self.source_config.name}，共 {len(data)} 条数据")
                return True
            else:
                logger.error("保存数据失败")
                return False

        except (ScraperError, ExtractorError) as e:
            logger.error(f"工作流执行失败: {e}")
            return False

    def _create_extractor(self):
        extractor_type = self.source_config.extractor
        return create_extractor(extractor_type, self.html_path, self.data_path)


class CustomWorkflow(Workflow):
    def __init__(self, url: str, output_filename: str, extractor_type: str = None):
        self.source_name = "custom"
        self.url = url
        self.html_file = output_filename
        self.data_file = os.path.splitext(output_filename)[0] + ".txt"
        self.extractor_type = extractor_type

        self.html_path = os.path.join(config_manager.get_output_dir("html"), self.html_file)
        self.data_path = os.path.join(config_manager.get_output_dir("data"), self.data_file)

        self.incremental = False
        self.source_config = None

    def scrape(self) -> str:
        scraper = create_scraper(self.url, self.html_file)
        return scraper.scrape()

    def extract(self, html_content: Optional[str] = None) -> list:
        if not self.extractor_type:
            logger.warning("未指定提取器类型，跳过提取")
            return []

        extractor = create_extractor(self.extractor_type, self.html_path, self.data_path)
        return extractor.extract(html_content=html_content)

    def _create_extractor(self):
        if not self.extractor_type:
            raise ExtractorError("未指定提取器类型")
        return create_extractor(self.extractor_type, self.html_path, self.data_path)