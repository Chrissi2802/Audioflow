# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

AudioFlow is a modern Python-based audio download tool designed for professional use. The project is currently in early development phase with a comprehensive architecture plan for building a CLI-first audio download utility with multiple interface options.

### Project Vision
- Professional audio download tool with modern Python practices
- CLI-first approach with potential web UI and API endpoints
- Batch processing capabilities with concurrent downloads
- Smart metadata handling and file organization
- Docker-ready deployment

## Development Commands

### Code Quality and Linting
```bash
# Linting (configured in .flake8)
flake8 .

# Type checking
mypy src/

# Code formatting
black .
isort .

# Security scanning
bandit -r src/
```

### Testing
```bash
# Run tests with coverage
pytest --cov=src/ --cov-report=html --cov-report=term-missing

# Run specific test files
pytest tests/test_specific.py

# Run with verbose output
pytest -v
```

### Development Environment
```bash
# Install dependencies (when available)
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run development server/CLI
python -m audioflow.cli

# Docker development
docker build -t audioflow .
docker run -v $(pwd)/downloads:/downloads audioflow
```

## Architecture Overview

### Core Components (Planned)
- **CLI Interface**: Click-based command line tool with Rich UI
- **Download Engine**: Async-based downloader using yt-dlp
- **File Manager**: Smart organization with metadata extraction
- **Configuration System**: Pydantic-based settings management
- **Models**: Type-safe data models for download operations

### Package Structure
```
src/
├── audioflow/
│   ├── __init__.py
│   ├── cli.py              # Click-based CLI interface
│   ├── core/
│   │   ├── downloader.py   # Main download engine
│   │   ├── config.py       # Configuration management
│   │   └── utils.py        # Utility functions
│   └── models/
│       └── download.py     # Data models
tests/
├── test_cli.py
├── test_downloader.py
└── conftest.py             # Test fixtures
```

### Technology Stack
- **Python 3.11+**: Modern Python features
- **yt-dlp**: Robust video/audio downloading
- **Click + Rich**: Professional CLI with beautiful output
- **Pydantic**: Data validation and settings management
- **asyncio**: Async processing for concurrent downloads
- **mutagen**: Audio metadata handling
- **pytest**: Testing framework

## Development Guidelines

### Code Quality Standards
- Line length: 88 characters (Black compatible)
- Max complexity: 10 (configured in .flake8)
- Type hints required for all functions
- Comprehensive test coverage (>80% target)
- Follow async/await patterns for I/O operations

### CLI Design Principles
- Single command for common use cases
- Batch processing for multiple URLs
- Progress tracking with Rich progress bars
- Configurable output directories and quality settings
- Error handling with retry mechanisms

### File Organization
- Organize downloads by artist when metadata available
- Support custom output directories
- Generate clean, sanitized filenames
- Embed metadata in downloaded files

## Key Features (Planned)

### Core Functionality
- Single URL and batch download support
- Multiple audio quality options (128k-320k)
- Parallel/concurrent downloads with limits
- Automatic retry on failures
- Progress tracking and status reporting

### Advanced Features
- Smart metadata extraction and embedding
- Artist-based folder organization
- Docker containerization
- Configuration file support
- Comprehensive error handling

## Development Phases

### Phase 1: Core CLI (Current)
- Basic project structure ✓
- CLI framework with Click
- Single URL download capability
- Basic error handling

### Phase 2: Enhanced Downloads
- Batch processing from file input
- Async/parallel download implementation
- Quality selection options
- Progress tracking

### Phase 3: Metadata & Organization
- Metadata extraction and embedding
- Smart file organization
- Duplicate detection
- Configuration management

## Legal and Compliance

### Important Considerations
- Tool is for educational/research purposes
- Users responsible for compliance with platform ToS
- No DRM circumvention
- Rate limiting implemented to respect services
- Apache 2.0 License for open source distribution

### Disclaimer Requirements
Always include appropriate disclaimers about legal use and user responsibility when working on download functionality.

## Future Roadmap

### Potential Extensions
- Web UI with Streamlit
- REST API with FastAPI  
- Database integration for history
- Cloud storage integration
- Advanced analytics and reporting

The project follows modern Python development practices with emphasis on type safety, async programming, and professional CLI design.