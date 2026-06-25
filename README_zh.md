# 米游社工具箱 (miHoYo ToolKit)

Language / 语言: [English](README.md) | [中文](README_zh.md)

基于 Playwright 的米游社数据抓取和提取工具。采用策略模式、管道模式和增量更新机制，实现高可扩展、低耦合的架构设计。

## 功能特性

- **策略模式**：抓取策略和提取策略完全解耦，便于扩展新数据源
- **管道处理**：可组合的数据处理步骤（去重、排序、备份、索引重排）
- **增量更新**：智能检测已存在数据，避免重复请求，支持数据合并
- **配置驱动**：YAML 配置文件 + Pydantic 类型验证，无需修改代码即可调整参数
- **双模式支持**：同步和异步两种网页抓取模式，适应不同性能需求
- **统一异常处理**：装饰器实现的错误捕获和自动重试机制
- **自动备份恢复**：数据修改前自动备份，支持查看和恢复历史版本

## 项目结构

```text
tool_kit/
├── cli/                    # 命令行界面
│   └── main.py             # 交互式菜单入口
├── core/                   # 核心模块
│   ├── config.py           # 配置管理（基于 Pydantic）
│   └── exceptions.py       # 自定义异常类
├── models/                 # 数据模型层
│   └── base.py             # ScrapedData 基类及具体数据类型
├── pipelines/              # 管道层
│   ├── base.py             # 管道步骤（去重、排序、备份等）
│   └── workflow.py         # 工作流编排
├── strategies/             # 策略层
│   ├── scraping.py         # 抓取策略（同步/异步/新闻页）
│   └── extraction.py       # 提取策略（图片/新闻/帖子/教程）
├── utils/                  # 工具模块
│   ├── backup.py           # 备份管理器
│   ├── decorators.py       # 错误处理和重试装饰器
│   └── progress.py         # 进度条工具
├── tests/                  # 单元测试
├── config.yaml             # 项目配置文件
├── pyproject.toml          # 项目元数据和依赖
└── main.py                 # 程序入口
```

## 环境要求

- Python >= 3.10
- Playwright >= 1.40.0
- 完整依赖见 `pyproject.toml`

## 安装步骤

### 1. 进入项目目录

```bash
cd d:\LingLan\material\project\github\vers123\tool_kit
```

### 2. 创建并激活虚拟环境

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
# 或以可编辑模式安装
pip install -e .
```

### 4. 安装 Playwright 浏览器

```bash
playwright install chromium
```

## 使用方法

### 通过 CLI 菜单运行

```bash
python main.py
```

菜单提供以下功能：

- 抓取用户发帖主页 / 增量抓取
- 抓取角色图鉴页面
- 抓取原神新闻页面 / 增量抓取
- 抓取米游社教程页面
- 提取各类数据（图片链接、发帖时间、新闻数据）
- 查看和恢复备份
- 查看和修改配置

### 编程方式调用工作流

```python
from pipelines import Workflow

# 抓取用户发帖
workflow = Workflow("user_posts")
workflow.run()

# 增量更新
workflow = Workflow("user_posts", incremental=True)
workflow.run()

# 抓取原神新闻
workflow = Workflow("genshin_news")
workflow.run()
```

### 直接使用策略

```python
from strategies import create_scraper, create_extractor

# 抓取页面
scraper = create_scraper(
    url="https://www.miyoushe.com/ys/accountCenter/postList?id=75276539",
    output_filename="user_posts.html",
    strategy_type="sync"
)
html_content = scraper.scrape()

# 提取数据
extractor = create_extractor("post", "html/user_posts.html", "data/posts.txt")
data = extractor.extract()
```

## 配置说明

编辑 `config.yaml` 自定义行为：

```yaml
browser:
  headless: false              # 是否显示浏览器窗口
  wait_seconds: 3              # 页面初始等待时间
  timeout: 30000               # 页面加载超时（毫秒）

sources:
  user_posts:
    name: "用户发帖"
    url: "https://www.miyoushe.com/ys/accountCenter/postList?id=75276539"
    extractor: "post"
  genshin_news:
    name: "原神新闻"
    url: "https://ys.mihoyo.com/main/news"
    extractor: "news"

incremental:
  enabled: true                # 启用增量更新
  stop_on_existing: true       # 遇到已存在数据时停止滚动
```

## 运行测试

```bash
# 先激活虚拟环境
.\venv\Scripts\activate

# 运行全部测试
python -m unittest discover -s tests -v

# 运行指定测试模块
python -m unittest tests.test_models -v
```

## 架构设计

### 策略模式 (Strategy Pattern)

**抓取策略**：

- `ScrapingStrategy`：抽象基类，定义抓取接口
  - `SyncScrapingStrategy`：同步浏览器自动化
  - `AsyncScrapingStrategy`：异步浏览器自动化
  - `NewsScrapingStrategy`：新闻页面专用（支持点击"加载更多"）

**提取策略**：

- `ExtractionStrategy`：抽象基类，定义提取接口
  - `ImageExtractionStrategy`：从图鉴页面提取角色图片链接
  - `NewsExtractionStrategy`：从新闻页面提取标题和日期
  - `PostExtractionStrategy`：从用户主页提取发帖时间和标题（支持相对时间解析）
  - `TutorialExtractionStrategy`：从教程页面提取角色编号和名称

### 管道模式 (Pipeline Pattern)

数据依次流经可配置的处理步骤：

1. **DeduplicationStep**：根据唯一键去重
2. **SortingStep**：按日期或索引排序
3. **IndexingStep**：重新分配连续序号
4. **BackupStep**：覆盖前创建带时间戳的备份

### 工作流 (Workflow)

`Workflow` 类整合抓取、提取、保存流程：

```text
配置驱动 → 选择策略 → 抓取页面 → 提取数据 → 管道处理 → 保存结果
```

## License

MIT License
