# Hướng dẫn cài đặt PIKA Memory System

## Yêu cầu hệ thống

- Python >= 3.9
- PostgreSQL (cho database)
- Milvus (cho vector store)
- Redis (cho caching)
- RabbitMQ (cho message queue, optional)
- Neo4j (cho graph store, optional)

## Cài đặt từ pyproject.toml

### 1. Cài đặt package và dependencies

```bash
# Cài đặt package với tất cả dependencies
pip install -e .

# Hoặc cài đặt với dev dependencies (bao gồm testing tools)
pip install -e ".[dev]"
```

### 2. Cài đặt từ source code

```bash
# Clone repository
git clone <repository-url>
cd pika-mem0-enterprise

# Tạo virtual environment (khuyến nghị)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows

# Cài đặt package
pip install -e .
```

### 3. Cài đặt dependencies riêng lẻ (nếu cần)

```bash
# Chỉ cài core dependencies
pip install -e .

# Cài thêm dev dependencies
pip install -e ".[dev]"
```

## Cấu hình môi trường

1. Copy file `.env.example` thành `.env` (nếu có)
2. Cập nhật các biến môi trường trong `.env`:

```bash
# PostgreSQL
POSTGRES_HOST=103.253.20.30
POSTGRES_USERNAME=postgres
POSTGRES_PASSWORD=123456aA
POSTGRES_PORT=5441
POSTGRES_DB=robot_mem0

# Milvus
MILVUS_HOST=124.197.21.40
MILVUS_PORT=19530
MILVUS_COLLECTION_NAME=user_facts

# Redis
REDIS_HOST=103.253.20.30
REDIS_PASSWORD=yourStrongPassword
REDIS_PORT=30004

# Neo4j
NEO4J_URI=bolt://124.197.21.40:8687
NEO4J_USER=neo4j
NEO4J_PASSWORD=mem0graph

# Mem0 OSS
MEM0_USE_OSS=true
MEM0_VECTOR_STORE_PROVIDER=milvus
MEM0_LLM_PROVIDER=openai
MEM0_EMBEDDER_PROVIDER=openai
OPENAI_API_KEY=sk-...

# RabbitMQ (optional)
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest
```

## Chạy ứng dụng

### Development mode

```bash
# Chạy API server
python scripts/run_api.py

# Hoặc dùng uvicorn trực tiếp
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production mode

```bash
# Sử dụng gunicorn với uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Chạy tests

```bash
# Chạy tất cả tests
pytest

# Chạy với coverage
pytest --cov=app --cov-report=html

# Chạy specific test file
pytest tests/unit/test_memory_service.py
```

## Database migrations

```bash
# Tạo migration mới
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Troubleshooting

### Lỗi: "No module named 'pymilvus'"

```bash
pip install pymilvus>=2.3.4
```

### Lỗi: "No module named 'mem0ai'"

```bash
pip install mem0ai==1.0.1
```

### Lỗi: "grpcio compilation failed"

Trên Windows, có thể cần cài đặt Visual C++ Build Tools hoặc dùng pre-built wheels:

```bash
pip install --upgrade pip
pip install pymilvus>=2.3.4
```

### Lỗi: "marshmallow version conflict"

```bash
pip install marshmallow>=3.0.0,<4.0.0
```

## Cấu trúc dependencies

Dependencies được quản lý trong `pyproject.toml`:

- **Core dependencies**: Tất cả packages cần thiết để chạy ứng dụng
- **Dev dependencies**: Testing tools (pytest, pytest-cov, etc.)

Xem chi tiết trong `pyproject.toml`.

## Notes

- `requirements.txt` không còn được sử dụng, tất cả dependencies được quản lý trong `pyproject.toml`
- Để cài đặt, luôn dùng `pip install -e .` thay vì `pip install -r requirements.txt`

