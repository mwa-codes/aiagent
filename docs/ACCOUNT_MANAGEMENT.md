# Account Management API Documentation

## Overview

The Account Management API provides comprehensive user profile and account management functionality for authenticated users. It follows FastAPI best practices with proper Pydantic validation, email uniqueness enforcement, and security measures.

## API Endpoints

### User Profile Management

#### GET `/users/me`
Get current authenticated user's basic profile.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "plan_id": 1
}
```

#### GET `/users/me/profile`
Get detailed user profile with plan information and usage stats.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "plan_id": 1,
  "plan_name": "Free",
  "max_files": 5,
  "current_files_count": 2
}
```

#### PUT `/users/me`
Update user profile (email and/or password).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "current_password": "current_password",
  "new_password": "NewSecurePass123!"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "newemail@example.com",
  "plan_id": 1
}
```

**Validation Rules:**
- Email must be unique across all users
- Current password required when changing password
- New password must meet strength requirements
- New password must be different from current password

### Password Management

#### PUT `/users/me/password`
Change user password with current password verification.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewSecurePass123!"
}
```

**Response:**
```json
{
  "message": "Password updated successfully"
}
```

**Password Requirements:**
- At least 8 characters long
- Contains at least one uppercase letter
- Contains at least one lowercase letter
- Contains at least one digit
- Contains at least one special character
- Must be different from current password

### Email Management

#### PUT `/users/me/email`
Change user email address with password verification.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "new_email": "newemail@example.com",
  "password": "current_password"
}
```

**Response:**
```json
{
  "message": "Email updated successfully",
  "old_email": "oldemail@example.com",
  "new_email": "newemail@example.com"
}
```

**Validation Rules:**
- New email must be unique across all users
- Password verification required
- New email must be different from current email
- Email format validation enforced

### Usage Statistics

#### GET `/users/me/usage`
Get user's current usage statistics and plan limits.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "current_files": 2,
  "max_files": 5,
  "usage_percentage": 40.0,
  "plan_name": "Free",
  "can_upload": true
}
```

#### GET `/users/me/activity`
Get user's recent account activity.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "user_id": 1,
  "email": "user@example.com",
  "plan": "Free",
  "recent_files": [
    {
      "id": 1,
      "filename": "document.pdf",
      "upload_date": "2025-06-11T10:30:00Z",
      "summary": "Document summary"
    }
  ]
}
```

### Account Deactivation

#### DELETE `/users/me/deactivate`
Deactivate user account (removes all user data).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "password": "current_password",
  "confirmation": "DELETE"
}
```

**Response:**
```json
{
  "message": "Account deactivated successfully",
  "warning": "All user data has been removed"
}
```

**Important Notes:**
- This action is irreversible
- All user files and data will be deleted
- User must type "DELETE" exactly to confirm
- Password verification required

## Pydantic Schemas

### UserUpdate
```python
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None
```

### PasswordChange
```python
class PasswordChange(BaseModel):
    current_password: str
    new_password: str
```

### EmailUpdate
```python
class EmailUpdate(BaseModel):
    new_email: EmailStr
    password: str
```

### AccountDeactivation
```python
class AccountDeactivation(BaseModel):
    password: str
    confirmation: str = "DELETE"
```

## Security Features

### Email Uniqueness
- Database-level unique constraint on email field
- API-level validation prevents duplicate emails
- Proper error messages for email conflicts

### Password Security
- Bcrypt hashing with automatic salt generation
- Password strength validation with multiple criteria
- Current password verification for sensitive operations
- Protection against password reuse

### Authentication
- JWT Bearer token authentication required for all endpoints
- Token validation on every request
- Proper HTTP status codes for unauthorized access

### Input Validation
- Pydantic models with comprehensive validation
- Email format validation using EmailStr
- Password strength requirements enforced
- Confirmation requirements for destructive operations

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Email already registered by another user"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "new_password"],
      "msg": "Password must contain at least one uppercase letter",
      "type": "value_error"
    }
  ]
}
```

## Usage Examples

### JavaScript/TypeScript Frontend

```javascript
// Get user profile
const getProfile = async (token) => {
  const response = await fetch('/users/me/profile', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
};

// Update email
const updateEmail = async (token, newEmail, password) => {
  const response = await fetch('/users/me/email', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      new_email: newEmail,
      password: password
    })
  });
  return response.json();
};

// Change password
const changePassword = async (token, currentPassword, newPassword) => {
  const response = await fetch('/users/me/password', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword
    })
  });
  return response.json();
};
```

### Python Client

```python
import requests

class AccountManager:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def get_profile(self):
        response = requests.get(f"{self.base_url}/users/me/profile", headers=self.headers)
        return response.json()
    
    def update_email(self, new_email, password):
        data = {"new_email": new_email, "password": password}
        response = requests.put(f"{self.base_url}/users/me/email", json=data, headers=self.headers)
        return response.json()
    
    def change_password(self, current_password, new_password):
        data = {"current_password": current_password, "new_password": new_password}
        response = requests.put(f"{self.base_url}/users/me/password", json=data, headers=self.headers)
        return response.json()
    
    def get_usage_stats(self):
        response = requests.get(f"{self.base_url}/users/me/usage", headers=self.headers)
        return response.json()
```

## Testing

Run the comprehensive test suite:

```bash
cd backend
python test_account_management.py
```

The test script validates:
- Profile retrieval and updates
- Email change functionality
- Password change functionality
- Usage statistics
- Input validation
- Error handling
- Authentication requirements

## Integration with Frontend

The account management API integrates seamlessly with frontend frameworks:

1. **Profile Pages**: Display user information and usage stats
2. **Settings Pages**: Allow users to update email and password
3. **Account Security**: Provide password change functionality
4. **Usage Dashboards**: Show file usage and plan limits
5. **Account Deletion**: Provide secure account deactivation

## Best Practices

1. **Always validate user input** using Pydantic schemas
2. **Require password confirmation** for sensitive operations
3. **Use proper HTTP status codes** for different error conditions
4. **Implement proper logging** for security events
5. **Rate limit** password change attempts
6. **Send email notifications** for important account changes
7. **Provide clear error messages** for validation failures

## Security Considerations

1. **Password Verification**: Always verify current password before changes
2. **Email Uniqueness**: Enforce unique emails across the platform
3. **Token Validation**: Validate JWT tokens on every request
4. **Input Sanitization**: Use Pydantic for automatic input validation
5. **Audit Logging**: Log important account changes for security monitoring
6. **Rate Limiting**: Implement rate limiting for sensitive endpoints
7. **HTTPS Only**: Ensure all account management endpoints use HTTPS in production
