# Bizify — Error Handling & Standard Responses

Bizify relies on FastAPI's built-in exception handling along with consistent standard HTTP status codes to ensure that API consumers (like the frontend application) can predict and handle errors gracefully.

## 1. Standard HTTP Status Codes

The API uses standard RESTful HTTP status codes to indicate the success or failure of an API request:

| Status Code | Meaning | Typical Usage in Bizify |
|---|---|---|
| **200 OK** | Success | Successful `GET`, `PATCH`, `PUT`, or `POST` (when not creating a resource). |
| **201 Created** | Created | Successful `POST` resulting in a new resource (e.g., `POST /ideas/`). |
| **204 No Content** | Success (No Body) | Successful `DELETE` operation where no data is returned. |
| **400 Bad Request** | Client Error | Invalid business logic (e.g., "Email already registered", "Password mismatch", "Insufficient funds"). |
| **401 Unauthorized** | Auth Error | Missing JWT token, invalid token, blacklisted token, or session expired. |
| **403 Forbidden** | Permission Error | User is authenticated but lacks required role or ownership (e.g., trying to edit an idea owned by another user, or accessing an admin route). |
| **404 Not Found** | Resource Missing | The requested record (idea, group, document) does not exist in the database. |
| **422 Unprocessable Entity**| Validation Error | The JSON payload structure is incorrect, or a field failed Pydantic validation (e.g., invalid email format, missing required field). |
| **500 Internal Server Error**| Server Error | An unhandled exception occurred within the application. |

---

## 2. Standard Error Response Format

Whenever an error occurs (400, 401, 403, 404), Bizify raises an `HTTPException` which standardizes the response body into a predictable JSON object containing a `detail` key.

### Example: Business Logic Error (400 Bad Request)
```json
{
  "detail": "Email already registered."
}
```

### Example: Not Found (404 Not Found)
```json
{
  "detail": "Group not found or access denied."
}
```

---

## 3. Validation Errors (422 Unprocessable Entity)

FastAPI automatically handles payload validation using **Pydantic** schemas. If the frontend sends an invalid payload, the server intercepts it before reaching the service layer and returns a `422` error detailing exactly which fields failed.

### Example: Validation Error Payload
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    },
    {
      "loc": ["body", "password"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```
*Frontend Tip: You can parse the `loc` array to show validation errors directly under specific input fields.*

---

## 4. Custom Error Handling

In the service layer, exceptions are caught and translated into human-readable HTTP errors. 

For example, in `auth_service.py` during login:
```python
if not verify_password(password, user.password_hash):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Incorrect email or password"
    )
```

In cases of unexpected internal crashes, the global exception handler returns a generic `500 Internal Server Error` to avoid exposing sensitive traceback information to the end-user.
