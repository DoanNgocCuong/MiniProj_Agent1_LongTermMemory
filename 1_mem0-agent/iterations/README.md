# mem0-supadatabase

Link repo: https://github.com/coleam00/ottomator-agents/tree/main/mem0-agent

============
`<think>`
Let me create a comprehensive README and CHANGELOG for this project. I'll structure it professionally to describe the project, its features, installation instructions, and usage.

For the README, I'll include:

1. Project overview
2. Features
3. Installation instructions
4. Usage
5. Configuration
6. Docker deployment
7. License and credits

For the CHANGELOG, I'll create an initial entry for the 1.0 release with all the features that have been implemented.
`</think>`

# Mem0 Chat Assistant with Database Viewer

## Release 1.0

A fullstack application featuring a memory-powered AI chat assistant built with Streamlit, Supabase vector storage, and OpenAI. This project demonstrates how AI can maintain context and remember past conversations across sessions using vector embeddings.

![Mem0 Chat Assistant](screenshot.png)

## Features

### 🧠 Memory-Powered Chat

- Long-term memory storage using vector embeddings
- Contextual responses based on conversation history
- Memory persistence across sessions

### 🔍 Database Explorer

- View and explore the vector database
- Browse all tables in all schemas
- Examine memory contents and metadata

### 🔒 User Authentication

- Secure login and registration using Supabase
- User-specific memories and conversations
- Profile management

### 🔧 Technical Features

- Vector embedding storage for semantic search
- Containerized deployment with Docker
- Error handling and graceful degradation

## Quick Start

### Using Docker Compose

```bash
# Clone the repository
git clone https://github.com/DoanNgocCuong/mem0-supadatabase.git
cd mem0-supadatabase

# Configure your environment variables
cp .env.example .env
# Edit .env with your Supabase and OpenAI credentials

# Start the applications
docker-compose up -d
```

### Accessing the Applications

- Chat Application: http://localhost:25048
- Database Viewer: http://localhost:25049

## Configuration

Edit the `.env` file to configure the following:

```
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
DATABASE_URL=your_database_connection_string
MODEL_CHOICE=gpt-4o-mini  # or another OpenAI model
```

## Architecture

This project consists of two main components:

1. **Mem0 Chat Assistant**: A Streamlit application that provides a chat interface with memory-powered responses.
2. **Database Viewer**: A separate Streamlit application for exploring the vector database.

Both components connect to the same Supabase backend for data storage and authentication.

## Development

### Requirements

- Python 3.10+
- Supabase account
- OpenAI API key

### Local Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the applications
streamlit run v3-streamlit-supabase-mem0.py
streamlit run v3_view_database.py
```

## Troubleshooting

### Common Issues

- **Database Timeout**: Increase PostgreSQL statement_timeout value
- **Authentication Issues**: Ensure Supabase credentials are correct
- **Memory Creation Error**: Check database connection and permissions

## Credits

Developed by [Doan Ngoc Cuong](https://github.com/DoanNgocCuong)

Based on the [Ottomator Mem0 Agent](https://github.com/coleam00/ottomator-agents/tree/main/mem0-agent)

## License

MIT License

```markdown:CHANGELOG.md
# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2024-03-30

### Added
- Initial release of Mem0 Chat Assistant
- Memory-powered conversations using vector embeddings
- User authentication with Supabase
- Database viewer for exploring vector storage
- Docker containerization for both applications
- Profile information display for logged in users
- Memory management features (search, add, clear)
- Error handling and graceful degradation
- Configurable OpenAI model selection
- Real-time chat interface with message history
- Author information and GitHub profile link

