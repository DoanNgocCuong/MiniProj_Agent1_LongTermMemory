"""
Mem0 client wrapper với support cho cả OSS và Enterprise API.
Refactored từ src/memory/mem_client.py với improvements.
"""
import os
from typing import Optional, List, Dict, Any

# Lazy imports để tránh lỗi khi package chưa được cài
try:
    from mem0 import MemoryClient
except ImportError:
    MemoryClient = None

try:
    from mem0.memory.main import Memory
except ImportError:
    Memory = None

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import Mem0Error
from app.resilience.retry import retry_with_backoff
from app.resilience.circuit_breaker import circuit_breaker

logger = get_logger(__name__)


def _build_mem0_oss_config() -> Dict[str, Any]:
    """
    Build Mem0 OSS configuration từ settings.
    
    Returns:
        Dict chứa config cho Memory.from_config()
    """
    # Vector Store Config
    vector_store_config = {
        "provider": settings.MEM0_VECTOR_STORE_PROVIDER,
        "config": {}
    }
    
    if settings.MEM0_VECTOR_STORE_PROVIDER == "qdrant":
        vector_store_config["config"] = {
            "collection_name": settings.MEM0_VECTOR_STORE_COLLECTION_NAME,
            "host": settings.MEM0_VECTOR_STORE_HOST,
            "port": settings.MEM0_VECTOR_STORE_PORT,
        }
        if settings.MEM0_VECTOR_STORE_URL:
            vector_store_config["config"]["url"] = settings.MEM0_VECTOR_STORE_URL
    elif settings.MEM0_VECTOR_STORE_PROVIDER == "chroma":
        vector_store_config["config"] = {
            "collection_name": settings.MEM0_VECTOR_STORE_COLLECTION_NAME,
            "host": settings.MEM0_VECTOR_STORE_HOST,
            "port": settings.MEM0_VECTOR_STORE_PORT,
        }
    elif settings.MEM0_VECTOR_STORE_PROVIDER == "pgvector":
        vector_store_config["config"] = {
            "collection_name": settings.MEM0_VECTOR_STORE_COLLECTION_NAME,
            "dbname": settings.POSTGRES_DB,
            "user": settings.POSTGRES_USER,
            "password": settings.POSTGRES_PASSWORD,
            "host": settings.POSTGRES_HOST,
            "port": settings.POSTGRES_PORT,
        }
    elif settings.MEM0_VECTOR_STORE_PROVIDER == "milvus":
        # Milvus cấu hình theo docs mới của Mem0:
        # - url: "./milvus.db" (Milvus Lite) hoặc "http://host:port"
        # - token: "user:password" (nếu có auth)
        # - embedding_model_dims: 1536 cho text-embedding-3-small
        collection_name = (
            settings.MEM0_VECTOR_STORE_COLLECTION_NAME
            or getattr(settings, "MILVUS_COLLECTION_NAME", "pika_memories")
        )
        # Nếu MEM0_VECTOR_STORE_URL không set, build từ MILVUS_HOST/PORT
        url = settings.MEM0_VECTOR_STORE_URL
        if not url:
            # Mặc định dùng Milvus server mode
            url = f"http://{settings.MILVUS_HOST}:{settings.MILVUS_PORT}"

        milvus_config: Dict[str, Any] = {
            "collection_name": collection_name,
            "embedding_model_dims": 1536,  # text-embedding-3-small
            "url": url,
            # MilvusDBConfig trong mem0 yêu cầu token là string; để "" nếu không dùng auth
            "token": "",
        }

        # Nếu có user/password thì ghép thành token "user:password"
        if settings.MEM0_VECTOR_STORE_USER and settings.MEM0_VECTOR_STORE_PASSWORD:
            milvus_config["token"] = (
                f"{settings.MEM0_VECTOR_STORE_USER}:{settings.MEM0_VECTOR_STORE_PASSWORD}"
            )

        vector_store_config["config"] = milvus_config
    
    # LLM Config
    llm_api_key = settings.MEM0_LLM_API_KEY or settings.OPENAI_API_KEY
    llm_config = {
        "provider": settings.MEM0_LLM_PROVIDER,
        "config": {
            "model": settings.MEM0_LLM_MODEL,
        }
    }
    if llm_api_key:
        llm_config["config"]["api_key"] = llm_api_key
    
    # Embedder Config
    embedder_api_key = settings.MEM0_EMBEDDER_API_KEY or settings.OPENAI_API_KEY
    embedder_config = {
        "provider": settings.MEM0_EMBEDDER_PROVIDER,
        "config": {
            "model": settings.MEM0_EMBEDDER_MODEL,
        }
    }
    if embedder_api_key:
        embedder_config["config"]["api_key"] = embedder_api_key
    
    # Graph Store Config (optional)
    graph_store_config = None
    if settings.MEM0_GRAPH_STORE_ENABLED and settings.MEM0_VERSION == "v1.1":
        graph_store_config = {
            "provider": settings.MEM0_GRAPH_STORE_PROVIDER,
            "config": {}
        }
        if settings.MEM0_GRAPH_STORE_PROVIDER == "neo4j":
            graph_store_config["config"] = {
                "uri": settings.NEO4J_URI,
                "user": settings.NEO4J_USER,
                "password": settings.NEO4J_PASSWORD,
            }
    
    # Build final config
    mem0_config = {
        "vector_store": vector_store_config,
        "llm": llm_config,
        "embedder": embedder_config,
        "version": settings.MEM0_VERSION,
    }
    
    if graph_store_config:
        mem0_config["graph_store"] = graph_store_config
    
    if settings.MEM0_HISTORY_DB_PATH:
        mem0_config["history_db_path"] = settings.MEM0_HISTORY_DB_PATH
    
    return mem0_config


