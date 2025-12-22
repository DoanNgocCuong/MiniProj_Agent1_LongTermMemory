"""
Memory Application Layer - Use cases and application services.

This package contains application services that orchestrate domain logic:
- Memory service: Handles memory CRUD operations
- Job service: Manages background job processing
- Extraction service: Coordinates memory extraction workflows

Application services coordinate between domain entities and infrastructure,
implementing use cases without containing business logic (which stays in domain layer).
"""

