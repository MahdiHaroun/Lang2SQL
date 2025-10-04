# Updated API Usage with Session Validation

## New /ask endpoint behavior

The `/ask` endpoint now requires both `user_id` and `session_id` in the payload and validates session ownership from the database.

### Request Format
```json
{
    "user_id": 1,
    "session_id": "593fc196-120e-48f7-ab79-1719eb0ee690",
    "question": "tell me what is my database about ?"
}
```

### Validation Process
1. **Authentication**: Bearer token is validated to get the authenticated user
2. **User ID Check**: `user_id` in payload must match the authenticated user's ID
3. **Session Ownership**: The `session_id` is validated against the database to ensure it belongs to the authenticated user
4. **Execution**: Only if both validations pass, the question is processed using the specified session

### Error Cases
- **403 Forbidden**: "User ID in payload does not match authenticated user"
- **403 Forbidden**: "Session ID does not belong to the authenticated user or session not found"

### Benefits
- **Explicit Session Control**: Users can specify exactly which session/thread to use
- **Database Validation**: Session ownership is verified against the database, not just token claims
- **Multi-Session Support**: Users can maintain multiple conversation threads
- **Security**: Prevents session hijacking by validating ownership in the database

### Complete Workflow Example

1. **Get your user ID and session ID from session status:**
```http
GET /databases/session-status
Authorization: Bearer <your_token>
```

Response:
```json
{
    "user_id": 1,
    "session_id": "593fc196-120e-48f7-ab79-1719eb0ee690",
    "database_connected": true
}
```

2. **Use these values in your /ask request:**
```http
POST /ask
Authorization: Bearer <your_token>
Content-Type: application/json

{
    "user_id": 1,
    "session_id": "593fc196-120e-48f7-ab79-1719eb0ee690", 
    "question": "tell me what is my database about ?"
}
```

### Session Management
- Each session ID is a unique UUID
- Session ID serves as both session identifier and conversation thread ID
- Sessions persist until explicitly disconnected
- Users can have multiple active sessions
- Each session can have its own database connection