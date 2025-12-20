# Bug Fix Report: Milvus Connection & Related Issues

**Ngày:** 2024-12-20  
**Tác giả:** AI Assistant  
**Mục đích:** Tài liệu hóa quá trình fix các bugs liên quan đến kết nối Milvus và các services khác

---

## 📋 Tóm Tắt

Quá trình fix bugs kết nối Milvus và các services liên quan gặp nhiều vấn đề phức tạp, từ database schema, Redis authentication, đến Milvus port configuration. Report này ghi lại toàn bộ quá trình troubleshooting và giải pháp cuối cùng.

---

## 🐛 Danh Sách Bugs Đã Fix

### Bug #1: SQLAlchemy Reserved Field Name `metadata`

**Mô tả:**
- Lỗi: `Attribute name 'metadata' is reserved when using the Declarative API`
- Xảy ra khi: App startup, auto-create tables
- Nguyên nhân: Field `metadata` là reserved name trong SQLAlchemy Declarative API

**Giải pháp:**
1. Đổi tên field trong models từ `metadata` → `meta_data`:
   - `UserModel.meta_data`
   - `ConversationModel.meta_data`
   - `FactMetadataModel.meta_data`

2. Cập nhật SQL queries để dùng `meta_data` column:
   ```python
   # app/domains/memory/infrastructure/repositories/fact_repository_impl.py
   INSERT INTO facts_metadata (..., meta_data) VALUES (...)
   SELECT meta_data FROM facts_metadata WHERE ...
   ```

3. Giữ nguyên `metadata` trong Fact entity (domain entity, không phải SQLAlchemy model):
   ```python
   # Mapping: fact.metadata (entity) → meta_data (database column)
   metadata=row.get("meta_data", {})
   ```

**Files đã sửa:**
- `app/infrastructure/db/models.py`
- `app/domains/memory/infrastructure/repositories/fact_repository_impl.py`

**Kết quả:** ✅ Tables tạo thành công, không còn lỗi reserved name

---

### Bug #2: Redis Authentication Required

**Mô tả:**
- Lỗi: `Authentication required` khi kết nối Redis
- Xảy ra khi: App startup, Redis connection
- Nguyên nhân: Redis server yêu cầu password nhưng code không hỗ trợ

**Giải pháp:**
1. Thêm fields vào `app/core/config.py`:
   ```python
   REDIS_PASSWORD: Optional[str] = None
   REDIS_USERNAME: Optional[str] = None  # For Redis 6+ ACL
   ```

2. Cập nhật `redis_url` property để tự động thêm password vào URL:
   ```python
   @property
   def redis_url(self) -> str:
       if self.REDIS_PASSWORD:
           if self.REDIS_USERNAME:
               return f"redis://{self.REDIS_USERNAME}:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
           else:
               return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
       return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
   ```

3. Thêm setting để làm Redis optional:
   ```python
   REDIS_REQUIRED: bool = False  # App vẫn chạy được nếu Redis unavailable
   ```

**Files đã sửa:**
- `app/core/config.py`
- `app/main.py` (thêm try-except cho optional Redis)

**Kết quả:** ✅ Redis kết nối thành công với password từ `.env`

---

### Bug #3: Milvus Connection Failed - Wrong Port

**Mô tả:**
- Lỗi: `Fail connecting to server on 124.197.21.40:8000, illegal connection params or server unavailable`
- Xảy ra khi: App startup, Milvus connection
- Nguyên nhân: Port 8000 không phải port gRPC của Milvus (đó là HTTP API port)

**Quá trình Troubleshooting:**

#### Bước 1: Kiểm tra Network Connectivity
```powershell
Test-NetConnection -ComputerName 124.197.21.40 -Port 8000
# Result: TcpTestSucceeded: True ✅
```

Port 8000 có thể kết nối TCP, nhưng Milvus gRPC không phản hồi.

#### Bước 2: Kiểm tra Port 19530 (Default Milvus gRPC)
```powershell
Test-NetConnection -ComputerName 124.197.21.40 -Port 19530
# Result: TcpTestSucceeded: True ✅
```

Port 19530 cũng có thể kết nối được.

#### Bước 3: Tìm hiểu về Milvus Ports
- **Port 8000**: HTTP API port (cho REST API)
- **Port 19530**: gRPC port (cho pymilvus client) ← **Cần dùng port này!**

