"""
Neo4j Graph Database Client

Client for Neo4j graph database operations (create nodes, relationships, queries).
"""

from typing import List, Dict, Any, Optional
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable

from app.core.config import settings
from app.core.logging import logger


class Neo4jClient:
    """Neo4j graph database client"""
    
    def __init__(self):
        self.driver = None
        self.connected = False
    
    async def connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            # Test connection
            await self.driver.verify_connectivity()
            self.connected = True
            logger.info(f"Connected to Neo4j at {settings.NEO4J_URI}")
            
            # Ensure constraints exist
            await self._ensure_constraints()
            
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Neo4j"""
        if self.driver:
            await self.driver.close()
            self.connected = False
            logger.info("Disconnected from Neo4j")
    
    async def _ensure_constraints(self):
        """Ensure database constraints and indexes exist"""
        try:
            async with self.driver.session() as session:
                # Create constraints (unique constraints also create indexes automatically)
                constraints = [
                    "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
                    "CREATE CONSTRAINT fact_id_unique IF NOT EXISTS FOR (f:Fact) REQUIRE f.id IS UNIQUE",
                    "CREATE CONSTRAINT conversation_id_unique IF NOT EXISTS FOR (c:Conversation) REQUIRE c.id IS UNIQUE",
                ]
                
                for constraint_query in constraints:
                    try:
                        await session.run(constraint_query)
                    except Exception as e:
                        # Constraint may already exist, ignore
                        logger.debug(f"Constraint creation skipped (may exist): {e}")
                
                # Create additional indexes for performance
                indexes = [
                    "CREATE INDEX user_created_at_idx IF NOT EXISTS FOR (u:User) ON (u.created_at)",
                    "CREATE INDEX fact_category_idx IF NOT EXISTS FOR (f:Fact) ON (f.category)",
                    "CREATE INDEX fact_created_at_idx IF NOT EXISTS FOR (f:Fact) ON (f.created_at)",
                    "CREATE INDEX fact_user_id_idx IF NOT EXISTS FOR (f:Fact) ON (f.user_id)",
                ]
                
                for index_query in indexes:
                    try:
                        await session.run(index_query)
                    except Exception as e:
                        # Index may already exist, ignore
                        logger.debug(f"Index creation skipped (may exist): {e}")
                
                logger.info("Neo4j constraints and indexes ensured")
        except Exception as e:
            logger.warning(f"Error ensuring Neo4j constraints/indexes (may already exist): {e}")
    
    async def create_user_if_not_exists(self, user_id: str) -> bool:
        """Create User node if not exists"""
        try:
            async with self.driver.session() as session:
                query = """
                MERGE (u:User {id: $user_id})
                SET u.created_at = coalesce(u.created_at, datetime())
                RETURN u
                """
                await session.run(query, user_id=user_id)
                return True
        except Exception as e:
            logger.error(f"Error creating user in Neo4j: {e}")
            return False
    
    async def create_fact_node(
        self,
        fact_id: str,
        user_id: str,
        content: str,
        category: str,
        confidence: float
    ) -> bool:
        """Create Fact node and link to User"""
        try:
            async with self.driver.session() as session:
                query = """
                MATCH (u:User {id: $user_id})
                MERGE (f:Fact {id: $fact_id})
                SET f.content = $content,
                    f.category = $category,
                    f.confidence = $confidence,
                    f.created_at = datetime()
                MERGE (u)-[:HAS_FACT]->(f)
                RETURN f
                """
                await session.run(
                    query,
                    user_id=user_id,
                    fact_id=fact_id,
                    content=content,
                    category=category,
                    confidence=confidence
                )
                logger.debug(f"Created fact node {fact_id} in Neo4j")
                return True
        except Exception as e:
            logger.error(f"Error creating fact node in Neo4j: {e}")
            return False
    
    async def create_fact_relationship(
        self,
        source_fact_id: str,
        target_fact_id: str,
        relationship_type: str = "RELATED_TO",
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create relationship between two facts"""
        try:
            async with self.driver.session() as session:
                props = properties or {}
                props_str = ", ".join([f"{k}: ${k}" for k in props.keys()]) if props else ""
                rel_props = f"{{{props_str}}}" if props_str else ""
                
                query = f"""
                MATCH (f1:Fact {{id: $source_id}}), (f2:Fact {{id: $target_id}})
                MERGE (f1)-[r:{relationship_type}{rel_props}]->(f2)
                RETURN r
                """
                await session.run(query, source_id=source_fact_id, target_id=target_fact_id, **props)
                logger.debug(f"Created relationship {source_fact_id} -> {target_fact_id}")
                return True
        except Exception as e:
            logger.error(f"Error creating relationship in Neo4j: {e}")
            return False
    
    async def get_fact_relationships(
        self,
        fact_id: str,
        relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get relationships for a fact"""
        try:
            async with self.driver.session() as session:
                rel_filter = f":{relationship_type}" if relationship_type else ""
                query = f"""
                MATCH (f:Fact {{id: $fact_id}})-[r{rel_filter}]->(related:Fact)
                RETURN related.id as fact_id, type(r) as relationship_type, properties(r) as properties
                """
                result = await session.run(query, fact_id=fact_id)
                relationships = []
                async for record in result:
                    relationships.append({
                        "fact_id": record["fact_id"],
                        "relationship_type": record["relationship_type"],
                        "properties": dict(record["properties"]) if record["properties"] else {}
                    })
                return relationships
        except Exception as e:
            logger.error(f"Error getting relationships from Neo4j: {e}")
            return []
    
    async def delete_fact_node(self, fact_id: str) -> bool:
        """Delete a fact node and all its relationships"""
        try:
            async with self.driver.session() as session:
                query = """
                MATCH (f:Fact {id: $fact_id})
                DETACH DELETE f
                """
                await session.run(query, fact_id=fact_id)
                logger.debug(f"Deleted fact node {fact_id} from Neo4j")
                return True
        except Exception as e:
            logger.error(f"Error deleting fact node from Neo4j: {e}")
            return False
    
    async def delete_user_data(self, user_id: str) -> bool:
        """Delete all data for a user (for GDPR)"""
        try:
            async with self.driver.session() as session:
                query = """
                MATCH (u:User {id: $user_id})
                DETACH DELETE u
                """
                await session.run(query, user_id=user_id)
                logger.info(f"Deleted all Neo4j data for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting user data from Neo4j: {e}")
            return False


# Global Neo4j client instance
neo4j_client = Neo4jClient()

