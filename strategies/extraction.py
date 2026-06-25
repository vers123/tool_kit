import re
import os
from abc import ABC, abstractmethod
from typing import List, Set, Optional
from datetime import datetime, timedelta
from loguru import logger
from core.config import config_manager
from models import ScrapedData, ImageData, NewsData, PostData, CharacterData
from core.exceptions import ExtractorError


class ExtractionStrategy(ABC):
    def __init__(self, html_path: str, data_path: str):
        self.html_path = html_path
        self.data_path = data_path
        self._output_dir = os.path.dirname(data_path)
        os.makedirs(self._output_dir, exist_ok=True)

    @abstractmethod
    def extract(self, html_content: Optional[str] = None) -> List[ScrapedData]:
        pass

    def load_html(self) -> str:
        if not os.path.exists(self.html_path):
            raise ExtractorError(f"HTML文件不存在: {self.html_path}")
        with open(self.html_path, "r", encoding="utf-8") as f:
            return f.read()

    def save_data(self, data: List[ScrapedData]) -> bool:
        try:
            content = "\n".join(item.to_line() for item in data)
            with open(self.data_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"数据已保存: {self.data_path}")
            return True
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            return False

    def get_existing_urls(self) -> Set[str]:
        if not os.path.exists(self.data_path):
            return set()
        try:
            data = self.load_existing_data()
            return {item.get_unique_key() for item in data if isinstance(item, ScrapedData)}
        except Exception:
            return set()

    def load_existing_data(self) -> List[ScrapedData]:
        return []

    def merge_data(self, old_data: List[ScrapedData], new_data: List[ScrapedData]) -> List[ScrapedData]:
        merged = {item.get_unique_key(): item for item in old_data}
        for item in new_data:
            merged[item.get_unique_key()] = item
        return sorted(merged.values(), key=lambda x: x.index)


class ImageExtractionStrategy(ExtractionStrategy):
    def extract(self, html_content: Optional[str] = None) -> List[ImageData]:
        if html_content is None:
            html_content = self.load_html()

        pattern = re.compile(
            r'class="collection-avatar__item".*?'
            r'data-src="(https://.*?mihoyo\.com/.*?\.\w+)\?.*?"'
            r'.*?'
            r'class="collection-avatar__title">(.*?)</div>',
            re.DOTALL
        )

        items = []
        for match in pattern.findall(html_content):
            img_url = match[0]
            name = match[1].strip()
            items.append(ImageData(name=name, url=img_url))

        items = list(reversed(items))
        for idx, item in enumerate(items, 1):
            item.index = idx

        logger.info(f"提取到 {len(items)} 个图片")
        return items


class NewsExtractionStrategy(ExtractionStrategy):
    def extract(self, html_content: Optional[str] = None, incremental: bool = False) -> List[NewsData]:
        if html_content is None:
            html_content = self.load_html()

        pattern = re.compile(
            r'<li class="news__item[^"]*">\s*<a href="(/main/news/detail/\d+)"[^>]*class="news__title[^"]*"[^>]*>'
            r'.*?<h3[^>]*title="([^"]*)"[^>]*>([^<]+)</h3>.*?'
            r'<div class="news__date">([^<]+)</div>',
            re.DOTALL
        )

        items = []
        for match in pattern.findall(html_content):
            url_path = match[0]
            title_attr = match[1]
            title_text = match[2].strip()
            date = match[3].strip()

            url = f"https://ys.mihoyo.com{url_path}"
            title = title_attr if title_attr else title_text
            title = re.sub(r'\s+', ' ', title)

            items.append(NewsData(title=title, url=url, date=date))

        if not items:
            logger.warning("使用宽松模式重新匹配")
            pattern_loose = re.compile(
                r'<li class="news__item[^"]*">.*?'
                r'<a href="(/main/news/detail/\d+)"[^>]*class="news__title[^"]*"[^>]*>'
                r'.*?<h3[^>]*>([^<]+)</h3>.*?'
                r'<div class="news__date">([^<]+)</div>',
                re.DOTALL
            )

            for match in pattern_loose.findall(html_content):
                url_path = match[0]
                title_text = match[1].strip()
                date = match[2].strip()

                url = f"https://ys.mihoyo.com{url_path}"
                title = re.sub(r'\s+', ' ', title_text)
                items.append(NewsData(title=title, url=url, date=date))

        if incremental and config_manager.get("incremental.merge_data", True):
            existing_data = self.load_existing_data()
            items = self.merge_data(existing_data, items)
            logger.info(f"增量合并完成，共 {len(items)} 条数据")

        items = sorted(set(items), key=lambda x: x.date, reverse=True)
        for idx, item in enumerate(items, 1):
            item.index = idx

        logger.info(f"提取到 {len(items)} 条新闻")
        return items

    def load_existing_data(self) -> List[NewsData]:
        if not os.path.exists(self.data_path):
            return []

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                content = f.read()

            items = []
            pattern = re.compile(r'\d{4}-(.+?)-\[(.+?)\]-\((https://.+?)\)')

            for match in pattern.findall(content):
                title = match[0].strip()
                date = match[1]
                url = match[2]
                items.append(NewsData(title=title, url=url, date=date))

            return items
        except Exception as e:
            logger.warning(f"加载旧数据失败: {e}")
            return []


