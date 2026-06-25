# miHoYo ToolKit

Language / 语言: [English](README.md) | [中文](README_zh.md)

A Python-based data scraping and extraction toolkit for miHoYo community platforms (米游社). Built with Playwright, featuring strategy patterns, pipeline processing, and incremental updates.

## Features

- **Strategy Pattern**: Decoupled scraping and extraction strategies for extensibility
- **Pipeline Processing**: Composable data processing steps (deduplication, sorting, backup)
- **Incremental Updates**: Smart data merging to avoid redundant requests
- **Configuration-Driven**: YAML-based configuration with Pydantic validation
- **Dual Mode Support**: Both synchronous and asynchronous scraping modes
- **Robust Error Handling**: Unified exception handling with retry decorators
- **Backup & Restore**: Automatic data backup with configurable retention

## Project Structure

```text
tool_kit/
├── cli/                    # Command-line interface
│   └── main.py             # CLI entry point with interactive menu
├── core/                   # Core modules
│   ├── config.py           # Configuration management (Pydantic-based)
│   └── exceptions.py       # Custom exceptions
├── models/                 # Data models
│   └── base.py             # ScrapedData base class & concrete types
├── pipelines/              # Pipeline layer
│   ├── base.py             # Pipeline steps (dedup, sort, backup)
│   └── workflow.py         # Workflow orchestration
├── strategies/             # Strategy layer
│   ├── scraping.py         # Scraping strategies (sync/async/news)
│   └── extraction.py       # Extraction strategies (image/news/post/tutorial)
├── utils/                  # Utilities
│   ├── backup.py           # Backup manager
│   ├── decorators.py       # Error handling & retry decorators
│   └── progress.py         # Progress indicators
├── tests/                  # Unit tests
├── config.yaml             # Project configuration
├── pyproject.toml          # Project metadata
└── main.py                 # Program entry point
```

## Requirements

- Python >= 3.10
- Playwright >= 1.40.0
- See `pyproject.toml` for full dependencies

## Installation

### 1. Clone the repository

```bash
cd d:\LingLan\material\project\github\vers123\tool_kit
```

### 2. Create and activate virtual environment

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
# Or install in editable mode
pip install -e .
```

### 4. Install Playwright browsers

```bash
playwright install chromium
```

## Usage

### Run with CLI menu

```bash
python main.py
```

### Run specific workflow programmatically

```python
from pipelines import Workflow

# Scrape user posts
workflow = Workflow("user_posts")
workflow.run()

# Incremental update
workflow = Workflow("user_posts", incremental=True)
workflow.run()

# Scrape Genshin news
workflow = Workflow("genshin_news")
workflow.run()
```

### Use strategies directly

```python
from strategies import create_scraper, create_extractor

# Scrape a page
scraper = create_scraper(
    url="https://www.miyoushe.com/ys/accountCenter/postList?id=75276539",
    output_filename="user_posts.html",
    strategy_type="sync"
)
html_content = scraper.scrape()

# Extract data
extractor = create_extractor("post", "html/user_posts.html", "data/posts.txt")
data = extractor.extract()
```

## Configuration

Edit `config.yaml` to customize behavior:

```yaml
browser:
  headless: false              # Show browser window
  wait_seconds: 3              # Initial wait time
  timeout: 30000               # Page load timeout (ms)

sources:
  user_posts:
    name: "User Posts"
    url: "https://www.miyoushe.com/ys/accountCenter/postList?id=75276539"
    extractor: "post"
  genshin_news:
    name: "Genshin News"
    url: "https://ys.mihoyo.com/main/news"
    extractor: "news"

incremental:
  enabled: true                # Enable incremental updates
  stop_on_existing: true       # Stop when existing data found
```

## Running Tests

```bash
# Activate virtual environment first
.\venv\Scripts\activate

# Run all tests
python -m unittest discover -s tests -v

# Run specific test module
python -m unittest tests.test_models -v
```

## Architecture

### Strategy Pattern

- `ScrapingStrategy`: Abstract base for page scraping
  - `SyncScrapingStrategy`: Synchronous browser automation
  - `AsyncScrapingStrategy`: Asynchronous browser automation
  - `NewsScrapingStrategy`: News page with "load more" button handling

- `ExtractionStrategy`: Abstract base for data extraction
  - `ImageExtractionStrategy`: Extract image URLs from baike pages
  - `NewsExtractionStrategy`: Extract news titles and dates
  - `PostExtractionStrategy`: Extract user posts with date parsing
  - `TutorialExtractionStrategy`: Extract character IDs and names

### Pipeline Pattern

Data flows through configurable steps:

1. **DeduplicationStep**: Remove duplicate entries by unique key
2. **SortingStep**: Sort by date or index
3. **IndexingStep**: Reassign sequential indices
4. **BackupStep**: Create timestamped backups before overwriting

## License

MIT License
