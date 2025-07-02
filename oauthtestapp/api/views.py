from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.socialaccount.models import SocialAccount, SocialToken
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from .serializers import UserSerializer, UserProfileSerializer
import json
import requests
import urllib.parse

User = get_user_model()

class UserCreate(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class UserDetail(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user

@api_view(['GET'])
@permission_classes([AllowAny])
def oauth_config_debug(request):
    """
    Debug endpoint to show current OAuth configuration.
    Visit this to check if your settings are correct.
    """
    return JsonResponse({
        "google_client_id": settings.GOOGLE_OAUTH_CLIENT_ID[:20] + "..." if settings.GOOGLE_OAUTH_CLIENT_ID else "NOT SET",
        "google_client_secret": "SET" if settings.GOOGLE_OAUTH_CLIENT_SECRET else "NOT SET",
        "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        "frontend_url": settings.FRONTEND_URL,
        "current_host": request.get_host(),
        "protocol": "https" if request.is_secure() else "http",
        "full_callback_url": f"{'https' if request.is_secure() else 'http'}://{request.get_host()}/api/auth/google/callback/",
        "instructions": {
            "1": "Add this redirect URI to Google Cloud Console:",
            "redirect_uri_for_google": settings.GOOGLE_OAUTH_REDIRECT_URI,
            "2": "Make sure your .env file has these variables set",
            "3": "Frontend should redirect to: /api/auth/google/login/"
        }
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def google_oauth_initiate(request):
    """
    Initiate Google OAuth flow - redirects to Google's authorization server.
    This is what your frontend should redirect to, not the /auth/google/ endpoint.
    """
    google_client_id = settings.GOOGLE_OAUTH_CLIENT_ID
    
    if not google_client_id:
        return JsonResponse({
            "error": "Google OAuth not configured. Please set GOOGLE_OAUTH_CLIENT_ID in environment."
        }, status=500)
    
    # Get redirect URI from settings (configurable)
    redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI
    
    # Google OAuth 2.0 authorization URL
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        'client_id': google_client_id,
        'redirect_uri': redirect_uri,
        'scope': 'email profile',
        'response_type': 'code',
        'access_type': 'online',
        'prompt': 'select_account'
    }
    
    auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@api_view(['POST'])
@permission_classes([AllowAny])
def google_oauth_login(request):
    """
    Handle Google OAuth login from frontend.
    This endpoint receives Google access token from your NextJS app.
    Expects: { "access_token": "google_access_token_from_frontend" }
    Returns: { "access_token": "jwt_token", "refresh_token": "refresh_token", "user": {...} }
    """
    try:
        data = json.loads(request.body)
        google_access_token = data.get('access_token')
        
        if not google_access_token:
            return JsonResponse({
                "error": "Google access token is required",
                "help": "Your frontend should get this token from Google OAuth and send it here"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify Google token and get user info
        google_user_info = get_google_user_info(google_access_token)
        if not google_user_info:
            return JsonResponse({
                "error": "Invalid Google access token"
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get or create user
        user = get_or_create_user_from_google(google_user_info)
        if not user:
            return JsonResponse({
                "error": "Failed to create or retrieve user"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Serialize user data
        user_serializer = UserProfileSerializer(user)
        
        return JsonResponse({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user_serializer.data,
            "message": "Login successful"
        }, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON format"
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return JsonResponse({
            "error": "An error occurred during authentication"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get current user profile data.
    Returns: { "user": {...} }
    """
    serializer = UserProfileSerializer(request.user)
    return Response({
        "user": serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user by blacklisting the refresh token.
    Expects: { "refresh_token": "refresh_token" }
    """
    try:
        data = json.loads(request.body)
        refresh_token = data.get('refresh_token')
        
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return JsonResponse({
            "message": "Logout successful"
        }, status=status.HTTP_200_OK)
        
    except Exception:
        return JsonResponse({
            "message": "Logout successful"
        }, status=status.HTTP_200_OK)

def get_google_user_info(access_token):
    """
    Get user information from Google using the access token.
    """
    try:
        response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        return None
        
    except requests.RequestException:
        return None

def get_or_create_user_from_google(google_user_info):
    """
    Get or create a user from Google user information.
    """
    try:
        email = google_user_info.get('email')
        first_name = google_user_info.get('given_name', '')
        last_name = google_user_info.get('family_name', '')
        google_id = google_user_info.get('id')
        
        if not email:
            return None
        
        # Try to get existing user by email
        try:
            user = User.objects.get(email=email)
            # Update user info if needed
            if not user.first_name and first_name:
                user.first_name = first_name
            if not user.last_name and last_name:
                user.last_name = last_name
            user.save()
            return user
        except User.DoesNotExist:
            pass
        
        # Create new user
        username = email.split('@')[0]
        # Ensure username is unique
        original_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create or update social account
        try:
            social_account, created = SocialAccount.objects.get_or_create(
                user=user,
                provider='google',
                defaults={'uid': google_id}
            )
            if not created and social_account.uid != google_id:
                social_account.uid = google_id
                social_account.save()
        except Exception:
            # If social account creation fails, still return the user
            pass
        
        return user
        
    except Exception:
        return None

# Google OAuth callback (handles redirect from Google)
@api_view(['GET'])
@permission_classes([AllowAny])
def google_oauth_callback(request):
    """
    Handle callback from Google OAuth.
    This receives the authorization code and exchanges it for tokens.
    """
    code = request.GET.get('code')
    
    if not code:
        error = request.GET.get('error', 'Unknown error')
        frontend_url = settings.FRONTEND_URL
        return redirect(f'{frontend_url}/auth/callback?error={error}')
    
    try:
        # Exchange code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            frontend_url = settings.FRONTEND_URL
            return redirect(f'{frontend_url}/auth/callback?error=token_exchange_failed')
        
        # Get user info
        google_user_info = get_google_user_info(token_json['access_token'])
        if not google_user_info:
            frontend_url = settings.FRONTEND_URL
            return redirect(f'{frontend_url}/auth/callback?error=user_info_failed')
        
        # Create/get user
        user = get_or_create_user_from_google(google_user_info)
        if not user:
            frontend_url = settings.FRONTEND_URL
            return redirect(f'{frontend_url}/auth/callback?error=user_creation_failed')
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Redirect to frontend with token
        frontend_url = settings.FRONTEND_URL
        return redirect(f'{frontend_url}/auth/callback?access_token={access_token}')
        
    except Exception as e:
        frontend_url = settings.FRONTEND_URL
        return redirect(f'{frontend_url}/auth/callback?error=authentication_failed')

# Legacy redirect view for allauth (if needed)
@login_required
def google_login_callback(request):
    """
    Legacy callback for allauth redirect flow.
    Redirects to frontend with error or success.
    """
    user = request.user
    
    try:
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Redirect to frontend with token
        frontend_url = settings.FRONTEND_URL
        return redirect(f'{frontend_url}/auth/callback?access_token={access_token}')
        
    except Exception:
        frontend_url = settings.FRONTEND_URL
        return redirect(f'{frontend_url}/auth/callback?error=authentication_failed')

@csrf_exempt
def validate_google_token(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            google_access_token = data.get('google_access_token')
            print("Google Access Token: ", google_access_token)
            
            if not google_access_token:
                return JsonResponse({"detail": "Google access token is missing"}, status=400)
            return JsonResponse({'valid': True})
        except json.JSONDecodeError:
            return JsonResponse({"detail": "Invalid JSON"}, status=400)
    return JsonResponse({"detail": "Invalid request method"}, status=405)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Simple health check endpoint
    """
    return JsonResponse({
        "status": "ok",
        "host": request.get_host(),
        "secure": request.is_secure(),
        "debug": settings.DEBUG,
        "allowed_hosts": settings.ALLOWED_HOSTS,
        "path": request.path,
        "method": request.method,
    })
