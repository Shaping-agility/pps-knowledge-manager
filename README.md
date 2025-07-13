# PPS Knowledge Manager

## Description
Brief description of what this project does.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/pps-knowledge-manager.git
cd pps-knowledge-manager
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```bash
python src/pps knowledge manager/main.py
```

## Development

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

Run tests:
```bash
# Regular tests (preserves database state)
pytest

# Deep cycle tests (resets database)
DEEP_TEST_CYCLE=1 pytest

# Run all tests including deep cycle
DEEP_TEST_CYCLE=1 pytest tests/
```

For more testing options, see [docs/testing.md](docs/testing.md).

## Test Timeouts

All tests are auto-terminated after 30 seconds using [pytest-timeout](https://pypi.org/project/pytest-timeout/). This prevents hung tests from blocking CI or local runs. You can override the timeout per test with the `@pytest.mark.timeout(seconds)` marker.

## Project Structure

```
pps-knowledge-manager/
├── src/pps knowledge manager/     # Main source code
├── tests/              # Test files
├── data/               # Data files
├── docs/               # Documentation
└── scripts/            # Utility scripts
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

Add your license here.
