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

## Testing Strategy

### Test Architecture
The test suite uses a **layered, session-scoped fixture approach** for clean separation and efficient execution:

```
tests/
  unit/          # Pure logic tests (no DB)
  functional/    # DB tests using shared fixtures
  deep_cycle/    # Tests that reset DB (run on demand)
```

### Data Isolation
Tests use an incremental count strategy for data isolation rather than resetting the database between tests:

- **Baseline Capture**: Each test captures initial document and chunk counts before operations
- **Incremental Validation**: Tests verify that counts increment by the expected amount (e.g., +1 document, +N chunks)
- **Shared Database**: Tests run against a shared database state, allowing for realistic testing scenarios
- **Deep Cycle Tests**: Full database resets are only performed for tests marked with `@pytest.mark.deep_cycle` and enabled via `DEEP_TEST_CYCLE=1`

### Test Categories
- **Primary Tests** (`@pytest.mark.primary`): Core functional behavior - quick smoke tests
- **Coverage Tests** (`@pytest.mark.coverage`): Additional edge-case coverage
- **Deep Cycle Tests** (`@pytest.mark.deep_cycle`): Tests that reset DB or run >10s

### Test Phases
- **Phase Reset** (`@pytest.mark.phase_reset`): Assert DB schema/health after reset
- **Phase Ingest** (`@pytest.mark.phase_ingest`): Verify ingestion results  
- **Phase Retrieval** (`@pytest.mark.phase_retrieval`): Verify retrieval / embedding

### Running Tests

Quick smoke (seconds):
```bash
pytest -m primary -q
```

Full functional (no deep reset):
```bash
pytest -m "primary or coverage" -q
```

Deep cycle (nightly):
```bash
pytest -m deep_cycle -q
```

All tests:
```bash
pytest -q
```

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
