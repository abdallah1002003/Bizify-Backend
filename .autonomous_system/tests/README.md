# Autonomous System Test Suite

## Running Tests

### Install Dependencies
```bash
pip install pytest pytest-cov pytest-mock
```

### Run All Tests
```bash
pytest autonomous_system/tests/ -v
```

### Run Unit Tests Only
```bash
pytest autonomous_system/tests/unit/ -v
```

### Run Integration Tests Only
```bash
pytest autonomous_system/tests/integration/ -v
```

### Run with Coverage
```bash
pytest autonomous_system/tests/ --cov=autonomous_system --cov-report=html
```

### Run Specific Test File
```bash
pytest autonomous_system/tests/unit/test_pattern_learning.py -v
```

### Run Specific Test
```bash
pytest autonomous_system/tests/unit/test_pattern_learning.py::TestPatternLearningSystem::test_learn_pattern_success -v
```

## Test Structure

```
autonomous_system/tests/
├── conftest.py                          # Shared fixtures
├── unit/                                # Unit tests
│   ├── test_pattern_learning.py        # PatternLearningSystem tests
│   └── test_self_evolution.py          # SelfEvolutionSystem tests
└── integration/                         # Integration tests
    └── test_workflows.py                # End-to-end workflow tests
```

## Coverage Goals

- **Unit Tests**: 80%+ coverage of core modules
- **Integration Tests**: All major workflows covered
- **Performance Tests**: Search < 1s for 1000+ patterns

## Writing New Tests

### Unit Test Template
```python
import pytest
from autonomous_system.module import YourClass

@pytest.fixture
def your_fixture():
    return YourClass()

class TestYourClass:
    def test_something(self, your_fixture):
        result = your_fixture.method()
        assert result == expected
```

### Integration Test Template
```python
import pytest

class TestWorkflow:
    def test_end_to_end(self, integrated_system):
        # Setup
        # Execute workflow
        # Verify results
        pass
```
