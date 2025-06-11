# Authentication System Documentation

## Overview

This FastAPI backend implements a complete JWT-based authentication system with the following features:

- **User Registration** with password strength validation
- **User Login** with JWT token generation
- **Password Hashing** using bcrypt
- **Protected Routes** with JWT token validation
- **User Plans** with file upload limits
- **Environment-based Configuration**

## API Endpoints

### Authentication Endpoints

#### POST `/auth/register`
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Password Requirements:**
- At least 8 characters long
- Contains at least one uppercase letter
- Contains at least one lowercase letter
- Contains at least one digit
- Contains at least one special character

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "plan_id": 1
}
```

#### POST `/auth/login`
Login with existing credentials.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### GET `/auth/me`
Get current user profile (requires authentication).

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "plan_id": 1
}
```

#### POST `/auth/refresh`
Refresh JWT token (requires authentication).

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### POST `/auth/logout`
Logout user (client should discard token).

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

## Environment Variables

Configure these environment variables in your `.env` file:

```bash
# JWT Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/postgres
DATABASE_URL_SYNC=postgresql://postgres:postgres@db:5432/postgres
```

## Security Features

### Password Hashing
- Uses bcrypt with automatic salt generation
- Passwords are never stored in plain text
- Secure password verification

### JWT Tokens
- Signed with HS256 algorithm
- Configurable expiration time
- Includes user email in token payload
- Bearer token authentication

### Password Validation
- Minimum 8 characters
- Must contain uppercase, lowercase, digit, and special character
- Real-time validation with descriptive error messages

## Database Models

### User Model
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True)
```

### Plan Model
```python
class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    max_files = Column(Integer, nullable=False, default=10)
```

## Usage Examples

### Frontend Integration (JavaScript)

```javascript
// Register a new user
const registerUser = async (email, password) => {
  const response = await fetch('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  return response.json();
};

// Login user
const loginUser = async (email, password) => {
  const response = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  return data;
};

// Make authenticated request
const getProfile = async () => {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/auth/me', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
};
```

### Python Client Example

```python
import requests

# Register and login
register_data = {"email": "test@example.com", "password": "TestPass123!"}
response = requests.post("http://localhost:8000/auth/register", json=register_data)

login_data = {"email": "test@example.com", "password": "TestPass123!"}
response = requests.post("http://localhost:8000/auth/login", json=login_data)
token = response.json()["access_token"]

# Use token for authenticated requests
headers = {"Authorization": f"Bearer {token}"}
profile = requests.get("http://localhost:8000/auth/me", headers=headers)
```

## Testing

Run the authentication test script:

```bash
cd backend
python test_auth.py
```

This will test:
- User registration
- User login
- Protected endpoint access
- Password validation

## Default Users

The system creates a default admin user:
- **Email:** admin@example.com
- **Password:** admin123!

## Plan Management

Users are automatically assigned to the "Free" plan upon registration:
- **Free Plan:** 5 file uploads maximum
- **Premium Plan:** 100 file uploads maximum

## Error Handling

The authentication system provides detailed error messages:

- `400 Bad Request`: Email already registered
- `401 Unauthorized`: Invalid credentials or token
- `422 Unprocessable Entity`: Password validation failed
- `500 Internal Server Error`: Server-side errors

## Integration with Other Services

### File Upload Service
Protected file upload endpoints automatically:
- Verify user authentication
- Check plan limits
- Associate files with user accounts

### GPT Service
Protected GPT endpoints:
- Require user authentication
- Track usage per user
- Store results linked to user files

## Security Best Practices

1. **Change default JWT secret** in production
2. **Use environment variables** for sensitive configuration
3. **Implement rate limiting** for auth endpoints
4. **Use HTTPS** in production
5. **Regularly rotate JWT secrets**
6. **Monitor failed login attempts**
7. **Implement account lockout** after multiple failures

## Troubleshooting

### Common Issues

1. **Import errors**: Dependencies not installed in container
2. **Database connection**: Check DATABASE_URL configuration
3. **JWT errors**: Verify JWT_SECRET_KEY is set
4. **Password validation**: Check password meets all requirements

### Debug Mode

Set `ENVIRONMENT=development` to enable:
- Detailed error messages
- SQL query logging
- Extended CORS origins