#### Bước 4: Fix Port Configuration

1. Cập nhật default port trong `app/core/config.py`:
   ```python
   MILVUS_PORT: int = 19530  # Default Milvus gRPC port (8000 is HTTP API port)
   ```

2. Cập nhật `.env` file:
   ```bash
   MILVUS_PORT=19530  # Thay vì 8000
   ```

3. Cải thiện error handling:
   ```python
   # app/infrastructure/search/milvus_client.py
   try:
       connections.connect(**connect_params)
   except Exception as connect_error:
       error_str = str(connect_error).lower()
       if "timeout" in error_str or "unavailable" in error_str:
           raise ConnectionError(
               f"Cannot connect to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}. "
               f"Please check:\n"
               f"  1. Milvus server is running\n"
               f"  2. Port {settings.MILVUS_PORT} is correct (default: 19530 for gRPC)\n"
               f"  3. Network/firewall allows connection\n"
               f"  4. Authentication credentials if required"
           ) from connect_error
   ```

**Files đã sửa:**
- `app/core/config.py` (default port: 8000 → 19530)
- `app/infrastructure/search/milvus_client.py` (cải thiện error handling)
- `.env` (MILVUS_PORT=19530)

**Kết quả:** ✅ Milvus kết nối thành công với port 19530

---

### Bug #4: Milvus Connection Timeout

**Mô tả:**
- Lỗi: `grpc.FutureTimeoutError` khi kết nối Milvus
- Xảy ra khi: Connection timeout (default 10s quá ngắn)
- Nguyên nhân: Network latency hoặc server chậm phản hồi

**Giải pháp:**
1. Tăng timeout từ 10s → 30s:
   ```python
   MILVUS_TIMEOUT: int = 30  # Connection timeout in seconds
   ```

2. Thêm authentication support (nếu cần):
   ```python
   MILVUS_USER: Optional[str] = None
   MILVUS_PASSWORD: Optional[str] = None
   ```

3. Thêm setting để làm Milvus optional:
   ```python
   MILVUS_REQUIRED: bool = True  # Có thể set False để app vẫn chạy được
   ```

**Files đã sửa:**
- `app/core/config.py`
- `app/main.py` (thêm try-except cho optional Milvus)

**Kết quả:** ✅ Timeout đủ dài, connection thành công

---

## 🔧 Các Cải Tiến Khác

### 1. Optional Services Support

Thêm khả năng làm các services optional để app vẫn chạy được khi một service không available:

```python
# app/core/config.py
REDIS_REQUIRED: bool = False
MILVUS_REQUIRED: bool = True
NEO4J_REQUIRED: bool = True

# app/main.py
try:
    await cache.connect()
except Exception as e:
    if settings.REDIS_REQUIRED:
        raise
    else:
        logger.warning(f"Redis connection failed (optional): {e}")
```

### 2. Better Error Messages

Cải thiện error messages để dễ debug hơn:

```python
# Milvus connection error với hướng dẫn cụ thể
raise ConnectionError(
    f"Cannot connect to Milvus at {host}:{port}. "
    f"Please check:\n"
    f"  1. Milvus server is running\n"
    f"  2. Port {port} is correct (default: 19530 for gRPC)\n"
    f"  3. Network/firewall allows connection\n"
    f"  4. Authentication credentials if required"
)
```

### 3. Auto-Create Database Support

Thêm khả năng tự động tạo database nếu chưa tồn tại:

```python
# app/infrastructure/db/connection.py
async def ensure_database(self):
    """Auto-create database if it doesn't exist"""
    # Connect to postgres database
    # Check if target database exists
    # Create if not exists
```

---

## 📊 Timeline Troubleshooting

| Thời gian | Vấn đề | Giải pháp | Kết quả |
|-----------|--------|-----------|---------|
| 14:30 | SQLAlchemy `metadata` reserved | Đổi `metadata` → `meta_data` | ✅ Fixed |
| 14:32 | Redis authentication | Thêm password support | ✅ Fixed |
| 14:34 | Milvus port 8000 fail | Test port 19530 | 🔄 Investigating |
| 14:40 | Milvus timeout | Tăng timeout 10s → 30s | 🔄 Investigating |
| 14:45 | Milvus port wrong | Đổi port 8000 → 19530 | ✅ Fixed |

---

## 🎯 Lessons Learned

### 1. **Luôn kiểm tra port đúng cho service**

