# 1. Cài .env
python -m venv .venv
.venv/Scripts/activate

# Cài lib
pip install -e. 

# 2. Run Local Server
python -m uvicorn app.main:app --host 0.0.0.0 --port 30031 --reload
python -m uvicorn app.main:app --host 0.0.0.0 --port 30003 --reload

# Check Milvus 
```bash
Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.
Install the latest PowerShell for new features and improvements! https://aka.ms/PSWindows
PS C:\Users\User> Test-NetConnection -ComputerName 124.197.21.40 -Port 8000 -InformationLevel Detailed

ComputerName : 124.197.21.40
RemoteAddress : 124.197.21.40
Port         : 8000
Protocol     : TCP
TcpTestSucceeded : True
PingSucceeded : True
```

WEB_CONCURRENCY=4 \
gunicorn app.server:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 \
  --timeout 120 \
  --log-level info

# Run Worker
python -m deploy.worker_tools


# 3. Test API

# Health Check
curl -X GET "http://localhost:30031/api/v1/health" \
  -H "Content-Type: application/json"

# 1. Extract Facts API
curl -X POST "http://localhost:30031/api/v1/extract_facts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "conversation_id": "conv_456",
    "conversation": [
      {
        "role": "user",
        "content": "Tôi tên là Nguyễn Văn A, sống ở Hà Nội. Tôi thích đọc sách và chơi đàn guitar."
      },
      {
        "role": "assistant",
        "content": "Xin chào Nguyễn Văn A! Tôi đã ghi nhận thông tin của bạn."
      }
    ],
    "metadata": {
      "source": "test",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  }'


{
    "status": "success",
    "message": "Extracted 3 facts successfully",
    "data": {
        "facts_count": 3,
        "fact_ids": [
            "06d7f5c8-4cd3-464d-bba7-009bfd3f903e",
            "f51e02b3-e550-4453-bf8a-2672020f4b57",
            "0732b43b-bd05-4d89-bf36-fb964879f5c7"
        ],
        "facts": [
            {
                "id": "06d7f5c8-4cd3-464d-bba7-009bfd3f903e",
                "content": "Nguyễn Văn A lives in Hanoi.",
                "category": "relationship",
                "confidence": 1.0,
                "created_at": "2025-12-20T07:52:55.954358"
            },
            {
                "id": "f51e02b3-e550-4453-bf8a-2672020f4b57",
                "content": "Nguyễn Văn A likes reading books.",
                "category": "preference",
                "confidence": 1.0,
                "created_at": "2025-12-20T07:52:55.954358"
            },
            {
                "id": "0732b43b-bd05-4d89-bf36-fb964879f5c7",
                "content": "Nguyễn Văn A enjoys playing the guitar.",
                "category": "preference",
                "confidence": 1.0,
                "created_at": "2025-12-20T07:52:55.954358"
            }
        ]
    }
}

# 2. Search Facts API
curl -X POST "http://localhost:300  31/api/v1/search_facts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "query": "Người dùng thích gì?",
    "limit": 10,
    "score_threshold": 0.4
  }'

{
    "status": "success",
    "data": {
        "query": "Người dùng thích gì?",
        "results_count": 5,
        "results": [
            {
                "fact_id": "15483779-0043-42bc-8881-50226308bfda",
                "content": "Nguyễn Văn A thích chơi đàn guitar.",
                "category": "preference",
                "score": 0.6195762395858764,
                "created_at": "2025-12-20T01:02:52.502681+00:00",
                "related_facts": []
            },
            {
                "fact_id": "5f4a32b0-37e0-4003-9f66-736497237d6b",
                "content": "Nguyễn Văn A thích chơi đàn guitar.",
                "category": "preference",
                "score": 0.6195762395858764,
                "created_at": "2025-12-20T00:58:16.229158+00:00",
                "related_facts": []
            },
            {
                "fact_id": "07e90571-f7d4-49f9-93a5-12c0ef19b1e0",
                "content": "Nguyễn Văn A thích đọc sách.",
                "category": "preference",
                "score": 0.6179321557283401,
                "created_at": "2025-12-20T01:02:52.502681+00:00",
                "related_facts": []
            },
            {
                "fact_id": "a444bdee-4b63-40f5-b485-7907b0bb4325",
                "content": "Nguyễn Văn A thích đọc sách.",
                "category": "preference",
                "score": 0.6179321557283401,
                "created_at": "2025-12-20T00:58:16.229158+00:00",
                "related_facts": []
            },
            {
                "fact_id": "f51e02b3-e550-4453-bf8a-2672020f4b57",
                "content": "Nguyễn Văn A likes reading books.",
                "category": "preference",
                "score": 0.2810041785240173,
                "created_at": "2025-12-20T00:52:55.954358+00:00",
                "related_facts": []
            }
        ]
    }
}

