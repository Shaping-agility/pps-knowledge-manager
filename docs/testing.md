# Testing Guide

## Test Categories

### Regular Tests
Most tests run by default and don't require database resets. These include:
- Unit tests for individual components
- Integration tests that don't modify persistent state
- Health checks and connection tests

### Deep Cycle Tests
Some tests require a clean database state and perform database resets. These are marked with the `deep_cycle` marker and are skipped by default to preserve your manual inspection data.

## Running Tests

### Default Test Run (Recommended for Development)
```bash
pytest tests/
```
- Runs all regular tests
- Skips deep cycle tests
- Preserves your database state for manual inspection

### Deep Cycle Tests (When Needed)
You can run deep cycle tests in two ways:

**Option 1: Environment Variable**
```bash
DEEP_TEST_CYCLE=1 pytest tests/
```

**Option 2: Pytest Marker**
```bash
pytest tests/ -m deep_cycle
```

### Run Everything (Full Test Suite)
```bash
DEEP_TEST_CYCLE=1 pytest tests/
```

## Deep Cycle Test Examples

Currently, the following tests are marked as deep cycle:
- `TestIdempotentIngestion.test_duplicate_ingestion_does_not_create_duplicates`
- `TestIdempotentIngestion.test_different_file_paths_create_separate_documents`

These tests verify idempotent behavior by:
1. Resetting the database to a clean state
2. Running ingestion operations
3. Verifying no duplicate data is created

## CI/CD Integration

For automated testing, set the environment variable in your CI pipeline:
```yaml
# GitHub Actions example
env:
  DEEP_TEST_CYCLE: 1
```

This ensures all tests run in CI while keeping development convenient. 