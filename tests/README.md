# Tests Directory

This directory contains test files and test fixtures.

## Directory Structure

```
tests/
├── README.md              # This file
├── fixtures/              # Test data and sample files
│   ├── test_message.txt   # Sample test message for duplicate detection
│   └── test_upload.txt    # Sample test document for upload testing
└── [other test files]     # Various test modules
```

## Fixtures

The `fixtures/` directory contains test data files used by the test suite:

### test_message.txt
- Sample conversation message mentioning a file
- Used to test filter reactions to file mentions
- Simulates real user conversations for testing

### test_upload.txt  
- Sample document content for upload testing
- Used to test duplicate detection algorithms
- Contains structured test data for validation

## Usage

These fixtures can be used in automated tests:

```python
# Example test usage
def test_duplicate_detection():
    with open('tests/fixtures/test_upload.txt', 'r') as f:
        test_content = f.read()
    # Use test_content for duplicate detection testing
```

## Integration with Test Suite

These fixtures support:
- **Duplicate Detection Testing**: Upload simulation and comparison
- **Filter Testing**: Message processing and response validation  
- **Performance Testing**: Consistent test data for benchmarking
- **Integration Testing**: End-to-end workflow validation

## Maintenance

When adding new test fixtures:
1. Use descriptive filenames
2. Include appropriate test metadata
3. Document expected behavior
4. Keep files small and focused
5. Update this README with new additions
