# Use bash on Unix and PowerShell on Windows
set shell := ["bash", "-cu"]
set windows-shell := ["pwsh", "-NoLogo", "-Command"]

# Default recipe: show help
default:
    just --list

# Install docs dependencies
docs-install:
    pip install -r docs/requirements.txt

# Install package + docs deps (dev mode)
docs-dev:
    pip install -e .
    pip install -r docs/requirements.txt

# Serve docs
docs-serve:
    mkdocs serve

# Build docs
docs-build:
    mkdocs build

# Cross-platform clean (uses Python instead of rm)
docs-clean:
    python -c "import shutil, pathlib; shutil.rmtree('site', ignore_errors=True)"
