# Installation

## Requirements

- Python 3.11 or higher
- Microsoft Exchange Server access
- Valid domain credentials

## Install from PyPI

Using pip:
```bash
pip install exmailer
```
Using uv (recommended):

```bash
uv pip install exmailer
```
## Install from Source

Clone the repository:

```bash
git clone https://github.com/aerosadegh/exmailer.git
cd exmailer
```
Install with uv:

```bash
uv sync
```

Or with pip:

```bash
pip install -e .
```
## Verify Installation

```python
import exmailer
print(exmailer.__version__)
```
## Development Installation

For development, install with additional dependencies:

```bash
uv sync --all-extras
```
Or:

```bash
pip install -e ".[dev]"
```
This includes:

- pytest for testing
- black for code formatting
- ruff for linting
- mypy for type checking
- pre-commit hooks
