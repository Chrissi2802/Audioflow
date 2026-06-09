# Installation Guide

This guide covers different ways to install and run AudioFlow-CLI.

## Prerequisites

- Python 3.11 or higher
- FFmpeg (for audio processing)

### System Dependencies

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3 python3-pip ffmpeg
```

#### macOS
```bash
# Using Homebrew
brew install python ffmpeg

# Using MacPorts
sudo port install python311 ffmpeg
```

#### Windows
1. Install Python from [python.org](https://python.org)
2. Install FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
3. Add FFmpeg to your PATH

## Installation Methods

### Method 1: PyPI (Recommended)

```bash
pip install audioflow-cli
```

### Method 2: Poetry

```bash
poetry add audioflow-cli
```

### Method 3: Development Installation

```bash
# Clone repository
git clone https://github.com/christopher-data/audioflow-cli.git
cd audioflow-cli

# Install with Poetry
poetry install

# Or install with pip
pip install -e .
```

### Method 4: Docker

```bash
# Pull image
docker pull audioflow/audioflow-cli

# Or build locally
git clone https://github.com/christopher-data/audioflow-cli.git
cd audioflow-cli
docker build -t audioflow-cli .
```

## Verification

Test your installation:

```bash
# Check version
audioflow --version

# Show help
audioflow --help

# Test download (with a short video)
audioflow info "https://www.youtube.com/watch?v=jNQXAC9IVRw"
```

## Configuration

### Environment Variables

Set these environment variables to customize AudioFlow:

```bash
export AUDIOFLOW_OUTPUT_DIR="$HOME/Downloads/AudioFlow"
export AUDIOFLOW_AUDIO_QUALITY="192"
export AUDIOFLOW_MAX_CONCURRENT_DOWNLOADS="3"
export AUDIOFLOW_ORGANIZE_BY_ARTIST="true"
```

### Configuration File

Create `~/.audioflow/config.yaml` (coming in future version):

```yaml
output_dir: "~/Downloads/AudioFlow"
audio_quality: "192"
audio_format: "mp3"
max_concurrent_downloads: 3
organize_by_artist: true
```

## Troubleshooting

### Common Issues

#### FFmpeg Not Found
```
Error: FFmpeg not found
```
**Solution**: Install FFmpeg and ensure it's in your PATH.

#### Permission Denied
```
Permission denied: '/path/to/output'
```
**Solution**: Check directory permissions or use a different output directory.

#### Python Version
```
Requires Python 3.11+
```
**Solution**: Update Python or use a virtual environment with the correct version.

### Docker Issues

#### Volume Permissions
```bash
# Fix permission issues on Linux
docker run --user $(id -u):$(id -g) -v $(pwd)/downloads:/downloads audioflow-cli
```

#### Memory Issues
```bash
# Increase Docker memory limit
docker run -m 1g audioflow-cli
```

### Getting Help

If you encounter issues:

1. Check the [FAQ](faq.md)
2. Search [existing issues](https://github.com/christopher-data/audioflow-cli/issues)
3. Create a [new issue](https://github.com/christopher-data/audioflow-cli/issues/new) with:
   - Your OS and Python version
   - Complete error message
   - Steps to reproduce

## Uninstallation

### PyPI Installation
```bash
pip uninstall audioflow-cli
```

### Poetry Installation
```bash
poetry remove audioflow-cli
```

### Docker
```bash
docker rmi audioflow-cli
```

## Upgrading

### PyPI
```bash
pip install --upgrade audioflow-cli
```

### Poetry
```bash
poetry update audioflow-cli
```

### Docker
```bash
docker pull audioflow/audioflow-cli:latest
```