# SQLAgent API User Guide

## Overview
SQLAgent is a production-ready API that allows users to connect to their databases and ask natural language questions. It uses Redis for session management and provides isolated database connections for each user.

## Architecture Flow

```
User Request → Authentication → Session Management → Database Connection → AI Processing → Response
     ↓              ↓                ↓                    ↓                   ↓           ↓
 Bearer Token → JWT Validation → Redis Session → Cached DB Tools → LangGraph Agent → Natural Language
```

## Redis Integration

Redis is used for:
- **Session Storage**: Each user session is stored as a Redis hash
- **Connection Caching**: Database connection strings are cached per session
- **Schema Caching**: Database schemas are cached for faster SQL generation
- **Session Persistence**: Sessions persist across API calls

---

## API Endpoints Usage Guide

### 1. User Registration & Authentication

#### Register New User
```http
POST /users/
Content-Type: application/json

{
    "name": "John Doe",
    "email": "john@example.com", 
    "password": "securepassword"
}
```

**Response:**
```json
{
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2025-10-05T10:30:00"
}
```

#### Login
```http
POST /login
Content-Type: application/x-www-form-urlencoded

username=john@example.com&password=securepassword
```

**Response:**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer"
}
```

**Redis State After Login:**
```
Redis Key: session:a7b8c9d0-1234-5678-9abc-def012345678
Redis Value: {
    "user_id": 1,
    "created_at": "1728118200"
}
```

---

### 2. Database Management

#### Add Database Connection
```http
POST /databases/add_db_connection
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
    "db_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database_name": "ecommerce_db",
    "username": "db_user",
    "db_password": "db_pass123",
    "owner_id": 1
}
```

**Response:**
```json
{
    "message": "Database added successfully",
    "db_connection": {
        "id": 101,
        "db_type": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database_name": "ecommerce_db",
        "username": "db_user",
        "owner_id": 1,
        "created_at": "2025-10-05T10:35:00"
    }
}
```

#### Connect to Database
```http
POST /databases/connect_db/101
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Response:**
```json
{
    "message": "Database connection successful and tools updated",
    "session_id": "a7b8c9d0-1234-5678-9abc-def012345678",
    "thread_id": "a7b8c9d0-1234-5678-9abc-def012345678",
    "db_id": 101,
    "database_name": "ecommerce_db",
    "user_id": 1
}
```

**Redis State After Database Connection:**
```
Redis Key: session:a7b8c9d0-1234-5678-9abc-def012345678
Redis Value: {
    "connection_string": "postgresql+psycopg2://db_user:db_pass123@localhost:5432/ecommerce_db",
    "created_at": "1728118500",
    "status": "connected",
    "db_schema": "CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(100), email VARCHAR(100)); CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INTEGER, total DECIMAL(10,2), created_at TIMESTAMP);"
}
```

**Memory Cache State:**
```python
session_connectors = {
    "a7b8c9d0-1234-5678-9abc-def012345678": <DBConnector object to ecommerce_db>
}
```

#### Check Session Status
```http
GET /databases/session-status
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Response:**
```json
{
    "user_id": 1,
    "session_id": "a7b8c9d0-1234-5678-9abc-def012345678",
    "thread_id": "a7b8c9d0-1234-5678-9abc-def012345678", 
    "database_connected": true
}
```

---

### 3. AI-Powered Database Queries

#### Ask Natural Language Questions
```http
POST /ask
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
    "user_id": 1,
    "session_id": "a7b8c9d0-1234-5678-9abc-def012345678",
    "question": "Show me all users who placed orders in the last 30 days"
}
```

**Behind the Scenes Process:**

1. **Session Validation**: 
   - Check Redis: `session:a7b8c9d0-1234-5678-9abc-def012345678` exists
   - Validate user owns this session
   
2. **Database Tools Retrieval**:
   - Check memory cache: `session_connectors["a7b8c9d0-1234-5678-9abc-def012345678"]`
   - If cached: reuse existing connector ✅
   - If not cached: create new connector and cache it

3. **Schema Retrieval**:
   - Check Redis: `HGET session:a7b8c9d0-1234-5678-9abc-def012345678 db_schema`
   - Return cached schema for faster processing

4. **AI Processing**:
   - LangGraph agent uses session-specific tools
   - Generates SQL: `SELECT u.* FROM users u JOIN orders o ON u.id = o.user_id WHERE o.created_at > NOW() - INTERVAL '30 days'`
   - Executes query using cached database connector
   - Formats results in natural language

**Response:**
```json
"I found 15 users who placed orders in the last 30 days. Here are the results:

1. John Smith (john@email.com) - Last order: 2025-09-28
2. Mary Johnson (mary@email.com) - Last order: 2025-09-25
3. Robert Davis (robert@email.com) - Last order: 2025-09-22
...

These users have been active recently and might be good candidates for follow-up marketing campaigns."
```

---

### 4. Session Management

#### Get Detailed Session Info
```http
GET /databases/session-info/a7b8c9d0-1234-5678-9abc-def012345678
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Response:**
```json
{
    "session_id": "a7b8c9d0-1234-5678-9abc-def012345678",
    "thread_id": "a7b8c9d0-1234-5678-9abc-def012345678",
    "user_id": 1,
    "database_connected": true,
    "redis_data": {
        "connection_string": "postgresql+psycopg2://db_user:***@localhost:5432/ecommerce_db",
        "created_at": "1728118500",
        "status": "connected",
        "db_schema": "CREATE TABLE users..."
    },
    "db_session_created_at": "2025-10-05T10:40:00"
}
```

