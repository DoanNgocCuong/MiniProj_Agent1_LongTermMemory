Đang phân tích luồng dữ liệu (Data Flow) khi thực hiện query "user favorite". Kiểm tra thêm các file liên quan:

[2 tools called]

Tóm tắt Data Flow khi query "user favorite":

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. CLIENT REQUEST                                                    │
│    POST /search_facts                                                │
│    {                                                                 │
│      "query": "user favorite (movie, character, pet...)",           │
│      "user_id": "user123",                                          │
│      "limit": 10,                                                   │
│      "score_threshold": 0.3                                         │
│    }                                                                 │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. FASTAPI ENDPOINT (src/main.py)                                   │
│    @app.post("/search_facts")                                       │
│    async def search_facts(request: SearchRequest)                   │
│    - Validate request                                                │
│    - Extract: query, user_id, limit, threshold                      │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. MEMORY INTERFACE LAYER (src/memory/mem_client.py)                │
│    await memory_client.search(                                      │
│        query="user favorite...",                                    │
│        user_id="user123",                                           │
│        top_k=10,                                                    │
│        threshold=0.3                                                │
│    )                                                                │
│    - Wrapper layer để chuẩn hóa interface                           │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. MEM0 CLIENT SDK (mem0/client/main.py)                            │
│    await self.client.search(query, **kwargs)                        │
│    - Build payload: {query, user_id, top_k, threshold, ...}         │
│    - HTTP POST to: https://api.mem0.ai/v1/memories/search/         │
│    - Headers: Authorization: Token $MEM0_API_KEY                    │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   │ HTTP POST Request
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. MEM0 API SERVER (External Service)                               │
│    POST /memories/search/                                           │
│                                                                      │
│    5.1. Authentication & Authorization                              │
│        - Validate API Key                                           │
│                                                                      │
│    5.2. Query Processing                                            │
│        - Extract query: "user favorite (movie, character...)"       │
│        - Build filters: {user_id: "user123"}                        │
│                                                                      │
│    5.3. Vector Embedding                                            │
│        - Embed query text → Vector [0.12, -0.45, 0.78, ...]        │
│        - Using embedding model (OpenAI, Azure OpenAI, etc.)         │
│                                                                      │
│    5.4. Vector Store Search                                         │
│        - Search in Vector DB (Chroma/Qdrant/PGVector)               │
│        - Similarity search với cosine distance                      │
│        - Apply filters: WHERE payload->>'user_id' = 'user123'       │
│        - Filter by threshold: score >= 0.3                          │
│        - Sort by similarity (ascending distance)                    │
│        - Limit: top_k = 10                                          │
│                                                                      │
│    5.5. Format Results                                              │
│        - Transform vector results → Memory objects                  │
│        - Include: id, memory, categories, metadata, score, etc.     │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   │ HTTP Response (JSON)
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. RESPONSE TRANSFORMATION (src/main.py)                            │
│    results = [                                                      │
│      {                                                              │
│        "id": "mem_123",                                             │
│        "memory": "User's favorite movie is The Matrix",             │
│        "categories": ["favorite_movie"],                            │
│        "user_id": "user123",                                        │
│        "score": 0.85,                                               │
│        "metadata": {...}                                            │
│      },                                                             │
│      ...                                                            │
│    ]                                                                │
│                                                                      │
│    Convert to SearchResultResponse format                           │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 7. CLIENT RESPONSE                                                  │
│    {                                                                │
│      "status": "ok",                                                │
│      "count": 5,                                                    │
│      "facts": [                                                     │
│        {                                                            │
│          "id": "mem_123",                                           │
│          "source": "conversation",                                  │
│          "user_id": "user123",                                      │
│          "conversation_id": "...",                                  │
│          "fact_type": ["favorite_movie"],                           │
│          "fact_value": "User's favorite movie is The Matrix",       │
│          "metadata": {...},                                         │
│          "score": 0.85                                              │
│        },                                                           │
│        ...                                                          │
│      ]                                                              │
│    }                                                                │
└─────────────────────────────────────────────────────────────────────┘
```

## Chi tiết các bước

### Step 1-2: API Gateway Layer

```128:143:src/main.py
@app.post("/search_facts", response_model=Dict, tags=["production"])
async def search_facts(request: SearchRequest):
    """
    Search facts using Mem0 API
    """
    try:
        logger.info(f"Searching facts with query: {request.query}")
      
        # Call MemoryClient to search memories
        results = await memory_client.search(
            query=request.query,
            user_id=request.user_id,
            agent_id=request.conversation_id,  # Using conversation_id as agent_id
            top_k=request.limit,
            threshold=request.score_threshold
        )