class PostExtractionStrategy(ExtractionStrategy):
    def extract(self, html_content: Optional[str] = None, incremental: bool = False) -> List[PostData]:
        if html_content is None:
            html_content = self.load_html()

        # 使用位置标记法正确匹配嵌套的div
        post_pattern = re.compile(r'<div class="mhy-account-center-post-card">', re.DOTALL)

        now = datetime.now()
        items = []
        for match in post_pattern.finditer(html_content):
            start = match.start()
            depth = 1
            pos = start + len(match.group())
            post_block = match.group()

            while depth > 0 and pos < len(html_content):
                if html_content[pos:pos+5] == '<div ':
                    depth += 1
                    pos += 4
                elif html_content[pos:pos+6] == '</div>':
                    depth -= 1
                    if depth == 0:
                        post_block = html_content[start:pos+6]
                        break
                    pos += 6
                else:
                    pos += 1

            time_match = re.search(r'class="mhy-account-center-time__small">([^<]+)<', post_block)
            url_match = re.search(r'href="(/ys/article/\d+)"', post_block)
            title_match = re.search(r'class="mhy-article-card__h3"[^>]*>([\s\S]*?)</div>', post_block)

            if not time_match or not url_match or not title_match:
                continue

            time_str = time_match.group(1).strip()
            if ' · ' in time_str:
                time_str = time_str.split(' · ')[0]

            url = f"https://www.miyoushe.com{url_match.group(1)}"
            title = title_match.group(1).strip()
            title = re.sub(r'\s+', ' ', title)
            final_date = self._parse_date(time_str, now)

            items.append(PostData(title=title, url=url, date=final_date))

        if incremental and config_manager.get("incremental.merge_data", True):
            existing_data = self.load_existing_data()
            items = self.merge_data(existing_data, items)

        items = sorted(set(items), key=lambda x: x.date, reverse=True)
        for idx, item in enumerate(items, 1):
            item.index = idx

        logger.info(f"提取到 {len(items)} 条帖子")
        return items

    def _parse_date(self, time_str: str, now: datetime) -> str:
        if "小时前" in time_str:
            h = int(re.findall(r'(\d+)小时前', time_str)[0])
            return (now - timedelta(hours=h)).strftime("%Y-%m-%d")
        elif re.match(r'\d{2}-\d{2}', time_str):
            return f"{now.year}-{time_str}"
        else:
            return time_str

    def load_existing_data(self) -> List[PostData]:
        if not os.path.exists(self.data_path):
            return []

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                content = f.read()

            items = []
            pattern = re.compile(r'\d{4}-(.+?)-\[(\d{4}-\d{2}-\d{2})\]\((https://.+?)\)')

            for match in pattern.findall(content):
                title = match[0].strip()
                date = match[1]
                url = match[2]
                items.append(PostData(title=title, url=url, date=date))

            return items
        except Exception as e:
            logger.warning(f"加载旧数据失败: {e}")
            return []


class TutorialExtractionStrategy(ExtractionStrategy):
    def extract(self, html_content: Optional[str] = None) -> List[CharacterData]:
        if html_content is None:
            html_content = self.load_html()

        characters = []
        table_pattern = re.compile(
            r'<tr class="table-row">.*?'
            r'<td[^>]*>.*?<p[^>]*>(\d+)</p>.*?'
            r'<td[^>]*>.*?<p[^>]*>([^<]+)</p>.*?'
            r'</tr>',
            re.DOTALL
        )

        for match in table_pattern.findall(html_content):
            char_id = match[0].strip()
            char_name = match[1].strip()
            if char_id != "对应编号" and char_name != "角色名":
                characters.append(CharacterData(id=char_id, name=char_name))

        if not characters:
            logger.warning("使用宽松模式重新匹配")
            loose_pattern = re.compile(
                r'<td[^>]*>.*?<p[^>]*>(\d{7,})</p>.*?'
                r'<td[^>]*>.*?<p[^>]*>([^<]+)</p>',
                re.DOTALL
            )

            for match in loose_pattern.findall(html_content):
                char_id = match[0].strip()
                char_name = match[1].strip()
                if len(char_id) >= 7:
                    characters.append(CharacterData(id=char_id, name=char_name))

        characters = sorted(set(characters), key=lambda x: int(x.id))
        for idx, char in enumerate(characters, 1):
            char.index = idx

        logger.info(f"提取到 {len(characters)} 个角色")
        return characters


class Extractor:
    def __init__(self, strategy: ExtractionStrategy):
        self.strategy = strategy

    def extract(self, **kwargs) -> List[ScrapedData]:
        return self.strategy.extract(**kwargs)

    def save_data(self, data: List[ScrapedData]) -> bool:
        return self.strategy.save_data(data)

    def get_existing_urls(self) -> Set[str]:
        return self.strategy.get_existing_urls()


def create_extractor(extractor_type: str, html_path: str, data_path: str) -> Extractor:
    extractor_classes = {
        "image": ImageExtractionStrategy,
        "news": NewsExtractionStrategy,
        "post": PostExtractionStrategy,
        "tutorial": TutorialExtractionStrategy,
    }

    strategy_class = extractor_classes.get(extractor_type)
    if not strategy_class:
        raise ExtractorError(f"未知的提取器类型: {extractor_type}")

    strategy = strategy_class(html_path, data_path)
    return Extractor(strategy)