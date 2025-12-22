# API Test Commands - cURL

Các lệnh cURL để test PIKA Memory System API.

## Base URL

```bash
BASE_URL="http://localhost:30031"
# hoặc
BASE_URL="http://0.0.0.0:30031"
```

## 1. Health Check / API Info

### Get API Documentation
```bash
curl -X GET "${BASE_URL}/docs"
```

### Get OpenAPI Schema
```bash
curl -X GET "${BASE_URL}/openapi.json"
```

## 2. Search Facts

Tìm kiếm facts/memories từ conversation history.

### Basic Search
```bash
curl -X POST "${BASE_URL}/api/v1/search_facts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "query": "What do I like?",
    "limit": 10,
    "score_threshold": 0.4
  }'
```

### Search với conversation_id filter
```bash
curl -X POST "${BASE_URL}/api/v1/search_facts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "query": "user favorite movie",
    "conversation_id": "conv_001",
    "limit": 20,
    "score_threshold": 0.3
  }'
```

### Search user favorites (proactive cache query)
```bash
curl -X POST "${BASE_URL}/api/v1/search_facts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "query": "user favorite (movie, character, pet, activity, friend, music, travel, toy)",
    "limit": 50,
    "score_threshold": 0.4
  }'
```

### Pretty print response
```bash
curl -X POST "${BASE_URL}/api/v1/search_facts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "query": "What are my preferences?",
    "limit": 10
  }' | python -m json.tool
```

## 3. Extract Facts (Async)

Extract facts từ conversation, trả về job_id để poll status.

### Basic Extract
```bash
curl -X POST "${BASE_URL}/api/v1/extract_facts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "conversation_id": "conv_001",
    "conversation": [
      {
        "role": "user",
        "content": "I love pizza and my favorite movie is The Matrix. I have a dog named Max."
      },
      {
        "role": "assistant",
        "content": "That sounds great! Pizza is delicious and The Matrix is a classic."
      }
    ],
    "metadata": {
      "source": "chat",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  }'
```

### Extract với nhiều conversation turns
```bash
curl -X POST "${BASE_URL}/api/v1/extract_facts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "conversation_id": "conv_002",
    "conversation": [
      {
        "role": "user",
        "content": "I like traveling to Japan. My favorite food is sushi."
      },
      {
        "role": "assistant",
        "content": "Japan is beautiful! Have you been to Tokyo?"
      },
      {
        "role": "user",
        "content": "Yes, I visited Tokyo last year. I also love anime."
      },
      {
        "role": "assistant",
        "content": "That is awesome! What is your favorite anime?"
      },
      {
        "role": "user",
        "content": "I really like Studio Ghibli movies, especially Spirited Away."
      }
    ],
    "metadata": {}
  }'
```

### Response sẽ có dạng:
```json
{
  "status": "accepted",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status_url": "/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/status"
}
```

## 4. Get Job Status

Poll job status để xem kết quả extraction.

### Get Job Status
```bash
# Thay {job_id} bằng job_id từ extract_facts response
JOB_ID="550e8400-e29b-41d4-a716-446655440000"

curl -X GET "${BASE_URL}/api/v1/jobs/${JOB_ID}/status"
```

### Poll job status với retry (bash script)
```bash
#!/bin/bash
JOB_ID="550e8400-e29b-41d4-a716-446655440000"
BASE_URL="http://localhost:30031"

while true; do
  STATUS=$(curl -s -X GET "${BASE_URL}/api/v1/jobs/${JOB_ID}/status" | python -c "import sys, json; print(json.load(sys.stdin)['status'])")
  echo "Job status: $STATUS"
  
  if [ "$STATUS" == "completed" ] || [ "$STATUS" == "failed" ]; then
    curl -s -X GET "${BASE_URL}/api/v1/jobs/${JOB_ID}/status" | python -m json.tool
    break
  fi
  
  sleep 2
done
```

### Pretty print job status
```bash
curl -X GET "${BASE_URL}/api/v1/jobs/${JOB_ID}/status" | python -m json.tool
```

## 5. Test Workflow (End-to-End)

