import unittest
import tempfile
import os
import yaml
from core.config import ConfigManager


class TestConfigManager(unittest.TestCase):
    def test_default_config(self):
        config_manager = ConfigManager()
        self.assertFalse(config_manager.get("browser.headless"))
        self.assertEqual(config_manager.get("browser.wait_seconds"), 3)
        self.assertEqual(config_manager.get("retry.max_attempts"), 3)

    def test_custom_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "test_config.yaml")

            test_config = {
                "browser": {
                    "headless": True,
                    "wait_seconds": 5
                }
            }

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(test_config, f)

            config_manager = ConfigManager(config_path)
            self.assertTrue(config_manager.get("browser.headless"))
            self.assertEqual(config_manager.get("browser.wait_seconds"), 5)

    def test_format_source_url(self):
        # 使用项目根目录的config.yaml
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, "config.yaml")
        if os.path.exists(config_path):
            config_manager = ConfigManager(config_path)
        else:
            config_manager = ConfigManager()

        # 如果有user_posts源则测试，否则跳过
        if "user_posts" in config_manager._config.sources:
            url = config_manager.format_source_url("user_posts")
            self.assertIn("miyoushe.com", url)
        else:
            self.skipTest("user_posts源配置不存在")

    def test_output_dir_creation(self):
        config_manager = ConfigManager()
        html_dir = config_manager.get_output_dir("html")
        self.assertTrue(os.path.isdir(html_dir))


if __name__ == '__main__':
    unittest.main()