# Django Google OAuth API

A production-ready Django REST API with Google OAuth authentication for NextJS frontend integration.

## Features

-   Google OAuth 2.0 authentication
-   JWT token-based authentication with refresh tokens
-   Production-ready configuration with environment variables
-   CORS support for frontend integration
-   User profile management
-   Secure token blacklisting for logout

## Quick Setup

### 1. Install Dependencies

```bash
pipenv install
pipenv shell
```

### 2. Environment Variables

Create a `.env` file in your project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Frontend Configuration
FRONTEND_URL=http://localhost:3000

# Google OAuth (Get from Google Cloud Console)
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
```

### 3. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials:
    - Application type: Web application
    - Authorized redirect URIs:
        - `http://localhost:8000/accounts/google/login/callback/` (for development)
        - `https://yourdomain.com/accounts/google/login/callback/` (for production)

### 4. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Optional: for admin access
```

### 5. Run Development Server

```bash
python manage.py runserver
```

## API Endpoints

### Authentication

#### Google OAuth Login

```http
POST /api/auth/google/
Content-Type: application/json

{
  "access_token": "google_access_token_from_frontend"
}
```

**Response:**

```json
{
    "access_token": "jwt_access_token",
    "refresh_token": "jwt_refresh_token",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "username": "john"
    },
    "message": "Login successful"
}
```

#### Get User Profile

```http
GET /api/auth/profile/
Authorization: Bearer jwt_access_token
```

#### Logout

```http
POST /api/auth/logout/
Authorization: Bearer jwt_access_token
Content-Type: application/json

{
  "refresh_token": "jwt_refresh_token"
}
```

### User Management

#### Get Current User

```http
GET /api/users/me/
Authorization: Bearer jwt_access_token
```

#### Create User (Manual Registration)

```http
POST /api/users/create/
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe"
}
```

## Frontend Integration (NextJS)

### 1. Install Google OAuth Library

```bash
npm install @google-cloud/oauth2
# or
npm install react-google-login
```

### 2. Frontend Implementation Example

```javascript
// Login component
import { GoogleLogin } from "react-google-login";

const handleGoogleLogin = async (googleResponse) => {
    try {
        const response = await fetch("http://localhost:8000/api/auth/google/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                access_token: googleResponse.accessToken,
            }),
        });

        const data = await response.json();

        if (response.ok) {
            // Store tokens in localStorage or secure cookie
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("refresh_token", data.refresh_token);
            localStorage.setItem("user", JSON.stringify(data.user));

            // Redirect to dashboard
            router.push("/dashboard");
        } else {
            console.error("Login failed:", data.error);
        }
    } catch (error) {
        console.error("Login error:", error);
    }
};

return (
    <GoogleLogin
        clientId="your-google-client-id"
        onSuccess={handleGoogleLogin}
        onFailure={(error) => console.log("Google login failed:", error)}
        cookiePolicy={"single_host_origin"}
    />
);
```

### 3. API Requests with JWT

```javascript
// API utility
const apiCall = async (endpoint, options = {}) => {
    const token = localStorage.getItem("access_token");

    const response = await fetch(`http://localhost:8000/api${endpoint}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
            ...options.headers,
        },
    });

    if (response.status === 401) {
        // Token expired, redirect to login
        localStorage.clear();
        window.location.href = "/login";
    }

    return response.json();
};

// Usage
const getUserProfile = () => apiCall("/auth/profile/");
```

## Production Deployment

### Environment Variables for Production

```env
SECRET_KEY=your-very-secure-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
FRONTEND_URL=https://yourfrontend.com
GOOGLE_OAUTH_CLIENT_ID=your-production-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-production-google-client-secret
```

### Security Considerations

1. **HTTPS**: Always use HTTPS in production
2. **Secret Key**: Use a strong, unique secret key
3. **CORS**: Configure specific allowed origins instead of allowing all
4. **Database**: Use PostgreSQL or similar for production
5. **Environment Variables**: Never commit secrets to version control

### Database Migration for Production

```bash
python manage.py collectstatic
python manage.py migrate
```

## Error Handling

The API returns consistent error responses:

```json
{
    "error": "Error description",
    "detail": "Additional details (optional)"
}
```

Common HTTP status codes:

-   `200`: Success
-   `400`: Bad Request (invalid data)
-   `401`: Unauthorized (invalid token)
-   `403`: Forbidden (insufficient permissions)
-   `500`: Internal Server Error

## Development Notes

-   JWT tokens expire after 60 minutes (configurable)
-   Refresh tokens expire after 7 days (configurable)
-   Users are created automatically on first Google login
-   Email addresses must be unique
-   The API handles duplicate usernames automatically

## Support

For issues or questions, check the Django and DRF documentation:

-   [Django Documentation](https://docs.djangoproject.com/)
-   [Django REST Framework](https://www.django-rest-framework.org/)
-   [django-allauth](https://django-allauth.readthedocs.io/)
