# Testing Guide

## Test Architecture Overview

The PPS Knowledge Manager uses a **layered, session-scoped fixture approach** for clean separation and efficient execution. This architecture ensures tests are order-independent, parallel-safe, and maintain clear intent separation.

### Directory Structure
```
tests/
  unit/          # Pure logic tests (no DB dependencies)
  functional/    # DB tests using shared fixtures
  deep_cycle/    # Tests that reset DB (run on demand)
```

### Test Categories

#### Primary Tests (`@pytest.mark.primary`)
Core functional behavior tests that serve as quick smoke tests:
- Essential functionality validation
- Core business logic verification
- Quick feedback for development

#### Coverage Tests (`@pytest.mark.coverage`)
Additional edge-case and robustness tests:
- Error handling scenarios
- Boundary condition testing
- Additional validation paths

#### Deep Cycle Tests (`@pytest.mark.deep_cycle`)
Tests that require database resets or run for extended periods:
- Full end-to-end workflows
- Performance testing
- Database state validation

### Test Phases

#### Phase Reset (`@pytest.mark.phase_reset`)
Tests that validate database schema and health after reset operations.

#### Phase Ingest (`@pytest.mark.phase_ingest`)
Tests that verify ingestion pipeline functionality and results.

#### Phase Retrieval (`@pytest.mark.phase_retrieval`)
Tests that validate retrieval, embedding, and similarity search capabilities.

## Fixture Architecture

### Session-Scoped Fixtures
Heavy operations are performed once per test session and shared across tests:

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def fresh_db():
    """Ensure database is reset to clean state once per test session."""
    mgr = SupabaseTestDataManager()
    assert mgr.reset(), "DB reset failed"
    yield

@pytest.fixture(scope="session")
def ingested_db(fresh_db):
    """Populate DB with sample data once per test session."""
    # Ingest sample data for retrieval tests
    yield result
```

### Data Isolation Strategy
Tests use incremental count validation rather than assuming clean database state:

```python
def test_ingestion_increments_counts(ingested_db, ingestion_pipeline):
    # Capture baseline counts
    initial_docs = ingestion_pipeline.storage_backend.get_document_count()
    initial_chunks = ingestion_pipeline.storage_backend.get_chunk_count()
    
    # Perform operation
    result = ingestion_pipeline.process_file(sample_file)
    
    # Validate increments
    assert final_docs == initial_docs + 1  # +1 document
    assert final_chunks == initial_chunks + result["chunks_created"]  # +N chunks
```

## Running Tests

### Quick Smoke Test (Development)
```bash
pytest -m primary -q
```
- Runs only primary tests
- Fast feedback (seconds)
- Validates core functionality

### Full Functional Test Suite
```bash
pytest -m "primary or coverage" -q
```
- Runs primary and coverage tests
- No database resets
- Comprehensive validation

### Deep Cycle Tests (When Needed)
```bash
pytest -m deep_cycle -q
```
- Runs tests that reset database
- Full end-to-end validation
- Performance and state testing

### Complete Test Suite
```bash
pytest -q
```
- Runs all tests in all categories
- Full validation including deep cycle
- Use for CI/CD or comprehensive testing

### Test by Phase
```bash
# Reset phase tests
pytest -m phase_reset -q

# Ingestion phase tests  
pytest -m phase_ingest -q

# Retrieval phase tests
pytest -m phase_retrieval -q
```

## Test Development Guidelines

### Writing New Tests

1. **Choose the right category**:
   - `@pytest.mark.primary` for core functionality
   - `@pytest.mark.coverage` for edge cases
   - `@pytest.mark.deep_cycle` for DB resets

2. **Use appropriate fixtures**:
   - `fresh_db` for tests needing clean state
   - `ingested_db` for tests needing sample data
   - `knowledge_manager` for core functionality

3. **Follow incremental count pattern**:
   ```python
   def test_my_functionality(ingested_db, knowledge_manager):
       # Capture baseline
       initial_count = knowledge_manager.storage_backend.get_document_count()
       
       # Perform operation
       result = knowledge_manager.some_operation()
       
       # Validate increment
       final_count = knowledge_manager.storage_backend.get_document_count()
       assert final_count == initial_count + expected_increment
   ```

### Test Organization

- **Primary tests** should be at the top of each test file
- **Coverage tests** should follow primary tests
- **Deep cycle tests** should be in the `deep_cycle/` directory
- Use descriptive test names that explain the behavior being tested

### Best Practices

1. **Document-Specific Validation**: When verifying ingestion results, assert counts scoped to the specific document (e.g. by `file_path`), never rely on global row counts.  This prevents brittle tests and avoids lazy database resets.
2. **Order Independence**: Tests should not depend on execution order
3. **Parallel Safety**: Tests should be safe to run in parallel
4. **Fast Feedback**: Primary tests should complete quickly
5. **Clear Intent**: Test names and marks should clearly communicate purpose
6. **Incremental Validation**: Use count-based validation rather than absolute state

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run primary tests
        run: pytest -m primary -q
      
      - name: Run full functional tests
        run: pytest -m "primary or coverage" -q
      
      - name: Run deep cycle tests
        run: pytest -m deep_cycle -q
```

### Environment Variables
- `OPENAI_API_KEY`: Required for embedding tests
- `SUPABASE_URL`: Supabase connection URL
- `SUPABASE_KEY`: Supabase service role key
- `SUPABASE_USER`: Database user (local development)
- `SUPABASE_PW`: Database password (local development)

## Troubleshooting

### Common Issues

1. **Test Timeouts**: Tests are automatically terminated after 30 seconds
2. **Database Connection**: Ensure Supabase is running and accessible
3. **Missing Files**: Some tests require sample data files in `data/raw/`
4. **Environment Variables**: Verify all required environment variables are set

### Debug Mode
```bash
# Run with verbose output
pytest -v

# Run with print statements visible
pytest -s

# Run specific test file
pytest tests/functional/test_ingestion.py -v
```

### Test Isolation
If tests are interfering with each other:
1. Check that tests use incremental count validation
2. Verify tests don't assume clean database state
3. Ensure tests use appropriate fixtures for data dependencies 