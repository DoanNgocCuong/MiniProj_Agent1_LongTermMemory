---
name: Integrate Mem0 REST API with 5-Layer Caching + Proactive Warming
overview: Tích hợp Mem0 REST API và thêm cơ chế proactive cache warming tự động sau khi extract_facts thành công để update L4→L3→L2 cache layers.
todos:
  - id: create-rest-client
    content: ""
    status: completed
  - id: update-mem0-wrapper
    content: Update Mem0ClientWrapper để hỗ trợ use_rest_api flag, khởi tạo Mem0RestClient khi use_rest_api=True, giữ nguyên interface methods
    status: completed
    dependencies:
      - create-rest-client
  - id: add-proactive-warming-extraction
    content: Update ExtractionService để inject ProactiveCacheService, sau khi extract thành công gọi update_user_favorite_cache() với error handling non-blocking
    status: completed
  - id: update-extraction-dependencies
    content: Update get_extraction_service() dependency để inject ProactiveCacheService và L2MaterializedView vào ExtractionService
    status: completed
    dependencies:
      - add-proactive-warming-extraction
  - id: update-worker-task
    content: Update extraction_task.py để pass ProactiveCacheService vào ExtractionService trong worker process
    status: completed
    dependencies:
      - update-extraction-dependencies
  - id: update-config
    content: Thêm MEM0_REST_API_URL, MEM0_USE_REST_API, MEM0_REST_API_TIMEOUT settings vào config.py
    status: completed
  - id: test-proactive-warming
    content: ""
    status: pending
    dependencies:
      - update-worker-task
  - id: add-monitoring
    content: Add logging cho proactive cache warming (success/failure, latency) để monitor performance
    status: completed
    dependencies:
      - add-proactive-warming-extraction
  - id: add-stm-l0-cache
    content: "Thêm L0 cache cho STM search trong STMService, cache key: stm_search:{session_id}:{hash(query)}, flow: L0→L1→STM context"
    status: completed
  - id: fix-merge-rank-boost
    content: "Fix merge & rank boost values trong MemoryOrchestrator: STM+LTM overlap = +0.15, STM recency = +0.1 (theo document)"
    status: completed
---

# Plan: Integrate Mem0 REST API với 5-Layer Caching + Proactive Warming

## Tổng quan

