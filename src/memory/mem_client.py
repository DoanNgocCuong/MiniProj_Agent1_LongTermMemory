import os
from pydoc import pager
from typing import Optional, List, Dict, Any, Literal
from mem0 import MemoryClient
from datetime import datetime, timedelta


class MemoryInterface:
    def __init__(self):
        self.client = MemoryClient(
            api_key=os.getenv("MEM0_API_KEY"), 
            # org_id=os.getenv("MEM0_ORG_ID"), 
            # project_id=os.getenv("MEM0_PROJECT_ID")
        )
    
    async def add(
        self,
        messages: List[Dict[str, str]],
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        infer: Optional[bool] = True,
        async_mode: Optional[bool] = False,
    ) -> List[dict]:
        """
        Thêm memories mới từ messages
        
        Args:
            messages: List các message dạng [{"role": "user", "content": "..."}]
            user_id: ID của user
            agent_id: ID của agent
            run_id: ID của run
            metadata: Metadata bổ sung
            
        Returns:
            List các Memory objects đã tạo
        """
        for idx, message in enumerate(messages):
            if not message.get("content"):
                messages[idx]["content"] = " "

        return await self.client.add(
            messages, 
            user_id=user_id, 
            agent_id=agent_id, 
            run_id=run_id, 
            metadata=metadata, 
            infer=infer, 
            async_mode=async_mode
        )
    
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
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm memories
        
        Args:
            query: Câu query tìm kiếm
            user_id: Filter theo user_id
            agent_id: Filter theo agent_id
            run_id: Filter theo run_id
            top_k: Số lượng kết quả trả về (default: 10)
            fields: List các field muốn trả về trong response
            rerank: Có rerank memories hay không (default: False)
            keyword_search: Tìm kiếm dựa trên keywords (default: False)
            filter_memories: Có filter memories hay không (default: False)
            threshold: Ngưỡng similarity tối thiểu (default: 0.3)
            org_id: Organization ID
            project_id: Project ID
            
        Returns:
            List các SearchResult
        """
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
    
    async def get_all(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        page_size: Optional[int] = 100,
        days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lấy tất cả memories với filter
        
        Args:
            user_id: Filter theo user_id
            agent_id: Filter theo agent_id
            run_id: Filter theo run_id
            limit: Số lượng kết quả trả về (default: 100)
            
        Returns:
            List các Memory objects
        """
        result = await self.client.get_all(
            user_id=user_id,
            run_id=run_id,
            page_size=page_size,
            version="v2"
        )
        # mem0 get_all returns a dict with 'data' key containing the list
        if isinstance(result, dict) and 'data' in result:
            return result['data']
        return result if isinstance(result, list) else []