### Step 1: Extract facts từ conversation
```bash
RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/extract_facts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "conversation_id": "conv_test_001",
    "conversation": [
      {
        "role": "user",
        "content": "I love pizza, especially margherita. My favorite movie is Inception. I have a golden retriever named Buddy."
      },
      {
        "role": "assistant",
        "content": "That is wonderful! Pizza and dogs are great."
      }
    ]
  }')

echo $RESPONSE | python -m json.tool
```

### Step 2: Extract job_id từ response
```bash
JOB_ID=$(echo $RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo "Job ID: $JOB_ID"
```

### Step 3: Poll job status
```bash
curl -X GET "${BASE_URL}/api/v1/jobs/${JOB_ID}/status" | python -m json.tool
```

### Step 4: Search facts sau khi extraction hoàn thành
```bash
curl -X POST "${BASE_URL}/api/v1/search_facts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "query": "What do I like?",
    "limit": 10
  }' | python -m json.tool
```

## 6. Test với PowerShell (Windows)

### Search Facts
```powershell
$baseUrl = "http://localhost:30031"
$body = @{
    user_id = "user_123"
    query = "What do I like?"
    limit = 10
    score_threshold = 0.4
} | ConvertTo-Json

Invoke-RestMethod -Uri "$baseUrl/api/v1/search_facts" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

### Extract Facts
```powershell
$baseUrl = "http://localhost:30031"
$body = @{
    user_id = "user_123"
    conversation_id = "conv_001"
    conversation = @(
        @{
            role = "user"
            content = "I love pizza and dogs"
        },
        @{
            role = "assistant"
            content = "That's great!"
        }
    )
    metadata = @{}
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod -Uri "$baseUrl/api/v1/extract_facts" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

$jobId = $response.job_id
Write-Host "Job ID: $jobId"
```

### Get Job Status
```powershell
$baseUrl = "http://localhost:30031"
$jobId = "550e8400-e29b-41d4-a716-446655440000"

Invoke-RestMethod -Uri "$baseUrl/api/v1/jobs/$jobId/status" `
    -Method GET
```

## 7. Test Performance

### Search với timing
```bash
time curl -X POST "${BASE_URL}/api/v1/search_facts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "query": "user favorite",
    "limit": 20
  }'
```

### Multiple concurrent searches
```bash
for i in {1..10}; do
  curl -X POST "${BASE_URL}/api/v1/search_facts" \
    -H "Content-Type: application/json" \
    -d "{
      \"user_id\": \"user_123\",
      \"query\": \"test query $i\",
      \"limit\": 10
    }" &
done
wait
```

## 8. Error Cases

### Missing required field
```bash
curl -X POST "${BASE_URL}/api/v1/search_facts" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test"
  }'
# Expected: 422 Validation Error
```

### Invalid job_id
```bash
curl -X GET "${BASE_URL}/api/v1/jobs/invalid_job_id/status"
# Expected: 404 Not Found
```

### Invalid score_threshold
```bash
curl -X POST "${BASE_URL}/api/v1/search_facts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "query": "test",
    "score_threshold": 1.5
  }'
# Expected: 422 Validation Error
```

## 9. Response Examples

### Search Response
```json
{
  "status": "ok",
  "count": 2,
  "facts": [
    {
      "id": "mem_001",
      "score": 0.95,
      "source": "conversation",
      "user_id": "user_123",
      "conversation_id": "conv_001",
      "fact_type": ["preference", "food"],
      "fact_value": "I like pizza",
      "metadata": {
        "created_at": "2024-01-15T10:30:00Z",
        "categories": ["preference", "food"]
      }
    }
  ]
}
```

### Extract Response (202 Accepted)
```json
{
  "status": "accepted",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status_url": "/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/status"
}
```

### Job Status Response
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "current_step": "finished",
  "data": {
    "extracted_facts": 3,
    "memories_created": 3
  },
  "error": null
}
```

## Notes

- Tất cả endpoints yêu cầu `Content-Type: application/json`
- Search endpoint sử dụng 5-layer caching (L0 → L1 → L2 → L3 → L4)
- Extract endpoint là async, trả về job_id để poll status
- Job status có thể là: `pending`, `processing`, `completed`, `failed`
- Default port: `30031` (có thể thay đổi trong config)