```

### Step 3-4: SDK Layer

```88:101:src/memory/mem_client.py
        return await self.client.search(
            query, 
            user_id=user_id,
            # agent_id=agent_id,
            # run_id=run_id,
            top_k=top_k, 
            rerank=rerank, 
            keyword_search=keyword_search, 
            filter_memories=filter_memories, 
            threshold=threshold,
            org_id=org_id,
            project_id=project_id,
            fields=fields,
        )
```

Mem0 Client gửi HTTP request:

```182:188:mem0/client/main.py
        payload = {"query": query}
        payload.update({k: v for k, v in kwargs.items() if v is not None})
        logger.info(f"=======Search payload: {payload}")
        response = await self.client.post("/memories/search/", json=payload)
        response.raise_for_status()
        capture_client_event("client.search", self, {"limit": kwargs.get("limit", 100)})
        return response.json()
```

### Step 5: Mem0 API (Server-side - xử lý trong Mem0 cloud)

1. Embed query → vector
2. Vector search:

   - Tính similarity với các vectors trong database
   - Filter: `user_id = "user123"`
   - Threshold: `score >= 0.3`
   - Sort by score (desc)
   - Limit: `top_k = 10`
3. Kết quả từ vector store (ví dụ PGVector):

```91:129:mem0/vector_stores/pgvector.py
    def search(self, query, limit=5, filters=None):
        """
        Search for similar vectors.

        Args:
            query (List[float]): Query vector.
            limit (int, optional): Number of results to return. Defaults to 5.
            filters (Dict, optional): Filters to apply to the search. Defaults to None.

        Returns:
            list: Search results.
        """
        filter_conditions = []
        filter_params = []

        if filters:
            for k, v in filters.items():
                filter_conditions.append("payload->>%s = %s")
                filter_params.extend([k, str(v)])

        filter_clause = (
            "WHERE " + " AND ".join(filter_conditions) if filter_conditions else ""
        )

        self.cur.execute(
            f"""
            SELECT id, vector <-> %s::vector AS distance, payload
            FROM {self.collection_name}
            {filter_clause}
            ORDER BY distance
            LIMIT %s
        """,
            (query, *filter_params, limit),
        )

        results = self.cur.fetchall()
        return [
            OutputData(id=str(r[0]), score=float(r[1]), payload=r[2]) for r in results
        ]
```

### Step 6-7: Response Formatting

```148:167:src/main.py
        # Convert to response format
        facts = [
            SearchResultResponse(
                id=result.get("id"),
                source="conversation",
                user_id=result.get("user_id"),
                conversation_id=request.conversation_id,
                fact_type=result.get("categories"),
                fact_value=result.get("memory"),
                metadata=result.get("metadata"),
                score=result.get("score"),
            )
            for result in results
        ]
      
        return {
            "status": "ok",
            "count": len(facts),
            "facts": facts
        }
```

## Tóm tắt

1. Text Query → FastAPI endpoint nhận request
2. FastAPI → MemoryInterface wrapper layer
3. MemoryInterface → Mem0 SDK Client
4. Mem0 SDK → HTTP POST to Mem0 API
5. Mem0 API → Embed query thành vector
6. Vector Store → Semantic search với filters
7. Results → Transform và format response
8. Client ← JSON response với facts

Luồng này sử dụng semantic search (vector similarity) thay vì keyword search, giúp tìm memories liên quan đến "user favorite" dù cách diễn đạt khác.