- Milvus có 2 ports: 8000 (HTTP) và 19530 (gRPC)
- pymilvus client cần port gRPC (19530), không phải HTTP (8000)
- **Lesson:** Đọc documentation về ports trước khi config

### 2. **Reserved names trong frameworks**

- SQLAlchemy có reserved names như `metadata`
- **Lesson:** Tránh dùng reserved names, hoặc đổi tên field

### 3. **Authentication support từ đầu**

- Redis và Milvus có thể yêu cầu authentication
- **Lesson:** Nên hỗ trợ authentication ngay từ đầu, không đợi đến khi cần

### 4. **Optional services pattern**

- Không phải service nào cũng critical
- **Lesson:** Cho phép services optional để app vẫn chạy được khi một service down

### 5. **Better error messages**

- Error messages rõ ràng giúp debug nhanh hơn
- **Lesson:** Luôn cung cấp hướng dẫn cụ thể trong error messages

---

## ✅ Kết Quả Cuối Cùng

### Trước khi fix:
```
❌ SQLAlchemy: Attribute name 'metadata' is reserved
❌ Redis: Authentication required
❌ Milvus: Fail connecting to server on port 8000
❌ App: Cannot start
```

### Sau khi fix:
```
✅ SQLAlchemy: Tables created successfully
✅ Redis: Connection established with password
✅ Milvus: Connected to 124.197.21.40:19530
✅ App: Started successfully
```

### Test Results:
```bash
✅ Database 'robot_mem0' already exists
✅ Database connection pool created
✅ Database tables created/verified
✅ Redis connection established
✅ Connected to Milvus at 124.197.21.40:19530
✅ Loaded existing collection: user_facts
✅ PIKA Memory System started successfully
```

---

## 📝 Files Đã Sửa

1. **app/infrastructure/db/models.py**
   - Đổi `metadata` → `meta_data` trong 3 models

2. **app/domains/memory/infrastructure/repositories/fact_repository_impl.py**
   - Cập nhật SQL queries để dùng `meta_data` column
   - Mapping `meta_data` (DB) → `metadata` (entity)

3. **app/core/config.py**
   - Thêm `REDIS_PASSWORD`, `REDIS_USERNAME`
   - Cập nhật `redis_url` property với password support
   - Thêm `MILVUS_USER`, `MILVUS_PASSWORD`, `MILVUS_TIMEOUT`
   - Đổi default `MILVUS_PORT: 8000 → 19530`
   - Thêm `REDIS_REQUIRED`, `MILVUS_REQUIRED`, `NEO4J_REQUIRED`

4. **app/infrastructure/cache/client.py**
   - Sử dụng `settings.redis_url` (đã có password)

5. **app/infrastructure/search/milvus_client.py**
   - Cải thiện error handling
   - Thêm authentication support
   - Better error messages

6. **app/main.py**
   - Thêm try-except cho optional services (Redis, Milvus, Neo4j)

7. **.env**
   - `MILVUS_PORT=19530` (thay vì 8000)
   - `REDIS_PASSWORD=yourStrongPassword`

---

## 🚀 Recommendations

### 1. **Documentation**
- Tạo `.env.example` với tất cả các ports đúng
- Document về Milvus ports (8000 vs 19530)

### 2. **Testing**
- Thêm integration tests cho connection failures
- Test với optional services disabled

### 3. **Monitoring**
- Thêm health checks cho từng service
- Alert khi services không available

### 4. **Configuration**
- Validate ports trong config
- Warn nếu dùng port không đúng (ví dụ: Milvus port 8000)

---

## 📚 References

- [Milvus Ports Documentation](https://milvus.io/docs/install_standalone-docker.md)
- [SQLAlchemy Reserved Names](https://docs.sqlalchemy.org/en/20/core/metadata.html)
- [Redis Authentication](https://redis.io/docs/management/security/authentication/)
- [pymilvus Connection](https://milvus.io/api-reference/pymilvus/v2.4.0/connections.html)

---

**Kết luận:** Quá trình fix bugs này mất nhiều thời gian do phải troubleshoot nhiều vấn đề liên quan. Tuy nhiên, các fixes đã được implement một cách có hệ thống và có documentation đầy đủ để tránh lặp lại các vấn đề tương tự trong tương lai.

---

*Report này được tạo tự động để document quá trình troubleshooting và fix bugs.*

