# Database Setup Guide

## Tự Động Tạo Bảng

Hệ thống có tính năng **tự động tạo bảng** khi khởi động nếu bảng chưa tồn tại.

### Cấu Hình

Trong file `.env`, bạn có thể bật/tắt tính năng này:

```env
# Auto-create tables on startup (default: true)
AUTO_CREATE_TABLES=true
```

### Cách Hoạt Động

1. Khi ứng dụng khởi động, nếu `AUTO_CREATE_TABLES=true`:
   - Hệ thống sẽ tự động kiểm tra và tạo các bảng nếu chưa tồn tại
   - Sử dụng SQLAlchemy `Base.metadata.create_all()`
   - Chỉ tạo bảng mới, không xóa hoặc sửa bảng đã tồn tại

2. Các bảng được tạo tự động:
   - `users` - Thông tin user metadata
   - `conversations` - Thông tin conversations
   - `facts_metadata` - Metadata của facts

### Tắt Tự Động Tạo Bảng

Nếu bạn muốn quản lý migrations bằng Alembic thay vì auto-create:

```env
AUTO_CREATE_TABLES=false
```

## Khởi Tạo Thủ Công

Nếu bạn tắt `AUTO_CREATE_TABLES`, bạn có thể tạo bảng thủ công bằng script:

```bash
python scripts/init_db.py
```

## Sử Dụng Alembic Migrations (Khuyến Nghị cho Production)

### Setup Alembic

1. Tạo file `alembic.ini`:
```bash
alembic init migrations
```

2. Cấu hình `migrations/env.py` để sử dụng async engine:
```python
from app.infrastructure.db.session import engine
from app.infrastructure.db.models import Base

target_metadata = Base.metadata
```

3. Tạo migration đầu tiên:
```bash
alembic revision --autogenerate -m "Initial migration"
```

4. Chạy migrations:
```bash
alembic upgrade head
```

### Lợi Ích của Alembic

- ✅ Quản lý version migrations
- ✅ Rollback migrations
- ✅ Track thay đổi schema
- ✅ Phù hợp cho production
- ✅ Team collaboration

## Models

Các models được định nghĩa trong `app/infrastructure/db/models.py`:

### UserModel
- `id` (String, Primary Key)
- `created_at`, `updated_at`
- `total_conversations`, `total_facts`
- `metadata` (JSON)

### ConversationModel
- `id` (String, Primary Key)
- `user_id` (String, Indexed)
- `created_at`
- `message_count`, `facts_extracted`
- `raw_conversation` (JSON)
- `metadata` (JSON)

### FactMetadataModel
- `fact_id` (String, Primary Key)
- `user_id` (String, Indexed)
- `conversation_id` (String, Indexed)
- `content` (Text)
- `category` (String, Indexed)
- `confidence` (Float)
- `milvus_id` (BigInteger)
- `created_at` (DateTime, Indexed)
- `accessed_count`, `last_accessed_at`
- `metadata` (JSON)

## Troubleshooting

### Lỗi: "relation already exists"

Nếu bảng đã tồn tại, `create_all()` sẽ không tạo lại. Đây là hành vi bình thường.

### Lỗi: "permission denied"

Đảm bảo database user có quyền CREATE TABLE:
```sql
GRANT CREATE ON DATABASE pika_mem0 TO postgres;
```

### Lỗi: "connection refused"

Kiểm tra:
1. PostgreSQL đang chạy
2. Connection settings trong `.env` đúng
3. Firewall không block port 5432

## Best Practices

1. **Development**: Dùng `AUTO_CREATE_TABLES=true` để tiện lợi
2. **Production**: Dùng Alembic migrations để quản lý schema changes
3. **Testing**: Tạo test database riêng với `AUTO_CREATE_TABLES=true`

## Milvus Vector Database

### Tự Động Tạo Collection

Milvus **tự động tạo collection** (tương đương "bảng" trong vector database) khi kết nối.

#### Cách Hoạt Động

1. Khi `milvus_client.connect()` được gọi trong startup:
   - Tự động gọi `_ensure_collection()`
   - Kiểm tra xem collection có tồn tại không
   - Nếu chưa tồn tại, tự động tạo collection với schema và index

2. Collection được tạo với:
   - **Schema** đầy đủ các fields
   - **Index** trên embedding field (IVF_FLAT với IP metric)

#### Collection Schema

Collection `user_facts` (tên từ `MILVUS_COLLECTION_NAME`) có các fields:

- `id` (VARCHAR, Primary Key, max_length=100)
- `fact_id` (VARCHAR, max_length=100)
- `user_id` (VARCHAR, max_length=100)
- `content` (VARCHAR, max_length=2000)
- `category` (VARCHAR, max_length=50)
- `embedding` (FLOAT_VECTOR, dim=1536) - **Indexed với IVF_FLAT**
- `confidence` (FLOAT)
- `created_at` (INT64) - Unix timestamp

#### Index Configuration

