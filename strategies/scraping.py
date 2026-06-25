import asyncio
import time
import os
from abc import ABC, abstractmethod
from typing import Optional, Set
from playwright.sync_api import sync_playwright, Page, Browser
from playwright.async_api import async_playwright
from loguru import logger
from core.config import config_manager
from core.exceptions import ScraperError


class ScrapingStrategy(ABC):
    def __init__(self, url: str, output_filename: str, **kwargs):
        self.url = url
        self.output_filename = output_filename
        self.html_dir = config_manager.get_output_dir("html")
        self.save_path = os.path.join(self.html_dir, output_filename)
        self.existing_urls: Set[str] = kwargs.get("existing_urls", set())
        self.incremental_mode = kwargs.get("incremental_mode", False)
        self._config = config_manager.get("browser")

    @abstractmethod
    def scrape(self) -> str:
        pass

    def _save_html(self, html_content: str) -> None:
        os.makedirs(self.html_dir, exist_ok=True)
        with open(self.save_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"HTML已保存: {self.save_path}")


class SyncScrapingStrategy(ScrapingStrategy):
    def scrape(self) -> str:
        logger.info(f"开始抓取页面: {self.url}")
        with sync_playwright() as p:
            browser, page = self._setup_browser(p)
            try:
                html_content = self._process_page(page)
                self._save_html(html_content)
                return html_content
            finally:
                browser.close()

    def _setup_browser(self, playwright) -> tuple[Browser, Page]:
        browser_args = list(self._config.args) if self._config.args else []
        if not self._config.headless:
            browser_args.append("--start-maximized")

        browser = playwright.chromium.launch(
            headless=self._config.headless,
            args=browser_args
        )

        context = browser.new_context(
            user_agent=self._config.user_agent,
            no_viewport=True
        )

        page = context.new_page()
        return browser, page

    def _process_page(self, page: Page) -> str:
        page.goto(self.url, timeout=self._config.timeout)
        page.wait_for_load_state("networkidle")
        time.sleep(self._config.wait_seconds)
        self._scroll_to_bottom(page)
        return page.content()

    def _scroll_to_bottom(self, page: Page) -> None:
        last_height = page.evaluate("document.body.scrollHeight")
        attempts = 0
        scroll_delay = config_manager.get("scroll.delay", 2.0)
        stop_on_existing = config_manager.get("incremental.stop_on_existing", True)

        while True:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(scroll_delay)
            new_height = page.evaluate("document.body.scrollHeight")

            if self.incremental_mode and self.existing_urls:
                if self._check_existing_urls(page) and stop_on_existing:
                    logger.info("检测到已存在数据，停止滚动")
                    break

            if new_height == last_height:
                attempts += 1
                if attempts >= 3:
                    logger.info("页面高度不再变化，停止滚动")
                    break
            else:
                attempts = 0

            last_height = new_height

    def _check_existing_urls(self, page: Page) -> bool:
        try:
            url_pattern = config_manager.get("sources.user_posts.url_pattern", "/article/")
            current_urls = page.evaluate(f"""
                Array.from(document.querySelectorAll('a[href*="{url_pattern}"]'))
                    .map(el => el.href)
            """)
            for url in current_urls:
                if url in self.existing_urls:
                    logger.info(f"检测到已存在URL: {url}")
                    return True
            return False
        except Exception as e:
            logger.warning(f"URL检测失败: {e}")
            return False


class AsyncScrapingStrategy(ScrapingStrategy):
    async def scrape(self) -> str:
        logger.info(f"异步开始抓取页面: {self.url}")
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=self._config.headless,
            args=self._config.args
        )
        page = await browser.new_page(user_agent=self._config.user_agent)

        try:
            await page.goto(self.url, timeout=self._config.timeout)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(self._config.wait_seconds)
            await self._async_scroll_to_bottom(page)
            html_content = await page.content()
            self._save_html(html_content)
            return html_content
        finally:
            await browser.close()
            await playwright.stop()

    async def _async_scroll_to_bottom(self, page) -> None:
        last_height = await page.evaluate("document.body.scrollHeight")
        attempts = 0
        scroll_delay = config_manager.get("scroll.delay", 2.0)

        while True:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(scroll_delay)
            new_height = await page.evaluate("document.body.scrollHeight")

            if new_height == last_height:
                attempts += 1
                if attempts >= 3:
                    break
            else:
                attempts = 0

            last_height = new_height


class NewsScrapingStrategy(SyncScrapingStrategy):
    def __init__(self, url: str, output_filename: str, **kwargs):
        super().__init__(url, output_filename, **kwargs)
        self.url_selector_template = "a[href*='/main/news/detail/']"

    def _process_page(self, page: Page) -> str:
        page.goto(self.url, timeout=self._config.timeout)
        page.wait_for_load_state("networkidle")
        time.sleep(self._config.wait_seconds)
        self._scroll_to_bottom(page)
        self._click_load_more(page)
        return page.content()

    def _click_load_more(self, page) -> bool:
        try:
            load_more_selector = "li.news__more, li.recommend__more"
            click_count = 0
            consecutive_failures = 0
            stop_on_existing = config_manager.get("incremental.stop_on_existing", True)

            while consecutive_failures < 3:
                if self.incremental_mode and self.existing_urls:
                    if self._check_existing_urls(page) and stop_on_existing:
                        logger.info("检测到已存在数据，停止点击加载更多")
                        break

                try:
                    locator = page.locator(load_more_selector)
                    if locator.count() > 0 and locator.is_visible():
                        click_count += 1
                        logger.info(f"点击加载更多按钮 (第{click_count}次)")
                        page.click(load_more_selector)
                        page.wait_for_timeout(3000)
                        page.wait_for_load_state("networkidle")
                        page.wait_for_timeout(1000)
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        page.wait_for_timeout(1000)
                except Exception as e:
                    consecutive_failures += 1
                    page.wait_for_timeout(1000)

            return click_count > 0
        except Exception as e:
            logger.warning(f"点击加载更多失败: {e}")
            return False

    def _check_existing_urls(self, page: Page) -> bool:
        try:
            current_urls = page.evaluate(f"""
                Array.from(document.querySelectorAll('{self.url_selector_template}'))
                    .map(el => el.href)
            """)
            for url in current_urls:
                if url in self.existing_urls:
                    return True
            return False
        except Exception:
            return False


class Scraper:
    def __init__(self, strategy: ScrapingStrategy):
        self.strategy = strategy

    def scrape(self) -> str:
        if hasattr(self.strategy, 'scrape') and callable(self.strategy.scrape):
            if asyncio.iscoroutinefunction(self.strategy.scrape):
                return asyncio.run(self.strategy.scrape())
            return self.strategy.scrape()
        raise ScraperError("策略对象没有有效的scrape方法")


def create_scraper(url: str, output_filename: str, strategy_type: str = "sync", **kwargs) -> Scraper:
    strategy_classes = {
        "sync": SyncScrapingStrategy,
        "async": AsyncScrapingStrategy,
        "news": NewsScrapingStrategy,
    }

    strategy_class = strategy_classes.get(strategy_type, SyncScrapingStrategy)
    strategy = strategy_class(url, output_filename, **kwargs)
    return Scraper(strategy)