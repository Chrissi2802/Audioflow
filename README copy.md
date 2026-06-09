# AudioFlow-CLI

[![CI Status](https://github.com/christopher-data/audioflow-cli/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/christopher-data/audioflow-cli/actions)
[![PyPI version](https://badge.fury.io/py/audioflow-cli.svg)](https://badge.fury.io/py/audioflow-cli)
[![Python versions](https://img.shields.io/pypi/pyversions/audioflow-cli.svg)](https://pypi.org/project/audioflow-cli/)
[![License](https://img.shields.io/github/license/christopher-data/audioflow-cli.svg)](https://github.com/christopher-data/audioflow-cli/blob/main/LICENSE)

Modern, professional audio download tool with advanced features and multiple interfaces.

## ✨ Features

- 🎵 **High-Quality Downloads**: Configurable audio quality (128k-320k kbps)
- ⚡ **Parallel Processing**: Concurrent downloads for maximum efficiency  
- 📁 **Smart Organization**: Automatic folder structure by artist
- 🎯 **Batch Processing**: Download multiple URLs from file
- 🔄 **Retry Logic**: Robust error handling with automatic retries
- 📊 **Progress Tracking**: Real-time download progress with Rich UI
- 🎨 **Beautiful CLI**: Professional command-line interface
- 🐳 **Docker Support**: Container-ready deployment
- 🔧 **Configurable**: Extensive customization options
- 🏷️ **Metadata Handling**: Automatic extraction and embedding

## 🚀 Quick Start

### Installation

```bash
# Via pip (when published)
pip install audioflow-cli

# Via Poetry
poetry add audioflow-cli

# Via Docker
docker pull audioflow/audioflow-cli
```

### Development Installation

```bash
# Clone repository
git clone https://github.com/christopher-data/audioflow-cli.git
cd audioflow-cli

# Install with Poetry
poetry install

# Or with pip
pip install -e .
```

### Basic Usage

```bash
# Download single audio
audioflow download "https://youtube.com/watch?v=example"

# Batch download from file
audioflow batch urls.txt

# High quality download
audioflow download "https://youtube.com/watch?v=example" --quality 320

# Custom output directory
audioflow download "https://youtube.com/watch?v=example" --output ~/Music

# Get media information
audioflow info "https://youtube.com/watch?v=example"

# Show configuration
audioflow config
```

## 📖 Advanced Usage

### Quality Options
- `128`: Low quality (128 kbps)
- `192`: Medium quality (192 kbps) - Default
- `256`: High quality (256 kbps)
- `320`: Ultra quality (320 kbps)

### Batch Downloads

Create a text file with URLs (one per line):

```text
# My favorite songs
https://youtube.com/watch?v=song1
https://youtube.com/watch?v=song2

# Comments are supported
https://youtube.com/watch?v=song3
```

Then run:

```bash
audioflow batch my_songs.txt --quality 320 --concurrent 5 --retry
```

### Docker Usage

```bash
# Basic usage
docker run -v $(pwd)/downloads:/downloads audioflow/audioflow-cli download "URL"

# Batch processing
docker run -v $(pwd)/downloads:/downloads -v $(pwd)/urls.txt:/urls.txt audioflow/audioflow-cli batch /urls.txt

# With docker-compose
docker-compose up audioflow
```

## 🛠️ Development

### Setup Development Environment

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Clone and setup
git clone https://github.com/christopher-data/audioflow-cli.git
cd audioflow-cli
poetry install

# Install pre-commit hooks
poetry run pre-commit install
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/audioflow --cov-report=html

# Run specific test file
poetry run pytest tests/test_downloader.py

# Run with verbose output
poetry run pytest -v
```

### Code Quality

```bash
# Format code
poetry run black src/ tests/
poetry run isort src/ tests/

# Lint code
poetry run flake8 src/ tests/

# Type checking
poetry run mypy src/audioflow/

# Security scan
poetry run bandit -r src/audioflow/

# Run all checks
poetry run pre-commit run --all-files
```

## 🔧 Configuration

AudioFlow can be configured via environment variables:

```bash
export AUDIOFLOW_OUTPUT_DIR="/path/to/downloads"
export AUDIOFLOW_AUDIO_QUALITY="320"
export AUDIOFLOW_MAX_CONCURRENT_DOWNLOADS="5"
export AUDIOFLOW_ORGANIZE_BY_ARTIST="true"
```

## 🏗️ Architecture

AudioFlow follows modern Python development practices:

- **Async/Await**: Efficient concurrent processing
- **Type Hints**: Full type safety with mypy
- **Pydantic Models**: Data validation and serialization
- **Rich CLI**: Beautiful terminal interface
- **Comprehensive Testing**: >90% test coverage
- **Docker Support**: Container-ready deployment

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on:

- Code of Conduct
- Development process
- Pull request process
- Coding standards

## 📄 License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

## ⚖️ Legal Disclaimer

This software is provided for educational and research purposes only. Users are solely responsible for ensuring their use complies with applicable laws and platform terms of service. The authors assume no liability for misuse of this software.

Please respect content creators and platform terms of service. Only download content you have permission to download.

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Powerful media downloader
- [Click](https://click.palletsprojects.com/) - Python CLI framework
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal formatting
- [Pydantic](https://docs.pydantic.dev/) - Data validation library
