#!/usr/bin/env python3

import sys
import os
import platform
from typing import Dict
from loguru import logger
from core.config import config_manager
from pipelines import Workflow, CustomWorkflow
from utils.backup import BackupManager


class ToolKitCLI:
    def __init__(self):
        self.version = "1.0.0"
        self.title = f"米游社工具箱 v{self.version}"
        self.options = self._setup_options()
        self.backup_manager = BackupManager(
            config_manager.get("backup.directory", "data/backups"),
            config_manager.get("backup.max_backups", 10)
        )

    def _setup_options(self) -> Dict:
        return {
            "1": {
                "label": "抓取用户发帖主页",
                "description": "从米游社抓取指定用户的发帖记录",
                "handler": self._run_workflow,
                "workflow": "user_posts",
                "incremental": False
            },
            "2": {
                "label": "增量抓取用户发帖",
                "description": "增量更新用户发帖，自动备份旧数据",
                "handler": self._run_workflow,
                "workflow": "user_posts",
                "incremental": True
            },
            "3": {
                "label": "抓取角色图鉴页面",
                "description": "从米游社百科抓取角色图鉴信息",
                "handler": self._run_workflow,
                "workflow": "character_baike",
                "incremental": False
            },
            "4": {
                "label": "抓取原神新闻页面",
                "description": "从原神官网抓取新闻页面",
                "handler": self._run_workflow,
                "workflow": "genshin_news",
                "incremental": False
            },
            "5": {
                "label": "增量抓取原神新闻",
                "description": "增量更新原神新闻，自动备份旧数据",
                "handler": self._run_workflow,
                "workflow": "genshin_news",
                "incremental": True
            },
            "6": {
                "label": "抓取米游社教程页面",
                "description": "从米游社抓取教程页面",
                "handler": self._fetch_tutorial_page
            },
            "7": {
                "label": "提取教程角色数据",
                "description": "从教程页面提取角色编号和名称",
                "handler": self._extract_tutorial_data
            },
            "8": {
                "label": "抓取自定义网站",
                "description": "抓取任意网站的HTML页面",
                "handler": self._fetch_custom_site
            },
            "9": {
                "label": "提取图鉴图片链接",
                "description": "从抓取的图鉴页面提取角色图片链接",
                "handler": self._run_workflow,
                "workflow": "character_baike",
                "incremental": False
            },
            "10": {
                "label": "提取用户发帖时间",
                "description": "从用户主页提取发帖时间和标题",
                "handler": self._run_workflow,
                "workflow": "user_posts",
                "incremental": False
            },
            "11": {
                "label": "增量提取用户发帖",
                "description": "增量提取并合并新旧数据",
                "handler": self._run_workflow,
                "workflow": "user_posts",
                "incremental": True
            },
            "12": {
                "label": "提取原神新闻数据",
                "description": "从新闻页面提取标题和链接",
                "handler": self._run_workflow,
                "workflow": "genshin_news",
                "incremental": False
            },
            "13": {
                "label": "增量提取新闻数据",
                "description": "增量提取并合并新旧数据",
                "handler": self._run_workflow,
                "workflow": "genshin_news",
                "incremental": True
            },
            "14": {
                "label": "查看备份文件",
                "description": "查看所有数据备份文件",
                "handler": self._show_backups
            },
            "15": {
                "label": "恢复备份数据",
                "description": "从备份文件恢复数据",
                "handler": self._restore_backup
            },
            "16": {
                "label": "查看当前配置",
                "description": "显示当前的配置信息",
                "handler": self._show_config
            },
            "17": {
                "label": "修改配置参数",
                "description": "修改URL、超时时间等配置",
                "handler": self._modify_config
            },
            "18": {
                "label": "重新加载配置",
                "description": "从配置文件重新加载配置",
                "handler": self._reload_config
            },
            "19": {
                "label": "系统信息",
                "description": "显示系统环境和依赖信息",
                "handler": self._show_system_info
            }
        }

    def _clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def _print_header(self):
        print("=" * 70)
        print(f"           {self.title}")
        print("=" * 70)
        print("  基于Playwright的米游社数据抓取和提取工具")
        print("=" * 70)

    def _print_menu(self):
        for key in sorted(self.options.keys(), key=int):
            option = self.options[key]
            print(f"  {key}. {option['label']}")
            print(f"      {option['description']}")

        print("=" * 70)
        print("  0. 退出程序")
        print("=" * 70)

    def _run_workflow(self, workflow_name: str, incremental: bool = False):
        mode = "增量" if incremental else "全量"
        print(f"\n[START] {mode}处理: {workflow_name}")
        workflow = Workflow(workflow_name, incremental=incremental)
        workflow.run()

    def _fetch_tutorial_page(self):
        print("\n开始抓取米游社教程页面...")
        print("默认教程ID: mh4imrrhzdzi")

        tutorial_id = input("请输入教程ID [mh4imrrhzdzi]: ").strip()
        if not tutorial_id:
            tutorial_id = "mh4imrrhzdzi"

        workflow = Workflow("tutorial", tutorial_id=tutorial_id)
        workflow.scrape()
        print(f"[OK] 教程页面抓取完成: {tutorial_id}")

    def _extract_tutorial_data(self):
        print("\n开始提取教程页面角色数据...")
        print("默认教程ID: mh4imrrhzdzi")

        tutorial_id = input("请输入教程ID [mh4imrrhzdzi]: ").strip()
        if not tutorial_id:
            tutorial_id = "mh4imrrhzdzi"

        workflow = Workflow("tutorial", tutorial_id=tutorial_id)
        data = workflow.extract()

        if data:
            workflow.save(data)
            print(f"[OK] 提取完成！共 {len(data)} 个角色")
            for char in data[:5]:
                print(f"  {char.id} - {char.name}")
            if len(data) > 5:
                print(f"  ... 还有 {len(data) - 5} 个角色")
        else:
            print("[ERROR] 未找到角色数据")

    def _fetch_custom_site(self):
        print("\n开始抓取自定义网站...")
        url = input("请输入要抓取的网站URL: ").strip()

        if not url:
            print("[ERROR] URL不能为空")
            return

        filename = input("请输入输出文件名 [custom_page.html]: ").strip()
        if not filename:
            filename = "custom_page.html"

        workflow = CustomWorkflow(url, filename)
        workflow.scrape()
        print(f"[OK] 自定义页面抓取完成: {filename}")

    def _show_config(self):
        print("\n[CONFIG] 当前配置信息：")
        print(f"   用户URL: {config_manager.get('sources.user_posts.url')}")
        print(f"   百科URL: {config_manager.get('sources.character_baike.url')}")
        print(f"   新闻URL: {config_manager.get('sources.genshin_news.url')}")
        print(f"   无头模式: {config_manager.get('browser.headless')}")
        print(f"   等待时间: {config_manager.get('browser.wait_seconds')}秒")
        print(f"   超时时间: {config_manager.get('browser.timeout')}毫秒")
        print(f"   重试次数: {config_manager.get('retry.max_attempts')}")
        print(f"   增量更新: {config_manager.get('incremental.enabled')}")
        print(f"   备份功能: {config_manager.get('backup.enabled')}")
        print(f"   最大备份数: {config_manager.get('backup.max_backups')}")

    def _show_backups(self):
        print("\n[BACKUP] 备份文件列表：")
        print("=" * 70)

        data_files = ["posts.txt", "news.txt", "image_urls.txt"]
        for data_file in data_files:
            print(f"\n{data_file} 备份：")
            backups = self.backup_manager.list_backups(data_file)
            if backups:
                for i, backup in enumerate(backups, 1):
                    size_kb = backup.size / 1024
                    print(f"  {i}. {backup.filename}")
                    print(f"     创建时间: {backup.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"     文件大小: {size_kb:.2f} KB")
            else:
                print("  无备份文件")

        print("=" * 70)

    def _restore_backup(self):
        print("\n[RESTORE] 恢复备份数据：")
        data_files = ["posts.txt", "news.txt", "image_urls.txt"]

        for i, data_file in enumerate(data_files, 1):
            print(f"{i}. 恢复 {data_file}")
        print("0. 返回")

        choice = input("\n请选择操作：").strip()

        if choice == "0":
            return

        try:
            index = int(choice) - 1
            if 0 <= index < len(data_files):
                self._restore_file_backup(data_files[index])
            else:
                print("[ERROR] 序号无效")
        except ValueError:
            print("[ERROR] 请输入有效数字")

    def _restore_file_backup(self, filename: str):
        print(f"\n[RESTORE] {filename} 备份恢复：")

        backups = self.backup_manager.list_backups(filename)
        if not backups:
            print("[WARN] 无可用备份文件")
            return

        print("可用的备份文件：")
        for i, backup in enumerate(backups, 1):
            print(f"  {i}. {backup.filename} ({backup.created_at.strftime('%Y-%m-%d %H:%M:%S')})")

        choice = input("\n请选择要恢复的备份序号（输入0返回）：").strip()

        if choice == "0":
            return

        try:
            index = int(choice) - 1
            if 0 <= index < len(backups):
                backup_path = backups[index].filepath
                target_path = os.path.join(config_manager.get_output_dir("data"), filename)

                if self.backup_manager.restore_backup(backup_path, target_path):
                    print("[OK] 数据已成功恢复")
                else:
                    print("[ERROR] 数据恢复失败")
            else:
                print("[ERROR] 序号无效")
        except ValueError:
            print("[ERROR] 请输入有效数字")

    def _modify_config(self):
        print("\n[SETTINGS] 配置修改（直接回车保持原值）")

        current_url = config_manager.get("sources.user_posts.url")
        new_url = input(f"用户URL [{current_url}]: ").strip()
        if new_url:
            config_manager._config.sources["user_posts"].url = new_url

        current_baike = config_manager.get("sources.character_baike.url")
        new_baike = input(f"百科URL [{current_baike}]: ").strip()
        if new_baike:
            config_manager._config.sources["character_baike"].url = new_baike

        current_wait = config_manager.get("browser.wait_seconds")
        new_wait = input(f"等待时间(秒) [{current_wait}]: ").strip()
        if new_wait and new_wait.isdigit():
            config_manager._config.browser.wait_seconds = int(new_wait)

        config_manager.save_config()
        print("[OK] 配置已保存")

    def _reload_config(self):
        config_manager.load_config()
        print("[OK] 配置已重新加载")

    def _show_system_info(self):
        print("\n[SYSTEM] 系统信息：")
        print(f"   操作系统: {platform.system()} {platform.release()}")
        print(f"   Python版本: {platform.python_version()}")
        print(f"   工作目录: {os.path.dirname(__file__)}")

        try:
            import playwright
            from playwright._repo_version import version
            print(f"   Playwright版本: {version}")
        except ImportError:
            print("   Playwright: 未安装")

    def run(self):
        logger.info("米游社工具箱启动")

        while True:
            self._clear_screen()
            self._print_header()
            self._print_menu()

            choice = input("\n请输入序号：").strip()

            if choice == "0":
                print("\n感谢使用米游社工具箱，再见！")
                logger.info("米游社工具箱退出")
                sys.exit(0)

            if choice in self.options:
                try:
                    option = self.options[choice]
                    handler = option["handler"]

                    if "workflow" in option:
                        handler(option["workflow"], option.get("incremental", False))
                    else:
                        handler()

                    input("\n按回车键继续...")
                except KeyboardInterrupt:
                    print("\n\n操作已取消")
                    input("按回车键继续...")
                except Exception as e:
                    logger.error(f"执行出错: {e}", exc_info=True)
                    print(f"\n[ERROR] 执行出错: {e}")
                    input("按回车键继续...")
            else:
                print("[ERROR] 无效的选择，请重新输入")
                input("按回车键继续...")


@logger.catch
def main():
    print("[START] 正在初始化米游社工具箱...")

    try:
        import playwright
        print("[OK] Playwright依赖检查通过")
    except ImportError:
        print("[ERROR] 缺少Playwright依赖，请运行: pip install playwright")
        print("然后运行: playwright install chromium")
        return

    toolkit = ToolKitCLI()
    toolkit.run()


if __name__ == "__main__":
    main()