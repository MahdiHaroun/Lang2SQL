# Session-Based Database Connection API Usage

## Overview
The SQLAgent API now supports session-based database connections, ensuring that each user has their own isolated database connection and conversation thread.

## Key Changes
1. **Unified Session/Thread ID**: Each user gets a unique UUID that serves as both session_id and thread_id
2. **User Isolation**: Database connections are now tied to specific users and sessions
3. **Security**: Users can only access their own database connections
4. **Conversation Continuity**: The session UUID maintains conversation memory across requests

## API Endpoints

### Authentication Required
All database-related endpoints now require authentication via Bearer token.

### 1. Get Session Status
```http
GET /databases/session-status
Authorization: Bearer <your_token>
```
Returns current user session information and database connection status.

### 2. Add Database Connection
```http
POST /databases/add_db_connection
Authorization: Bearer <your_token>
Content-Type: application/json

{
    "db_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database_name": "mydb",
    "username": "myuser",
    "db_password": "mypassword",
    "owner_id": 1  // This will be automatically set to current user
}
```

### 3. Connect to Database
```http
POST /databases/connect_db/{db_id}
Authorization: Bearer <your_token>
```
Connects the database to your current session. Returns session_id for reference.

### 4. Get User's Databases
```http
GET /databases
Authorization: Bearer <your_token>
```
Returns all database connections owned by the current user.

### 5. Ask Questions
```http
POST /ask
Authorization: Bearer <your_token>
Content-Type: application/json

{
    "question": "Show me all users in the database"
    // Note: thread_id is automatically set to your session_id (UUID)
    // No need to specify thread_id as it's handled by the session system
}
```

### 6. Disconnect Session
```http
POST /databases/disconnect-session
Authorization: Bearer <your_token>
```
Disconnects database and cleans up session resources.

### 7. Health Check with Session
```http
GET /health/session
Authorization: Bearer <your_token>
```
Returns service health along with current session information.

## Workflow Example

1. **Login/Register** to get authentication token
2. **Check Session Status** to see current session
3. **Add Database Connection** (if not already added)
4. **Connect to Database** using the database ID
5. **Ask Questions** - each question will use your session's database connection
6. **Disconnect** when done (optional - sessions persist)

## Session Management

- **Session Creation**: Automatically created on first authenticated request with a UUID
- **Session Persistence**: Sessions persist until explicitly disconnected
- **Session Isolation**: Each session has its own database connection and conversation memory
- **Unified ID**: Session ID (UUID) serves as both session identifier and conversation thread ID
- **Thread Continuity**: The same UUID maintains conversation context across all requests

## Benefits

1. **Multi-User Support**: Multiple users can connect to different databases simultaneously
2. **Conversation Memory**: Each session maintains its own conversation history
3. **Security**: Users can only access their own database connections
4. **Resource Management**: Sessions can be disconnected to free up resources
5. **Thread Safety**: No conflicts between different user sessions

## Migration from Previous Version

If you were using the old API:
1. Add authentication to all requests
2. Use `/databases` instead of `/databases/{user_id}`
3. The `/connect_db/{db_id}` endpoint now returns session information
4. All questions are automatically tied to your session's database connection