def _convert_messages_to_text(messages: List[Dict[str, str]]) -> str:
    """
    Convert list of messages thành text string cho Mem0 OSS.
    
    Args:
        messages: List of messages [{"role": "user", "content": "..."}]
        
    Returns:
        Combined text string
    """
    if not messages:
        return ""
    
    text_parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if content:
            text_parts.append(f"{role.capitalize()}: {content}")
    
    return "\n".join(text_parts)


class Mem0ClientWrapper:
    """
    Wrapper cho Mem0 với support cả OSS và Enterprise API.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        project_id: Optional[str] = None,
        use_oss: Optional[bool] = None,
    ):
        """
        Initialize Mem0 client wrapper.
        
        Args:
            api_key: Mem0 API key (chỉ dùng cho Enterprise API)
            org_id: Organization ID (chỉ dùng cho Enterprise API)
            project_id: Project ID (chỉ dùng cho Enterprise API)
            use_oss: Force sử dụng OSS (default: từ settings.MEM0_USE_OSS)
        """
        self.use_oss = use_oss if use_oss is not None else settings.MEM0_USE_OSS
        
        if self.use_oss:
            # Mem0 OSS - không cần API key
            if Memory is None:
                raise ImportError("Mem0 OSS package not found. Install with: pip install mem0ai")
            try:
                config = _build_mem0_oss_config()
                logger.info(f"Initializing Mem0 OSS with config: vector_store={config['vector_store']['provider']}, llm={config['llm']['provider']}")
                self.client = Memory.from_config(config)
                logger.info("Mem0 OSS client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Mem0 OSS client: {e}")
                raise Mem0Error(f"Failed to initialize Mem0 OSS client: {e}") from e
        else:
            # Mem0 Enterprise API - cần API key
            if MemoryClient is None:
                raise ImportError("Mem0 Enterprise package not found. Install with: pip install mem0ai")
            self.api_key = api_key or settings.MEM0_API_KEY
            self.org_id = org_id or settings.MEM0_ORG_ID
            self.project_id = project_id or settings.MEM0_PROJECT_ID
            
            if not self.api_key:
                raise ValueError("MEM0_API_KEY is required for Enterprise API")
            
            try:
                self.client = MemoryClient(
                    api_key=self.api_key,
                    org_id=self.org_id,
                    project_id=self.project_id,
                )
                logger.info("Mem0 Enterprise client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Mem0 Enterprise client: {e}")
                raise Mem0Error(f"Failed to initialize Mem0 Enterprise client: {e}") from e
    
    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def add(
        self,
        messages: List[Dict[str, str]],
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        infer: Optional[bool] = True,
        async_mode: Optional[bool] = False,
    ) -> List[Dict[str, Any]]:
        """
        Add memories từ conversation messages.
        
        Args:
            messages: List of messages [{"role": "user", "content": "..."}]
            user_id: User ID
            agent_id: Agent ID (conversation ID)
            run_id: Run ID
            metadata: Additional metadata
            infer: Whether to infer facts (chỉ dùng cho Enterprise API)
            async_mode: Whether to use async mode (chỉ dùng cho Enterprise API)
            
        Returns:
            List of created memory objects hoặc dict với message
            
        Raises:
            Mem0Error: If the operation fails
        """
        try:
            if self.use_oss:
                # Mem0 OSS: API chính thức dùng tham số đầu tiên là `messages`
                # (str hoặc List[{"role","content"}]). Ta truyền thẳng messages gốc,
                # để Mem0 tự xử lý format theo version mới.
                if not messages:
                    logger.warning("Empty messages, skipping add")
                    return []
                
                logger.info(f"Adding memories for user_id={user_id}, agent_id={agent_id} (OSS)")
                
                # Mem0 OSS add() là sync, không phải async
                result = self.client.add(
                    messages,
                    user_id=user_id,
                    agent_id=agent_id,
                    run_id=run_id,
                    metadata=metadata,
                )
                
                # OSS returns {"message": "ok"} hoặc list of results
                if isinstance(result, dict) and "message" in result:
                    logger.info("Successfully added memories (OSS)")
                    # Return empty list hoặc extract từ response nếu có
                    return []
                elif isinstance(result, list):
                    logger.info(f"Successfully added {len(result)} memories (OSS)")
                    return result
                else:
                    logger.warning(f"Unexpected response format: {result}")
                    return []
            else:
                # Mem0 Enterprise API
                # Ensure all messages have content
                for idx, message in enumerate(messages):
                    if not message.get("content"):
                        messages[idx]["content"] = " "
                
                logger.info(f"Adding memories for user_id={user_id}, agent_id={agent_id} (Enterprise)")
                result = await self.client.add(
                    messages,
                    user_id=user_id,
                    agent_id=agent_id,
                    run_id=run_id,
                    metadata=metadata,
                    infer=infer,
                    async_mode=async_mode,
                )
                logger.info(f"Successfully added {len(result)} memories (Enterprise)")
                return result
        except Exception as e:
            logger.error(f"Error adding memories: {e}")
            raise Mem0Error(f"Failed to add memories: {e}") from e
    
    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        top_k: Optional[int] = 10,
        fields: Optional[List[str]] = None,
        rerank: Optional[bool] = False,
        keyword_search: Optional[bool] = False,
        filter_memories: Optional[bool] = False,
        threshold: Optional[float] = 0.3,
        org_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search memories by query.
        
        Args:
            query: Search query string
            user_id: Filter by user ID
            agent_id: Filter by agent ID
            run_id: Filter by run ID
            top_k: Maximum number of results (limit cho OSS)
            fields: Fields to return (chỉ dùng cho Enterprise)
            rerank: Whether to rerank results (chỉ dùng cho Enterprise)
            keyword_search: Whether to use keyword search (chỉ dùng cho Enterprise)
            filter_memories: Whether to filter memories (chỉ dùng cho Enterprise)
            threshold: Minimum similarity threshold (chỉ dùng cho Enterprise)
            org_id: Organization ID (chỉ dùng cho Enterprise)
            project_id: Project ID (chỉ dùng cho Enterprise)
            
        Returns:
            List of search results
            
        Raises:
            Mem0Error: If the operation fails
        """
        try:
            if self.use_oss:
                logger.info(f"Searching memories with query='{query[:50]}...', user_id={user_id} (OSS)")
                
                # Mem0 OSS search() là sync
                result = self.client.search(
                    query=query,
                    user_id=user_id,
                    agent_id=agent_id,
                    run_id=run_id,
                    limit=top_k or 10,
                )
                
                # OSS returns {"memories": [...]} hoặc list
                if isinstance(result, dict) and "memories" in result:
                    memories = result["memories"]
                elif isinstance(result, list):
                    memories = result
                else:
                    memories = []
                
                logger.info(f"Found {len(memories)} memories (OSS)")
                return memories
            else:
                logger.info(f"Searching memories with query='{query[:50]}...', user_id={user_id} (Enterprise)")
                result = await self.client.search(
                    query,
                    user_id=user_id,
                    agent_id=agent_id,
                    run_id=run_id,
                    top_k=top_k,
                    rerank=rerank,
                    keyword_search=keyword_search,
                    filter_memories=filter_memories,
                    threshold=threshold,
                    org_id=org_id or self.org_id,
                    project_id=project_id or self.project_id,
                    fields=fields,
                )
                logger.info(f"Found {len(result)} memories (Enterprise)")
                return result
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            raise Mem0Error(f"Failed to search memories: {e}") from e
    
    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def get_all(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        page_size: Optional[int] = 100,
        days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all memories với optional filters.
        
        Args:
            user_id: Filter by user ID
            agent_id: Filter by agent ID
            run_id: Filter by run ID
            page_size: Number of results per page (limit cho OSS)
            days: Filter by days (chỉ dùng cho Enterprise)
            
        Returns:
            List of memory objects
            
        Raises:
            Mem0Error: If the operation fails
        """
        try:
            if self.use_oss:
                logger.info(f"Getting all memories for user_id={user_id} (OSS)")
                
                # Mem0 OSS get_all() là sync
                result = self.client.get_all(
                    user_id=user_id,
                    agent_id=agent_id,
                    run_id=run_id,
                    limit=page_size or 100,
                )
                
                # OSS returns {"memories": [...]} hoặc list
                if isinstance(result, dict) and "memories" in result:
                    memories = result["memories"]
                elif isinstance(result, list):
                    memories = result
                else:
                    memories = []
                
                logger.info(f"Retrieved {len(memories)} memories (OSS)")
                return memories
            else:
                logger.info(f"Getting all memories for user_id={user_id} (Enterprise)")
                result = await self.client.get_all(
                    user_id=user_id,
                    agent_id=agent_id,
                    run_id=run_id,
                    page_size=page_size,
                    version="v2",
                )
                # Handle different response formats
                if isinstance(result, dict) and "data" in result:
                    memories = result["data"]
                elif isinstance(result, list):
                    memories = result
                else:
                    memories = []
                
                logger.info(f"Retrieved {len(memories)} memories (Enterprise)")
                return memories
        except Exception as e:
            logger.error(f"Error getting all memories: {e}")
            raise Mem0Error(f"Failed to get all memories: {e}") from e