- **Index Type**: IVF_FLAT
- **Metric Type**: IP (Inner Product - cosine similarity)
- **Parameters**: nlist=1024

#### Cấu Hình

Collection name được cấu hình trong `.env`:
```env
MILVUS_COLLECTION_NAME=user_facts
```

### Troubleshooting Milvus

#### Lỗi: "Collection already exists"
- Đây là hành vi bình thường
- Code sử dụng `utility.has_collection()` để kiểm tra trước khi tạo
- Nếu collection đã tồn tại, chỉ load collection hiện có

#### Lỗi: "Connection refused"
Kiểm tra:
1. Milvus server đang chạy
2. Connection settings trong `.env` đúng:
   - `MILVUS_HOST` (default: localhost)
   - `MILVUS_PORT` (default: 19530)
3. Firewall không block port

#### Lỗi: "Dimension mismatch"
- Embedding dimension phải là 1536 (cho OpenAI text-embedding-3-small)
- Nếu thay đổi embedding model, cần tạo collection mới với dimension mới

#### Xóa và Tạo Lại Collection

Nếu cần tạo lại collection (ví dụ: thay đổi schema):

```python
from app.infrastructure.search.milvus_client import milvus_client
from pymilvus import utility

# Xóa collection cũ
if utility.has_collection("user_facts"):
    utility.drop_collection("user_facts")

# Kết nối lại để tự động tạo collection mới
await milvus_client.connect()
```

## Neo4j Graph Database

### Tự Động Tạo Constraints và Indexes

Neo4j **không có "bảng"** như SQL database. Thay vào đó, nó sử dụng:
- **Nodes** (nút) - được tạo động khi cần
- **Relationships** (mối quan hệ) - kết nối giữa các nodes
- **Constraints** - đảm bảo tính duy nhất của properties
- **Indexes** - tăng tốc query

Hệ thống **tự động tạo constraints và indexes** khi kết nối Neo4j:

#### Constraints (Tự động tạo khi connect)
- `user_id_unique` - Đảm bảo `User.id` là duy nhất
- `fact_id_unique` - Đảm bảo `Fact.id` là duy nhất  
- `conversation_id_unique` - Đảm bảo `Conversation.id` là duy nhất

#### Indexes (Tự động tạo khi connect)
- `user_created_at_idx` - Index cho `User.created_at`
- `fact_category_idx` - Index cho `Fact.category`
- `fact_created_at_idx` - Index cho `Fact.created_at`
- `fact_user_id_idx` - Index cho `Fact.user_id`

### Cách Hoạt Động

1. Khi `neo4j_client.connect()` được gọi trong startup:
   - Tự động gọi `_ensure_constraints()`
   - Tạo constraints và indexes nếu chưa tồn tại
   - Sử dụng `IF NOT EXISTS` để tránh lỗi nếu đã tồn tại

2. Nodes được tạo động:
   - `User` nodes - khi gọi `create_user_if_not_exists()`
   - `Fact` nodes - khi gọi `create_fact_node()`
   - `Conversation` nodes - khi cần (chưa implement)

3. Relationships được tạo động:
   - `HAS_FACT` - User → Fact
   - `RELATED_TO` - Fact → Fact

### Node Types và Properties

#### User Node
```cypher
(:User {
  id: String (UNIQUE),
  created_at: DateTime
})
```

#### Fact Node
```cypher
(:Fact {
  id: String (UNIQUE),
  content: String,
  category: String,
  confidence: Float,
  created_at: DateTime,
  user_id: String (INDEXED)
})
```

#### Relationships
```cypher
(User)-[:HAS_FACT]->(Fact)
(Fact)-[:RELATED_TO]->(Fact)
```

### Khởi Tạo Thủ Công (Nếu Cần)

Nếu bạn muốn tạo constraints/indexes thủ công:

```python
from app.infrastructure.external.neo4j_client import neo4j_client

await neo4j_client.connect()  # Tự động tạo constraints/indexes
```

Hoặc chạy Cypher trực tiếp trong Neo4j Browser:
```cypher
CREATE CONSTRAINT user_id_unique IF NOT EXISTS 
FOR (u:User) REQUIRE u.id IS UNIQUE;

CREATE INDEX fact_category_idx IF NOT EXISTS 
FOR (f:Fact) ON (f.category);
```

### Troubleshooting Neo4j

#### Lỗi: "Constraint already exists"
- Đây là hành vi bình thường
- Constraints/indexes chỉ được tạo một lần
- Code sử dụng `IF NOT EXISTS` để tránh lỗi

#### Lỗi: "Permission denied"
Đảm bảo Neo4j user có quyền tạo constraints:
```cypher
// Trong Neo4j Browser, chạy với admin user
GRANT CREATE CONSTRAINT ON DATABASE neo4j TO user;
```

#### Lỗi: "Connection refused"
Kiểm tra:
1. Neo4j đang chạy
2. Connection settings trong `.env` đúng
3. Firewall không block port 7687 (Bolt) hoặc 7474 (HTTP)

## Xem Thêm

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)