#### Disconnect Session
```http
POST /databases/disconnect-session
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Response:**
```json
{
    "message": "Session disconnected successfully",
    "session_id": "a7b8c9d0-1234-5678-9abc-def012345678",
    "thread_id": "a7b8c9d0-1234-5678-9abc-def012345678",
    "user_id": 1,
    "redis_cleanup": true
}
```

**Redis State After Disconnect:**
```
Redis Key: session:a7b8c9d0-1234-5678-9abc-def012345678 (DELETED)
```

**Memory Cache State After Disconnect:**
```python
session_connectors = {}  # Empty - connector removed
```

---

## Complete Workflow Example

### Scenario: E-commerce Business Owner Analyzing Sales Data

1. **User Registration & Login**
```bash
# Register
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Sarah Wilson","email":"sarah@shop.com","password":"secure123"}'

# Login  
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=sarah@shop.com&password=secure123'
```

2. **Add E-commerce Database**
```bash
curl -X POST http://localhost:8000/databases/add_db_connection \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "postgresql",
    "host": "db.myshop.com", 
    "port": 5432,
    "database_name": "ecommerce",
    "username": "shop_user",
    "db_password": "shop_pass",
    "owner_id": 2
  }'
```

3. **Connect to Database**
```bash
curl -X POST http://localhost:8000/databases/connect_db/102 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

4. **Ask Business Questions**
```bash
# Question 1: Revenue Analysis
curl -X POST http://localhost:8000/ask \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "session_id": "b8c9d0e1-2345-6789-abcd-ef0123456789",
    "question": "What was our total revenue last month?"
  }'

# Question 2: Top Products
curl -X POST http://localhost:8000/ask \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2, 
    "session_id": "b8c9d0e1-2345-6789-abcd-ef0123456789",
    "question": "Which products are selling the most this quarter?"
  }'

# Question 3: Customer Analysis  
curl -X POST http://localhost:8000/ask \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "session_id": "b8c9d0e1-2345-6789-abcd-ef0123456789", 
    "question": "Show me customers who haven't ordered in 3 months"
  }'
```

5. **Session Persistence Benefits**
   - Each question uses the same cached database connection
   - Schema is loaded once and reused
   - Conversation context is maintained via thread_id
   - No reconnection overhead between questions

---

## Redis Data Structure Reference

### Session Hash Structure
```
Key: session:{session_id}
Fields:
├── connection_string: "postgresql+psycopg2://user:pass@host:port/db"  
├── created_at: "1728118500"
├── status: "connected"
└── db_schema: "CREATE TABLE users (...); CREATE TABLE orders (...);"
```

### Session Expiration
- **Default TTL**: 24 hours (86400 seconds)
- **Auto-renewal**: On each API call
- **Manual cleanup**: Via `/databases/disconnect-session`

---

## Health Checks & Monitoring

### Basic Health Check
```http
GET /health
```

**Response:**
```json
{
    "status": "healthy",
    "message": "Service is up and running", 
    "timestamp": "2025-10-05T12:00:00.000Z",
    "version": "1.0.0",
    "redis": "healthy"
}
```

### Session-Aware Health Check
```http
GET /health/session
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
    "status": "healthy",
    "message": "Service is up and running",
    "user_id": 1,
    "session_id": "a7b8c9d0-1234-5678-9abc-def012345678",
    "thread_id": "a7b8c9d0-1234-5678-9abc-def012345678",
    "database_connected": true,
    "timestamp": "2025-10-05T12:00:00.000Z"
}
```

---

## Error Handling

### Common Error Responses

#### Invalid Session
```json
{
    "detail": "Session ID does not belong to the authenticated user or session not found"
}
```

#### Database Connection Failed
```json
{
    "detail": "No database connected for this session. Please connect a database first."
}
```

#### Redis Connection Issues
```json
{
    "status": "degraded",
    "message": "Service running but Redis unavailable",
    "redis": "unhealthy"
}
```

---

## Production Considerations

### Performance Optimizations
- **Connection Caching**: Database connectors are cached per session
- **Schema Caching**: Database schemas are cached in Redis 
- **Session Reuse**: Sessions persist across multiple API calls
- **Memory Management**: Automatic cleanup prevents memory leaks

### Scalability Features
- **Stateless Design**: All session state stored in Redis
- **Horizontal Scaling**: Multiple API instances can share Redis
- **Load Balancing**: Session affinity not required
- **Resource Isolation**: Each user gets their own database tools

### Security Features
- **JWT Authentication**: All endpoints require valid tokens
- **Session Validation**: Database ownership verified per request
- **Connection Isolation**: Users cannot access other users' databases
- **Automatic Cleanup**: Sessions expire and clean up resources

---

This architecture ensures a production-ready, scalable, and secure API for natural language database querying with proper session management and resource optimization.