### Fixed
- PostgreSQL timeout issues with increased timeouts
- Memory collection creation with proper error handling
- Database connection stability across container restarts
- Authentication session persistence
- Metadata extraction and display in Database Viewer
```

Is there anything specific you'd like me to add to the README or CHANGELOG?


---

# Check ngày 20/12/2025 - Khi AI đã quá mạnh để đọc nhanh 1 repo 



Đang phân tích cách triển khai mem0 trong code hiện tại. Đọc các file chính để hiểu cấu trúc.

[5 tools called]

Đang xem thêm các file trong `studio-integration-version` để hiểu đầy đủ:

[2 tools called]

Tóm tắt cách triển khai mem0 trong code hiện tại:

## Tổng quan triển khai mem0

Có 4 phiên bản triển khai, từ cơ bản đến nâng cao:

---

### 1. Version 1: Basic Implementation (`v1-basic-mem0.py`)

Triển khai cơ bản với in-memory storage:

```8:18:v1-basic-mem0.py
config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o-mini"
        }
    }
}

openai_client = OpenAI()
memory = Memory.from_config(config)
```

Đặc điểm:

- Chỉ cấu hình LLM (OpenAI)
- Không có vector store → lưu trong memory tạm thời
- Phù hợp để test nhanh

---

### 2. Version 2: Supabase Integration (`v2-supabase-mem0.py`)

Thêm Supabase làm vector store:

```9:26:v2-supabase-mem0.py
config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": os.getenv('MODEL_CHOICE', 'gpt-4o-mini')
        }
    },
    "vector_store": {
        "provider": "supabase",
        "config": {
            "connection_string": os.environ['DATABASE_URL'],
            "collection_name": "memories"
        }
    }  
}

openai_client = OpenAI()
memory = Memory.from_config(config)
```

Đặc điểm:

- Thêm `vector_store` với provider `supabase`
- Lưu memories vào PostgreSQL (Supabase)
- Dữ liệu tồn tại lâu dài

---

### 3. Version 3: Streamlit Web App (`v3-streamlit-supabase-mem0.py`)

Phiên bản đầy đủ với UI và authentication:

#### a) Cấu hình Memory với Supabase:

```65:100:v3-streamlit-supabase-mem0.py
        # Tạo config cho Memory - loại bỏ create_collection
        config = {
            "llm": {
                "provider": "openai",
                "config": {
                    "model": MODEL_CHOICE
                }
            },
            "vector_store": {
                "provider": "supabase",
                "config": {
                    "connection_string": conn_str,
                    "collection_name": "memories_new",
                    "embedding_model_dims": 1536  # Số chiều của OpenAI text-embedding-ada-002
                }
            }  
        }
      
        # Thử tạo collection trước khi khởi tạo Memory
        try:
            import vecs
            db = vecs.create_client(conn_str)
            # Kiểm tra nếu collection đã tồn tại
            try:
                # Sử dụng get_or_create_collection thay vì create_collection
                db.get_or_create_collection(
                    name="memories_new",
                    dimension=1536
                )
                st.success("Collection đã được tạo/truy cập thành công!")
            except Exception as e:
                st.warning(f"Không thể tạo collection: {str(e)}")
        except Exception as e:
            st.warning(f"Không thể kết nối với vecs: {str(e)}")
      
        return Memory.from_config(config)
```

Điểm nổi bật:

- Tạo collection trước bằng `vecs` với `get_or_create_collection`
- Chỉ định `embedding_model_dims: 1536` (OpenAI ada-002)
- Xử lý timeout cho database connection
- Có fallback nếu khởi tạo thất bại

#### b) Workflow sử dụng Memory:

```166:203:v3-streamlit-supabase-mem0.py
def chat_with_memories(message, user_id):
    try:
        # Retrieve relevant memories
        with st.spinner("Searching memories..."):
            try:
                relevant_memories = memory.search(query=message, user_id=user_id, limit=3)
                memories_str = "\n".join(f"- {entry['memory']}" for entry in relevant_memories["results"])
            except Exception as e:
                st.error(f"Error retrieving memories: {str(e)}")
                memories_str = "(No memories available)"
      
        # Generate Assistant response
        system_prompt = f"You are a helpful AI assistant with memory. Answer the question based on the query and user's memories.\nUser Memories:\n{memories_str}"
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}]
      
        with st.spinner("Thinking..."):
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini", 
                    messages=messages,
                    timeout=60  # Increase timeout to 60 seconds
                )
                assistant_response = response.choices[0].message.content
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")
                return "I'm sorry, I couldn't generate a response at this time. Please try again later."

        # Create new memories from the conversation
        try:
            messages.append({"role": "assistant", "content": assistant_response})
            memory.add(messages, user_id=user_id)
        except Exception as e:
            st.warning(f"Could not save this conversation to memory: {str(e)}")

        return assistant_response
    except Exception as e:
        st.error(f"General error: {str(e)}")
        return "Sorry, an error occurred. Please try again later."
