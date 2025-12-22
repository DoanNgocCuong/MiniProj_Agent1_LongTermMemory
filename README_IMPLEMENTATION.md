# PIKA Memory System - Implementation Guide

## Tổng quan

Dự án đã được refactor hoàn toàn sang Clean Architecture với caching 5 lớp và async job processing.

## Cấu trúc dự án

```
app/
├── core/                    # Configuration, logging, exceptions
├── api/                     # FastAPI endpoints và schemas
├── domains/                 # Domain layer (DDD)
│   └── memory/
│       ├── domain/          # Entities, Value Objects
│       ├── application/     # Services, Repository interfaces
│       └── infrastructure/  # Repository implementations, ORM models
├── infrastructure/          # Technical infrastructure
│   ├── cache/              # Caching layers (L0-L4)
│   ├── database/           # PostgreSQL session
│   ├── messaging/           # RabbitMQ service
│   └── mem0/               # Mem0 client wrapper
├── middleware/             # HTTP middleware
├── resilience/             # Circuit breaker, retry logic
└── utils/                  # Utility functions

workers/
├── tasks/                  # Background worker tasks
│   ├── extraction_task.py
│   └── proactive_cache_task.py
└── main.py                 # Worker entry point
```

## Cài đặt

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình environment variables

Tạo file `.env` từ `.env.example` và điền các giá trị:

```env
# Database
POSTGRES_USER=pika_user
POSTGRES_PASSWORD=pika_password
POSTGRES_DB=pika_memory
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest

# Mem0
MEM0_API_KEY=your_mem0_api_key

# OpenAI (optional)
OPENAI_API_KEY=your_openai_api_key
```

### 3. Khởi tạo database

```bash
# Chạy migrations
alembic upgrade head

# Hoặc tạo tables thủ công
python scripts/init_db.py
```

## Chạy ứng dụng

### API Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API sẽ chạy tại: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Worker

```bash
python -m workers.main
```

Worker sẽ:
- Consume extraction jobs từ RabbitMQ
- Chạy proactive caching scheduler (mỗi 30 phút)

## API Endpoints

### POST /api/v1/search_facts

Tìm kiếm memories/facts.

**Request:**
```json
{
  "user_id": "user_123",
  "query": "What do I like?",
  "limit": 10,
  "score_threshold": 0.4
}
```

**Response:**
```json
{
  "status": "ok",
  "count": 2,
  "facts": [
    {
      "id": "mem_001",
      "score": 0.95,
      "fact_value": "I like pizza",
      "metadata": {}
    }
  ]
}
```

### POST /api/v1/extract_facts

Extract facts từ conversation (async).

**Request:**
```json
{
  "user_id": "user_123",
  "conversation_id": "conv_001",
  "conversation": [
    {"role": "user", "content": "I like pizza"}
  ],
  "metadata": {}
}
```

**Response (202 Accepted):**
```json
{
  "status": "accepted",
  "job_id": "job_550e8400-...",
  "status_url": "/api/v1/jobs/job_550e8400-.../status"
}
```

### GET /api/v1/jobs/{job_id}/status

Lấy trạng thái của extraction job.

**Response:**
```json
{
  "job_id": "job_550e8400-...",
  "status": "completed",
  "progress": 100,
  "current_step": "Completed",
  "data": {
    "facts_extracted": 2
  }
}
```

## Caching Strategy

Hệ thống sử dụng 5 lớp cache:

1. **L0: Session Cache** - In-memory, request lifetime
2. **L1: Redis Cache** - Distributed cache, 1 hour TTL
3. **L2: Materialized View** - PostgreSQL, pre-computed user favorites
4. **L3: Embedding Cache** - Redis, caches query embeddings (24h TTL)
5. **L4: Vector Search** - Mem0 fallback khi tất cả cache miss

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_memory_service.py
```

## Migration từ code cũ

Code cũ trong `src/` vẫn được giữ lại để đảm bảo backward compatibility. Để migrate:

1. Test API mới song song với API cũ
2. Route một phần traffic đến version mới
3. Monitor metrics và error rates
4. Cutover 100% traffic khi stable

## Troubleshooting

### Lỗi kết nối database
- Kiểm tra PostgreSQL đang chạy
- Kiểm tra credentials trong `.env`

### Lỗi kết nối Redis
- Kiểm tra Redis đang chạy
- Kiểm tra `REDIS_HOST` và `REDIS_PORT`

### Lỗi RabbitMQ
- Kiểm tra RabbitMQ đang chạy
- Kiểm tra credentials trong `.env`

### Lỗi Mem0 API
- Kiểm tra `MEM0_API_KEY` trong `.env`
- Kiểm tra network connectivity

## Performance Optimization

Hệ thống đã được optimize với:
- Connection pooling cho database và Redis
- Async parallelism trong services
- Multi-layer caching để giảm latency
- Proactive caching cho queries thường xuyên

Mục tiêu: P95 latency < 200ms cho search_facts API.

