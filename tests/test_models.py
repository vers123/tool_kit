import unittest
from models import ImageData, NewsData, PostData, CharacterData


class TestImageData(unittest.TestCase):
    def test_to_line(self):
        data = ImageData(name="角色1", url="https://example.com/image1.jpg", index=1)
        line = data.to_line()
        self.assertEqual(line, "0001-角色1-[https://example.com/image1.jpg]")

    def test_unique_key(self):
        data = ImageData(name="角色1", url="https://example.com/image1.jpg")
        self.assertEqual(data.get_unique_key(), "https://example.com/image1.jpg")


class TestNewsData(unittest.TestCase):
    def test_to_line(self):
        data = NewsData(title="测试新闻", url="https://example.com/news/1", date="2024-01-01", index=1)
        line = data.to_line()
        self.assertEqual(line, "0001-测试新闻-[2024-01-01]-(https://example.com/news/1)")

    def test_unique_key(self):
        data = NewsData(title="测试新闻", url="https://example.com/news/1", date="2024-01-01")
        self.assertEqual(data.get_unique_key(), "https://example.com/news/1")


class TestPostData(unittest.TestCase):
    def test_to_line(self):
        data = PostData(title="测试帖子", url="https://example.com/post/1", date="2024-01-01", index=1)
        line = data.to_line()
        self.assertEqual(line, "0001-测试帖子-[2024-01-01](https://example.com/post/1)")

    def test_unique_key(self):
        data = PostData(title="测试帖子", url="https://example.com/post/1", date="2024-01-01")
        self.assertEqual(data.get_unique_key(), "https://example.com/post/1")


class TestCharacterData(unittest.TestCase):
    def test_to_line(self):
        data = CharacterData(id="10000001", name="角色1", index=1)
        line = data.to_line()
        self.assertEqual(line, "0001-10000001-角色1")

    def test_unique_key(self):
        data = CharacterData(id="10000001", name="角色1")
        self.assertEqual(data.get_unique_key(), "10000001")


if __name__ == '__main__':
    unittest.main()