```

Quy trình:

1. Search: `memory.search(query, user_id, limit=3)` để lấy memories liên quan
2. Generate: Đưa memories vào system prompt, gọi OpenAI
3. Store: `memory.add(messages, user_id)` để lưu cuộc hội thoại

#### c) Quản lý Memory:

```276:281:v3-streamlit-supabase-mem0.py
            # Memory management options
            st.subheader("Memory Management")
            if st.button("Clear All Memories"):
                memory.clear(user_id=user.id)
                st.success("All memories cleared!")
                st.session_state.messages = []
                st.rerun()
```

---

### 4. Studio Integration Version (`studio-integration-version/`)

Tích hợp với Pydantic AI và FastAPI:

#### a) Agent với Pydantic AI:

```27:36:studio-integration-version/mem0_agent.py
mem0_agent = Agent(
    OpenAIModel(llm),
    system_prompt=f'You are a helpful AI. Answer the question based on query and memories. The current date is: {datetime.now().strftime("%Y-%m-%d")}',
    deps_type=Mem0Deps,
    retries=2
)

@mem0_agent.system_prompt  
def add_memories(ctx: RunContext[str]) -> str:
    return f"\nUser Memories:\n{ctx.deps.memories}"
```

#### b) FastAPI Endpoint với Memory:

```168:203:studio-integration-version/mem0_agent_endpoint.py
        # Retrieve relevant memories with Mem0
        try:
            relevant_memories = memory.search(query=request.query, user_id=request.user_id, limit=3)
            memories_str = "\n".join(f"- {entry['memory']}" for entry in relevant_memories["results"])
        except Exception as e:
            print(f"Error retrieving memories: {str(e)}")
            memories_str = "(No memories available)"

        # Initialize agent dependencies
        async with httpx.AsyncClient() as client:
            deps = Mem0Deps(
                memories=memories_str
            )

            # Run the agent with conversation history
            result = await mem0_agent.run(
                request.query,
                message_history=messages,
                deps=deps
            )

        # Store agent's response
        await store_message(
            session_id=request.session_id,
            message_type="ai",
            content=result.data,
            data={"request_id": request.request_id}
        )

        # Update memories based on the last user message and agent response
        try:
            memory_messages = [
                {"role": "user", "content": request.query},
                {"role": "assistant", "content": result.data}
            ]
            memory.add(memory_messages, user_id=request.user_id)      
        except Exception as e:
            print(f"Error adding memory: {str(e)}")
```

---

## Tóm tắt kiến trúc

### Các thành phần chính:

1. Memory Configuration:

   - LLM Provider: OpenAI (gpt-4o-mini)
   - Vector Store: Supabase (PostgreSQL + pgvector)
   - Collection: `memories_new` hoặc `memories_api_new`
   - Embedding: 1536 dimensions (OpenAI ada-002)
2. Memory Operations:

   - `memory.search(query, user_id, limit)`: Tìm kiếm memories
   - `memory.add(messages, user_id)`: Lưu cuộc hội thoại
   - `memory.clear(user_id)`: Xóa tất cả memories của user
3. User Isolation:

   - Mỗi user có `user_id` riêng
   - Memories được lọc theo `user_id` khi search
4. Error Handling:

   - Có fallback nếu Memory khởi tạo thất bại
   - Xử lý timeout cho database
   - Try-catch cho các operations

---

## Điểm mạnh của cách triển khai

1. Tách biệt theo user (`user_id`)
2. Lưu trữ lâu dài với Supabase
3. Tự động tạo collection nếu chưa có
4. Xử lý lỗi và fallback
5. Tích hợp với Streamlit và FastAPI

Bạn muốn tôi giải thích sâu hơn phần nào, hoặc đề xuất cải thiện?