1. Tích hợp Mem0 REST API service (http://124.197.21.40:8888) thay thế SDK mode
2. Thêm cơ chế proactive cache warming tự động sau khi extract_facts/add memory thành công
3. Đảm bảo hệ thống caching 5 lớp (L0→L1→L2→L3→L4) hoạt động hiệu quả

## Proactive Cache Warming Flow

Theo document caching 5 lớp, sau khi extraction thành công cần:

```javascript
Extract Facts Success
    ↓
1. Query L4 (Mem0 REST API) cho user_favorite_summary
    ↓
2. Save vào L3 (PostgreSQL Materialized View)
    ↓
3. Warm L2 (Redis Result Cache) với top results
    ↓
4. Increment version tag → Invalidate old L2 entries
    ↓
5. Update L1 (Redis Embedding Cache) nếu có embedding mới
```



## Implementation Plan

### Phase 1: REST API Client cho Mem0

**File:** `app/infrastructure/mem0/mem0_rest_client.py`

- Tạo `Mem0RestClient` class với httpx.AsyncClient
- Methods: `add_memories()`, `search_memories()`, `get_all()`
- Retry logic, circuit breaker, error handling

### Phase 2: Update Mem0ClientWrapper

**Update:** `app/infrastructure/mem0/mem0_client.py`

- Thêm `use_rest_api` flag
- Khi `use_rest_api=True`: khởi tạo `Mem0RestClient`
- Giữ nguyên interface methods

### Phase 3: Thêm Proactive Cache Warming vào ExtractionService

**Update:** `app/domains/memory/application/services/extraction_service.py`

- Inject `ProactiveCacheService` vào `__init__`
- Sau khi extract facts thành công, gọi:
  ```python
          await self.proactive_cache_service.update_user_favorite_cache(user_id)
  ```




- Wrap trong try-except để không break extraction nếu cache warming fail

**Flow:**

1. Extract facts via repository
2. Invalidate old cache (existing logic)
3. **NEW:** Trigger proactive cache warming

- Query L4 (Mem0) cho user favorites
- Update L3 (PostgreSQL Materialized View)
- Warm L2 (Redis Result Cache)
- Bump version tag

### Phase 4: Update ExtractionService Dependencies

**Update:** `app/api/dependencies.py`

- Update `get_extraction_service()` để inject:
- `ProactiveCacheService` (cần `MemoryRepository` + `L2MaterializedView`)
- `L2MaterializedView` (cần database session)

**Update:** `workers/tasks/extraction_task.py`

- Update `process_extraction_job()` để pass `ProactiveCacheService` vào `ExtractionService`
- Đảm bảo async worker cũng trigger cache warming

### Phase 5: Configuration

**Update:** `app/core/config.py`

- Thêm REST API settings (đã có trong plan trước)
- Verify `PROACTIVE_CACHE_ENABLED` flag (nếu có)

### Phase 6: Error Handling & Performance

- Proactive cache warming phải non-blocking:
- Wrap trong try-except, log error nhưng không raise
- Có thể run async để không block extraction response
- Consider async fire-and-forget pattern:
  ```python
          # Fire and forget - don't wait for cache warming
          asyncio.create_task(
              self.proactive_cache_service.update_user_favorite_cache(user_id)
          )
  ```




### Phase 7: Thêm L0 Cache cho STM Search

**Update:** `app/domains/memory/application/services/stm_service.py` hoặc tạo STM search method mới

- Thêm L0 cache cho STM search results
- Cache key: `stm_search:{session_id}:{hash(query)}`
- Flow: L0 (in-mem) → L1 (Redis) → STM context lookup
- Đảm bảo STM search có cache layers giống LTM

### Phase 8: Fix Merge & Rank Boost Values

**Update:** `app/domains/memory/application/services/memory_orchestrator.py`

- Fix boost values để đúng với document:
- STM+LTM overlap boost: +0.15 (thay vì +0.1)
- STM recency bonus: +0.1 (thay vì +0.05)

### Phase 9: (Optional) STM API Endpoint

**File:** `app/api/v1/endpoints/stm.py` (nếu cần)

- Tạo endpoint `POST /api/v1/stm/add_message` như trong document
- Input: session_id, role, content
- Output: HTTP 200 (triggers compression if needed)

**Note:** Có thể không cần nếu STM được manage internally trong conversation flow.

## Files sẽ được tạo/sửa

### Modified Files:

- `app/infrastructure/mem0/mem0_client.py` - Add REST API mode
- `app/infrastructure/mem0/mem0_rest_client.py` - New REST API client
- `app/domains/memory/application/services/extraction_service.py` - Add proactive cache warming
- `app/domains/memory/application/services/memory_orchestrator.py` - Fix merge & rank boost values
- `app/domains/memory/application/services/stm_service.py` - Add L0 cache cho STM search
- `app/api/dependencies.py` - Update dependencies injection
- `workers/tasks/extraction_task.py` - Update worker to use proactive caching
- `app/core/config.py` - Add REST API settings

### Optional Files:

- `app/api/v1/endpoints/stm.py` - STM API endpoint (nếu cần expose)

### No Changes Needed:

- `app/infrastructure/cache/proactive_cache.py` - Đã có sẵn
- `app/infrastructure/cache/l2_materialized_view.py` - Đã có sẵn
- Cache layers (L0, L1, L2, L3) - Đã hoạt động tốt

## Verification

Sau khi implement, verify:

1. Extract facts thành công → logs show "Updating favorite cache for user_id=..."
2. L3 (PostgreSQL) được update với user favorite summary
3. L2 (Redis) được warm với search results