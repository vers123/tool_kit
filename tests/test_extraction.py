import unittest
import tempfile
import os
from strategies import create_extractor


class TestImageExtraction(unittest.TestCase):
    def setUp(self):
        self.test_html = '''
        <div class="collection-avatar__item">
            <img data-src="https://upload-bbs.mihoyo.com/image1.jpg?param=value">
            <div class="collection-avatar__title">角色1</div>
        </div>
        <div class="collection-avatar__item">
            <img data-src="https://upload-bbs.mihoyo.com/image2.png?param=value">
            <div class="collection-avatar__title">角色2</div>
        </div>
        '''

    def test_extract_image_urls(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            html_path = os.path.join(temp_dir, "test.html")
            data_path = os.path.join(temp_dir, "test.txt")

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self.test_html)

            extractor = create_extractor("image", html_path, data_path)
            image_data = extractor.extract()

            self.assertEqual(len(image_data), 2)
            self.assertEqual(image_data[0].name, "角色2")
            self.assertEqual(image_data[0].url, "https://upload-bbs.mihoyo.com/image2.png")


class TestPostExtraction(unittest.TestCase):
    def setUp(self):
        self.test_html = '''
        <div class="mhy-account-center-post-list">
            <div class="mhy-account-center-post-card">
                <div class="mhy-account-center-time__small">2024-01-15 · 其他信息</div>
                <a href="/ys/article/123"></a>
                <div class="mhy-article-card__h3">测试帖子标题</div>
            </div>
        </div>
        '''

    def test_extract_posts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            html_path = os.path.join(temp_dir, "test.html")
            data_path = os.path.join(temp_dir, "test.txt")

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self.test_html)

            extractor = create_extractor("post", html_path, data_path)
            post_data = extractor.extract()

            self.assertEqual(len(post_data), 1)
            self.assertEqual(post_data[0].title, "测试帖子标题")
            self.assertEqual(post_data[0].date, "2024-01-15")
            self.assertEqual(post_data[0].url, "https://www.miyoushe.com/ys/article/123")


if __name__ == '__main__':
    unittest.main()