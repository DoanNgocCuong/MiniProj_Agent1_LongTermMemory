# PIKA Memory System - Project Structure

## 📁 Structure Overview

Dự án sử dụng **Domain-Driven Design (DDD)** structure theo Decision Template.

```
app/
├── main.py                        # FastAPI app entry point
├── core/                          # Configuration & cross-cutting concerns
├── api/                           # Presentation layer (HTTP/REST)
├── domains/                       # Domain layer (DDD bounded contexts)
│   └── memory/                    # Memory domain
│       ├── domain/                # Entities, Value Objects, Events
│       ├── application/           # Services, Use Cases, Repository interfaces
│       └── infrastructure/        # Concrete implementations
├── infrastructure/                # Technical infrastructure
├── middleware/                    # HTTP middleware
├── security/                      # Security utilities
├── resilience/                    # Resilience patterns
└── utils/                         # Utility functions
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env với các giá trị thực tế
# - POSTGRES_* settings
# - MILVUS_HOST, MILVUS_PORT
# - NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
# - REDIS_HOST, REDIS_PORT
# - OPENAI_API_KEY
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Application

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Access API Docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📋 Next Steps

1. ✅ Structure đã được tạo
2. ⏳ Implement domain entities (complete)
3. ⏳ Implement repositories (Milvus, Neo4j, PostgreSQL)
4. ⏳ Implement services (FactExtractor, FactSearcher)
5. ⏳ Implement API endpoints (complete skeleton)
6. ⏳ Add middleware (error handling, logging, auth)
7. ⏳ Add security (encryption, validation)
8. ⏳ Add resilience (circuit breaker, retry)

## 📚 Documentation

- [SDD Document](./docs/CKP/NewSDD.md)
- [Optimization Guide](./docs/CKP/NewSDD_about_Optimization.md)
- [Structure Decision](./docs/CKP/Structure_Decision_Analysis.md)

## 🏗️ Architecture Principles

- **Domain-Driven Design**: Clear separation between domain, application, and infrastructure
- **Repository Pattern**: Abstract data access through interfaces
- **Dependency Injection**: Services injected via FastAPI Depends
- **SOLID Principles**: Single responsibility, dependency inversion
- **Clean Architecture**: Layers: API → Application → Domain ← Infrastructure


