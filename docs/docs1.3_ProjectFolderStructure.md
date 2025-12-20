# New Folder Structure

```bash

your_project/

│

├── 📦 app/                                    # Main Application

│   ├── __init__.py

│   ├── main.py                               # FastAPI app creation, lifespan events

│   │

│   ├── 🔌 api/                               # PRESENTATION LAYER (HTTP/REST/GraphQL)

│   │   ├── __init__.py

│   │   ├── dependencies.py                   # Shared dependency injection (Depends)

│   │   ├── middleware/                       # HTTP middleware

│   │   │   ├── __init__.py

│   │   │   ├── error_handler.py              # Global error handling (try/except wrapper)

│   │   │   ├── request_logger.py             # Request/response logging with structlog

│   │   │   ├── correlation_id.py             # Distributed tracing (trace_id, span_id)

│   │   │   ├── auth_middleware.py            # JWT validation, user context injection

│   │   │   └── performance_monitor.py        # Request latency tracking

│   │   │

│   │   └── v1/                               # API versioning (v1, v2 in future)

│   │       ├── __init__.py

│   │       ├── router.py                     # Main router aggregator

│   │       │                                 # APIRouter("/v1").include_router(auth_router)...

│   │       │

│   │       ├── endpoints/                    # Feature-specific endpoint groups

│   │       │   ├── __init__.py

│   │       │   ├── auth.py                   # POST /login, /refresh, /logout

│   │       │   ├── users.py                  # GET /users, POST /users, PATCH /users/{id}

│   │       │   ├── products.py               # GET /products, POST /products (search, filter)

│   │       │   ├── orders.py                 # POST /orders, GET /orders/{id}, PATCH /orders/{id}/status

│   │       │   ├── payments.py               # POST /payments/webhook, GET /payments/{id}

│   │       │   └── health.py                 # GET /health (Kubernetes readiness/liveness)

│   │       │

│   │       └── schemas/                      # Request/Response Pydantic models (per endpoint)

│   │           ├── __init__.py

│   │           ├── auth.py                   # LoginRequest, LoginResponse, TokenPayload

│   │           ├── user.py                   # UserCreate, UserUpdate, UserResponse

│   │           ├── product.py                # ProductCreate, ProductResponse

│   │           └── order.py                  # OrderCreate, OrderResponse

│   │

│   ├── ⚙️ core/                              # CONFIGURATION & CROSS-CUTTING CONCERNS

│   │   ├── __init__.py

│   │   ├── config.py                         # Pydantic BaseSettings + environment vars

│   │   │                                     # class Settings: db_url, redis_url, jwt_secret, etc.

│   │   │

│   │   ├── constants.py                      # App-wide constants, enums

│   │   │                                     # enum UserRole: ADMIN, USER, GUEST

│   │   │                                     # MAX_PAGE_SIZE = 100

│   │   │

│   │   ├── exceptions.py                     # Custom exceptions (domain-agnostic)

│   │   │                                     # class AppException(Exception): ...

│   │   │                                     # class ValidationError: ...

│   │   │

│   │   ├── security.py                       # Security utilities

│   │   │   ├── jwt_handler.py                # create_token(), verify_token()

│   │   │   ├── password.py                   # hash_password(), verify_password()

│   │   │   └── cors.py                       # CORS configuration

│   │   │

│   │   ├── logging.py                        # Structured logging setup

│   │   │                                     # logger = setup_logging() → JSON format for ELK

│   │   │

│   │   ├── telemetry.py                      # OpenTelemetry setup

│   │   │                                     # trace_provider, metric_provider setup

│   │   │

│   │   └── enums.py                          # Reusable enums

│   │                                         # class OrderStatus: PENDING, PAID, SHIPPED

│   │

│   ├── 🏢 domains/                           # DOMAIN LAYER (DDD BOUNDED CONTEXTS)

│   │   ├── __init__.py

│   │   │

│   │   ├── users/                            # ===== USER MANAGEMENT BOUNDED CONTEXT =====

│   │   │   ├── __init__.py

│   │   │   │

│   │   │   ├── domain/                       # DOMAIN LOGIC (Entities, Value Objects, Events)

│   │   │   │   ├── __init__.py

│   │   │   │   ├── entities.py               # User entity: email, password_hash, status

│   │   │   │   │                             # class User: aggregate root

│   │   │   │   ├── value_objects.py          # Email, PhoneNumber, PasswordHash

│   │   │   │   │                             # class Email: validate_email(), __eq__()

│   │   │   │   ├── events.py                 # UserCreated, UserUpdated, UserDeleted

│   │   │   │   │                             # class UserCreatedEvent: user_id, email, timestamp

│   │   │   │   └── exceptions.py             # UserNotFound, EmailAlreadyExists

│   │   │   │

│   │   │   ├── application/                  # APPLICATION LOGIC (Use Cases, Orchestration)

│   │   │   │   ├── __init__.py

│   │   │   │   ├── services/

│   │   │   │   │   ├── user_service.py       # UserService: create_user(), get_user(), update_user()

│   │   │   │   │   └── auth_service.py       # AuthService: login(), logout(), refresh_token()

│   │   │   │   │

│   │   │   │   ├── usecases/                 # (Optional, if using full CQRS)

│   │   │   │   │   ├── create_user.py

│   │   │   │   │   ├── get_user.py

│   │   │   │   │   └── update_user.py

│   │   │   │   │

│   │   │   │   ├── repositories/             # ABSTRACT REPOSITORY INTERFACES

│   │   │   │   │   ├── __init__.py

│   │   │   │   │   ├── base.py               # BaseRepository[T]

│   │   │   │   │   │                         # async def get(id: UUID) -> T

│   │   │   │   │   │                         # async def save(entity: T) -> T

│   │   │   │   │   └── user_repository.py    # IUserRepository: find_by_email(), find_by_id()

│   │   │   │   │

│   │   │   │   ├── dto/                      # Data Transfer Objects (if using CQRS)

│   │   │   │   │   ├── user_dto.py

│   │   │   │   │   └── auth_dto.py

│   │   │   │   │

│   │   │   │   └── commands.py               # (Optional) Command objects for CQRS

│   │   │   │       ├── create_user_cmd.py

│   │   │   │       └── update_user_cmd.py

│   │   │   │

│   │   │   └── infrastructure/               # INFRASTRUCTURE (Concrete Implementations)

│   │   │       ├── __init__.py

│   │   │       ├── models.py                 # SQLAlchemy ORM model: User

│   │   │       ├── schemas.py                # Pydantic schemas: UserCreate, UserResponse

│   │   │       ├── repositories/

│   │   │       │   ├── __init__.py

│   │   │       │   └── user_repository_impl.py  # Concrete UserRepository implementation

│   │   │       │

│   │   │       ├── mappers.py                # Map ORM ↔ Domain Entity

│   │   │       │                             # class UserMapper: orm_to_entity(), entity_to_orm()

│   │   │       │

│   │   │       └── event_handlers.py         # Event subscribers for UserCreated, UserDeleted

│   │   │                                     # send welcome email, update analytics

│   │   │

│   │   ├── products/                         # ===== PRODUCT CATALOG BOUNDED CONTEXT =====

│   │   │   ├── domain/

│   │   │   │   ├── entities.py

│   │   │   │   ├── value_objects.py          # Money, Sku, Category

│   │   │   │   ├── events.py                 # ProductCreated, InventoryUpdated

│   │   │   │   └── exceptions.py

│   │   │   │

│   │   │   ├── application/

│   │   │   │   ├── services/

│   │   │   │   │   ├── product_service.py

│   │   │   │   │   └── inventory_service.py

│   │   │   │   └── repositories/

│   │   │   │       └── product_repository.py

│   │   │   │

│   │   │   └── infrastructure/

│   │   │       ├── models.py                 # Product, Inventory ORM

│   │   │       ├── repositories/

│   │   │       │   └── product_repository_impl.py

│   │   │       └── event_handlers.py         # Handle product events

│   │   │

│   │   ├── orders/                           # ===== ORDER MANAGEMENT BOUNDED CONTEXT =====

│   │   │   ├── domain/

│   │   │   │   ├── entities.py               # Order (aggregate root), OrderItem

│   │   │   │   ├── value_objects.py          # OrderStatus, Address, Currency

│   │   │   │   ├── events.py                 # OrderCreated, PaymentProcessed, OrderShipped

│   │   │   │   └── exceptions.py             # OrderNotFound, InvalidOrderStatus

│   │   │   │

│   │   │   ├── application/

│   │   │   │   ├── services/

│   │   │   │   │   └── order_service.py      # Create, update, cancel order

│   │   │   │   │

│   │   │   │   └── repositories/

│   │   │   │       ├── order_repository.py   # Abstract

│   │   │   │       └── order_item_repository.py

│   │   │   │

│   │   │   └── infrastructure/

│   │   │       ├── models.py                 # Order, OrderItem ORM

│   │   │       ├── repositories/

│   │   │       │   └── order_repository_impl.py

│   │   │       │

│   │   │       └── event_handlers.py         # OrderCreated → trigger payment service

│   │   │                                     # PaymentSuccess → update order status

│   │   │

│   │   ├── payments/                         # ===== PAYMENT PROCESSING BOUNDED CONTEXT =====

│   │   │   ├── domain/

│   │   │   │   ├── entities.py               # Payment (aggregate root)

│   │   │   │   ├── value_objects.py          # PaymentStatus, Money, TransactionId

│   │   │   │   ├── events.py                 # PaymentInitiated, PaymentSuccess, PaymentFailed

│   │   │   │   └── exceptions.py

│   │   │   │

│   │   │   ├── application/

│   │   │   │   ├── services/

│   │   │   │   │   └── payment_service.py    # Process payment, handle webhooks

│   │   │   │   │

│   │   │   │   └── repositories/

│   │   │   │       └── payment_repository.py

│   │   │   │

│   │   │   └── infrastructure/

│   │   │       ├── models.py

│   │   │       ├── repositories/

│   │   │       │   └── payment_repository_impl.py

│   │   │       │

│   │   │       └── stripe_adapter.py         # Stripe API integration

│   │   │

│   │   └── shared/                           # ===== SHARED DOMAIN LOGIC =====

│   │       ├── __init__.py

│   │       ├── events.py                     # Base Event class, EventPublisher

│   │       │                                 # class Event: domain, event_type, timestamp, data

│   │       │

│   │       ├── specifications.py             # Query specifications (DDD)

│   │       │                                 # class Specification: to_predicate()

│   │       │

│   │       └── value_objects.py              # Shared VO: Id, AuditFields

│   │                                         # class EntityId(ValueObject): id, created_at, updated_by

│   │

│   ├── 🔌 infrastructure/                    # INFRASTRUCTURE LAYER (Technical Details)

│   │   ├── __init__.py

│   │   │

│   │   ├── db/                               # DATABASE

│   │   │   ├── __init__.py

│   │   │   ├── session.py                    # SQLAlchemy session factory + context manager

│   │   │   │                                 # async def get_session() → AsyncSession

│   │   │   │

│   │   │   ├── base.py                       # Base model with common fields

│   │   │   │                                 # class BaseModel: id, created_at, updated_at, deleted_at

│   │   │   │

│   │   │   ├── connection.py                 # DB connection pool setup

│   │   │   │

│   │   │   └── transactions.py               # Transaction management

│   │   │                                     # async with transaction(): ...

│   │   │

│   │   ├── cache/                            # CACHING (Redis)

│   │   │   ├── __init__.py

│   │   │   ├── client.py                     # Redis client wrapper

│   │   │   │                                 # async def get(key), async def set(key, value, ttl)

│   │   │   │

│   │   │   ├── keys.py                       # Cache key generation constants

│   │   │   │                                 # USER_CACHE_KEY = "user:{user_id}"

│   │   │   │

│   │   │   ├── ttl.py                        # TTL constants by entity

│   │   │   │                                 # USER_TTL = 3600, PRODUCT_TTL = 7200

│   │   │   │

│   │   │   └── decorators.py                 # @cache_result(ttl=3600)

│   │   │

│   │   ├── messaging/                        # MESSAGE QUEUE & EVENTS (Kafka/RabbitMQ)

│   │   │   ├── __init__.py

│   │   │   ├── broker.py                     # Kafka/RabbitMQ client setup

│   │   │   │                                 # class MessageBroker: publish(), consume()

│   │   │   │

│   │   │   ├── celery_app.py                 # Celery configuration

│   │   │   │                                 # @app.task async def send_email(user_id)

│   │   │   │

│   │   │   ├── publishers/                   # Event publishers per domain

│   │   │   │   ├── __init__.py

│   │   │   │   ├── user_events.py

│   │   │   │   ├── order_events.py

│   │   │   │   └── payment_events.py

│   │   │   │

│   │   │   ├── consumers/                    # Event subscribers

│   │   │   │   ├── __init__.py

│   │   │   │   ├── order_consumer.py         # Handle OrderCreated → trigger payment

│   │   │   │   ├── payment_consumer.py       # Handle PaymentSuccess → update order status

│   │   │   │   └── user_consumer.py          # Handle UserCreated → send welcome email

│   │   │   │

│   │   │   └── schemas.py                    # Kafka message schemas (JSON serialization)

│   │   │

│   │   ├── storage/                          # FILE STORAGE (S3, GCS, Local)

│   │   │   ├── __init__.py

│   │   │   ├── base.py                       # Abstract storage interface

│   │   │   │                                 # class StorageProvider: upload(), download(), delete()

│   │   │   │

│   │   │   ├── s3_client.py                  # AWS S3 implementation

│   │   │   │                                 # class S3Storage(StorageProvider): ...

│   │   │   │

│   │   │   ├── local_storage.py              # Local filesystem (dev/test)

│   │   │   │

│   │   │   └── gcs_client.py                 # Google Cloud Storage (optional)

│   │   │

│   │   ├── external/                         # EXTERNAL API CLIENTS (3rd Party)

│   │   │   ├── __init__.py

│   │   │   ├── base_client.py                # Base HTTP client with retry, circuit breaker

│   │   │   │                                 # class BaseApiClient: _request(), _retry_with_backoff()

│   │   │   │

│   │   │   ├── stripe_client.py              # Stripe payment processor

│   │   │   │                                 # class StripeClient: create_payment(), refund()

│   │   │   │

│   │   │   ├── email_client.py               # SendGrid email service

│   │   │   │                                 # class EmailClient: send_email(), send_batch()

│   │   │   │

│   │   │   ├── llm_client.py                 # OpenAI / LLM API

│   │   │   │                                 # class LLMClient: generate_summary(), classify()

│   │   │   │

│   │   │   └── analytics_client.py           # Analytics (Google Analytics, Mixpanel)

│   │   │

│   │   ├── search/                           # SEARCH & ANALYTICS

│   │   │   ├── __init__.py

│   │   │   ├── elasticsearch.py              # Elasticsearch client

│   │   │   │                                 # async def index_product(), async def search()

│   │   │   │

│   │   │   └── milvus_client.py              # Vector search (embeddings)

│   │   │                                     # For AI/ML features

│   │   │

│   │   └── repositories/                     # CONCRETE REPOSITORY IMPLEMENTATIONS

│   │       ├── __init__.py

│   │       ├── base_repository.py            # Generic CRUD: get(), create(), update(), delete()

│   │       │

│   │       ├── user_repository.py            # Extends BaseRepository, implements IUserRepository

│   │       ├── product_repository.py         # Extends BaseRepository

│   │       ├── order_repository.py           # Extends BaseRepository

│   │       └── payment_repository.py         # Extends BaseRepository

│   │

│   ├── 🛡️ middleware/                        # HTTP MIDDLEWARE (Cross-cutting)

│   │   ├── __init__.py

│   │   ├── error_handler.py                  # Global exception handling

│   │   │                                     # @app.exception_handler(Exception)

│   │   │

│   │   ├── request_logger.py                 # Log all requests/responses

│   │   │                                     # Structured JSON logging

│   │   │

│   │   ├── correlation_id.py                 # Distributed tracing

│   │   │                                     # x-request-id, x-trace-id headers

│   │   │

│   │   ├── auth.py                           # JWT authentication

│   │   │                                     # async def verify_token(token: str)

│   │   │

│   │   └── rate_limiter.py                   # Rate limiting (per user, per endpoint)

│   │

│   ├── 🔒 security/                          # SECURITY UTILITIES

│   │   ├── __init__.py

│   │   ├── jwt_handler.py                    # JWT create/verify

│   │   │                                     # encode_token(), decode_token()

│   │   │

│   │   ├── password.py                       # Password hashing

│   │   │                                     # hash_password() → bcrypt, verify_password()

│   │   │

│   │   ├── cors.py                           # CORS configuration

│   │   │                                     # CORSMiddleware setup

│   │   │

│   │   ├── permissions.py                    # RBAC (Role-Based Access Control)

│   │   │                                     # async def check_permission(user, resource, action)

│   │   │

│   │   └── encryption.py                     # Encryption at rest

│   │                                         # encrypt_field(), decrypt_field()

│   │

│   ├── 🛡️ resilience/                        # RESILIENCE PATTERNS

│   │   ├── __init__.py

│   │   ├── circuit_breaker.py                # Circuit breaker (prevent cascading failures)

│   │   │                                     # @circuit_breaker(failure_threshold=5)

│   │   │

│   │   ├── retry.py                          # Retry logic with exponential backoff

│   │   │                                     # @retry(max_attempts=3, backoff=2)

│   │   │

│   │   ├── timeout.py                        # Timeout management

│   │   │                                     # @with_timeout(seconds=5)

│   │   │

│   │   └── bulkhead.py                       # Resource isolation

│   │                                         # Limit concurrent requests per resource

│   │

│   └── 🛠️ utils/                             # UTILITIES & HELPERS

│       ├── __init__.py

│       ├── date_utils.py                     # Date/time helpers

│       │                                     # to_utc(), parse_iso8601(), age_from_dob()

│       │

│       ├── string_utils.py                   # String manipulation

│       │                                     # slugify(), camel_to_snake(), truncate()

│       │

│       ├── pagination.py                     # Pagination logic

│       │                                     # class PaginationParams: limit, offset

│       │

│       ├── validators.py                     # Custom validators

│       │                                     # validate_email(), validate_phone()

│       │

│       ├── decorators.py                     # Reusable decorators

│       │                                     # @retry, @cache, @log_time, @require_auth

│       │

│       ├── converters.py                     # Type converters

│       │                                     # str_to_uuid(), dict_to_model()

│       │

│       └── file_utils.py                     # File operations

│                                             # generate_unique_filename(), safe_path()

│

├── 🧪 tests/                                 # TEST SUITE (Mirror domain structure)

│   ├── __init__.py

│   ├── conftest.py                           # Pytest fixtures + setup

│   │                                         # @pytest.fixture: async_client, db_session, redis

│   │

│   ├── factories/                            # Factory Boy for test data generation

│   │   ├── __init__.py

│   │   ├── user_factory.py

│   │   ├── product_factory.py

│   │   ├── order_factory.py

│   │   └── payment_factory.py

│   │

│   ├── fixtures/                             # Reusable test fixtures

│   │   ├── __init__.py

│   │   ├── auth_fixtures.py                  # JWT tokens, auth contexts

│   │   ├── db_fixtures.py                    # Database setup/teardown

│   │   └── mocking_fixtures.py               # Mock external services

│   │

│   ├── unit/                                 # UNIT TESTS (Business logic in isolation)

│   │   ├── __init__.py

│   │   ├── domains/

│   │   │   ├── test_user_service.py          # Test UserService.create_user()

│   │   │   ├── test_order_service.py         # Test OrderService.create_order()

│   │   │   ├── test_payment_service.py       # Test PaymentService.process_payment()

│   │   │   └── test_product_service.py

│   │   │

│   │   ├── utils/

│   │   │   ├── test_validators.py

│   │   │   ├── test_pagination.py

│   │   │   └── test_date_utils.py

│   │   │

│   │   └── security/

│   │       ├── test_jwt.py

│   │       └── test_password.py

│   │

│   ├── integration/                          # INTEGRATION TESTS (Service + Repository + DB)

│   │   ├── __init__.py

│   │   ├── test_user_creation.py             # UserService → UserRepository → PostgreSQL

│   │   ├── test_order_flow.py                # OrderService → OrderRepository, PaymentService

│   │   ├── test_payment_processing.py        # PaymentService → Stripe API (mocked)

│   │   └── test_product_search.py            # ProductService → Elasticsearch

│   │

│   ├── api/                                  # API ENDPOINT TESTS (HTTP contract)

│   │   ├── __init__.py

│   │   ├── test_auth.py                      # POST /v1/auth/login, POST /v1/auth/refresh

│   │   ├── test_users.py                     # GET /v1/users, POST /v1/users, PATCH /v1/users/{id}

│   │   ├── test_products.py                  # GET /v1/products, POST /v1/products

│   │   ├── test_orders.py                    # POST /v1/orders, GET /v1/orders/{id}

│   │   └── test_payments.py                  # POST /v1/payments/webhook

│   │

│   ├── e2e/                                  # END-TO-END TESTS (Full user journeys)

│   │   ├── __init__.py

│   │   ├── test_user_signup.py               # Sign up → Login → Create order

│   │   ├── test_complete_checkout.py         # Browse → Add to cart → Checkout → Payment

│   │   └── test_payment_webhook.py           # Webhook handling, event processing

│   │

│   └── load/                                 # LOAD & PERFORMANCE TESTS

│       ├── __init__.py

│       ├── locustfile.py                     # Locust load test scenarios

│       └── k6_scenarios.js                   # K6 performance test scripts

│

├── 📚 docs/                                  # DOCUMENTATION

│   ├── __init__.py

│   ├── README.md                             # Project overview, quick start

│   │

│   ├── ARCHITECTURE.md                       # HLD (High-Level Design)

│   │                                         # Chapter 5 from your SDD template

│   │                                         # System overview, C4 diagrams, tech stack

│   │

│   ├── DEVELOPMENT.md                        # Local development setup

│   │                                         # Prerequisites, env setup, running locally

│   │

│   ├── API.md                                # API documentation

│   │                                         # Link to Swagger UI, authentication

│   │

│   ├── DEPLOYMENT.md                         # Production deployment guide

│   │                                         # K8s setup, monitoring, scaling

│   │

│   ├── RUNBOOK.md                            # Operational runbook

│   │                                         # Incident response, common issues

│   │

│   ├── ADR/                                  # Architecture Decision Records

│   │   ├── ADR-001-db-choice.md              # Why PostgreSQL vs MongoDB

│   │   ├── ADR-002-event-driven.md           # Why Kafka/RabbitMQ for async

│   │   ├── ADR-003-ddd-structure.md          # Why DDD bounded contexts

│   │   └── ADR-004-api-versioning.md         # API versioning strategy

│   │

│   ├── CONTRIBUTING.md                       # How to contribute

│   │                                         # Code style, PR process, testing requirements

│   │

│   ├── CHANGELOG.md                          # Version history

│   │                                         # v1.0.0 released, breaking changes, new features

│   │

│   ├── SECURITY.md                           # Security guidelines

│   │                                         # Vulnerability disclosure, best practices

│   │

│   └── GLOSSARY.md                           # Domain terminology

│                                             # User, Order, Payment, Product definitions

│

├── 📊 migrations/                            # DATABASE MIGRATIONS (Alembic)

│   ├── __init__.py

│   ├── env.py                                # Alembic environment setup

│   ├── script.py.mako                        # Migration template

│   │

│   └── versions/                             # Migration history

│       ├── 001_initial_schema.py             # create users, products, orders tables

│       ├── 002_add_audit_fields.py           # add created_at, updated_at, deleted_at

│       ├── 003_add_payment_table.py

│       └── ...

│

├── 🐳 docker/                                # DOCKER & CONTAINERIZATION

│   ├── Dockerfile                            # Production image

│   │                                         # Multi-stage build: builder → runtime

│   │

│   ├── Dockerfile.dev                        # Development image

│   │                                         # Includes dev tools, debugger

│   │

│   ├── docker-compose.yml                    # Local dev environment

│   │                                         # app, postgres, redis, rabbitmq, elasticsearch

│   │

│   ├── docker-compose.prod.yml               # Production-like environment

│   │

│   └── .dockerignore                         # Exclude files from build context

│

├── 🌐 infrastructure/                        # INFRASTRUCTURE AS CODE

│   ├── terraform/                            # Terraform configuration

│   │   ├── main.tf                           # Main resources

│   │   ├── variables.tf                      # Input variables

│   │   ├── outputs.tf                        # Output values

│   │   ├── provider.tf                       # AWS/GCP provider config

│   │   │

│   │   ├── networking/

│   │   │   ├── vpc.tf                        # Virtual Private Cloud

│   │   │   └── security_groups.tf            # Firewall rules

│   │   │

│   │   ├── database/

│   │   │   ├── rds.tf                        # PostgreSQL RDS

│   │   │   └── backup.tf                     # Backup policy

│   │   │

│   │   ├── cache/

│   │   │   └── elasticache.tf                # Redis cluster

│   │   │

│   │   ├── compute/

│   │   │   ├── eks.tf                        # Kubernetes (EKS)

│   │   │   └── ec2.tf                        # EC2 instances

│   │   │

│   │   ├── storage/

│   │   │   ├── s3.tf                         # S3 buckets

│   │   │   └── efs.tf                        # Shared storage

│   │   │

│   │   └── monitoring/

│   │       ├── cloudwatch.tf                 # AWS CloudWatch

│   │       └── alarms.tf                     # Alarms & notifications

│   │

│   └── helm/                                 # Kubernetes Helm charts

│       ├── Chart.yaml                        # Chart metadata

│       ├── values.yaml                       # Default values

│       ├── values-prod.yaml                  # Production overrides

│       ├── values-staging.yaml               # Staging overrides

│       │

│       └── templates/

│           ├── deployment.yaml               # K8s Deployment

│           ├── service.yaml                  # K8s Service

│           ├── configmap.yaml                # Configuration

│           ├── secrets.yaml                  # Secrets (mounted from external source)

│           ├── hpa.yaml                      # Horizontal Pod Autoscaler

│           ├── pdb.yaml                      # Pod Disruption Budget

│           ├── ingress.yaml                  # Ingress controller

│           └── networkpolicy.yaml            # Network policies

│

├── 🔧 .github/                               # CI/CD WORKFLOWS (GitHub Actions)

│   └── workflows/

│       ├── test.yml                          # Run tests on PR

│       │                                     # Unit, integration, E2E tests

│       │

│       ├── lint.yml                          # Code quality checks

│       │                                     # Black, isort, mypy, flake8, pylint

│       │

│       ├── security.yml                      # Security scanning

│       │                                     # Bandit, Safety, Snyk, SAST

│       │

│       ├── build.yml                         # Build & push Docker image

│       │                                     # ECR, Docker Hub

│       │

│       └── deploy.yml                        # Deploy to K8s

│                                             # Staging → Production with canary

│

├── 📋 scripts/                               # UTILITY SCRIPTS

│   ├── __init__.py

│   ├── seed_data.py                          # Load initial/test data

│   │                                         # python scripts/seed_data.py

│   │

│   ├── cleanup.py                            # Cleanup old data

│   │                                         # python scripts/cleanup.py

│   │

│   ├── user_migration.py                     # Data migration scripts

│   │                                         # from_old_db_to_new_db()

│   │

│   ├── performance_audit.py                  # Profiling & optimization

│   │                                         # python -m cProfile

│   │

│   ├── generate_test_data.py                 # Generate load test data

│   │

│   └── db_backup.sh                          # Database backup script

│

├── 📄 Configuration Files (Root)

│   ├── pyproject.toml                        # Modern Python project metadata

│   │                                         # [project], [tool.poetry], [tool.black], etc.

│   │

│   ├── setup.py                              # Setup script (can be minimal)

│   ├── setup.cfg                             # Setup configuration

│   │

│   ├── requirements.txt                      # Production dependencies (pinned)

│   ├── requirements-dev.txt                  # Development dependencies

│   ├── requirements-test.txt                 # Test dependencies

│   │

│   ├── .env.example                          # Environment template

│   ├── .env.test                             # Test environment

│   │

│   ├── .gitignore                            # Git ignore patterns

│   ├── .pre-commit-config.yaml               # Pre-commit hooks

│   │

│   ├── pytest.ini                            # Pytest configuration

│   ├── mypy.ini                              # Type checking config

│   ├── .flake8                               # Flake8 linting rules

│   ├── .pylintrc                             # Pylint configuration

│   ├── .bandit                               # Security scanning config

│   │

│   ├── Makefile                              # Common commands

│   │                                         # make test, make lint, make run, make docker-build

│   │

│   └── docker.env                            # Docker environment variables

│

└── 📄 Root Documentation

    ├── README.md                             # Quick start + project overview

    ├── ROADMAP.md                            # Product & tech roadmap (12-24 months)

    ├── CONTRIBUTING.md                       # Contribution guidelines

    ├── LICENSE                               # License file

    └── CODE_OF_CONDUCT.md                    # Community guidelines

```

Xem thử template folder structure sau và recommend cho
