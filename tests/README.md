# Tests

## Chạy Tests

### Chạy tất cả tests:
```bash
pytest
```

### Chạy tests với coverage:
```bash
pytest --cov=app --cov-report=html
```

### Chạy tests trong thư mục cụ thể:
```bash
# Chỉ test API endpoints
pytest tests/api/

# Chỉ test unit tests
pytest tests/unit/

# Chỉ test integration tests
pytest tests/integration/
```

### Chạy test file cụ thể:
```bash
pytest tests/api/test_extract_endpoint.py
```

### Chạy test function cụ thể:
```bash
pytest tests/api/test_extract_endpoint.py::test_extract_facts_success
```

### Chạy với verbose output:
```bash
pytest -v
```

### Chạy và dừng ở test đầu tiên fail:
```bash
pytest -x
```

### Chạy lại test vừa fail:
```bash
pytest --lf
```

## Cấu Trúc Tests

```
tests/
├── conftest.py              # Shared fixtures
├── api/                     # API endpoint tests
│   ├── test_extract_endpoint.py
│   ├── test_search_endpoint.py
│   ├── test_health_endpoint.py
│   └── test_async_example.py  # Ví dụ async testing
├── unit/                    # Unit tests
│   └── domains/
└── integration/             # Integration tests
```

## Xem Coverage Report

Sau khi chạy với `--cov-report=html`, mở file:
```
htmlcov/index.html
```

## Tài Liệu Chi Tiết

Xem [API Testing Guide](../../docs/API_TESTING_GUIDE.md) để biết chi tiết về cách viết tests.

