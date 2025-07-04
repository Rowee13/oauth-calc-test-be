from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # Debug endpoint
    path('auth/debug/', views.oauth_config_debug, name='oauth_config_debug'),  # Debug OAuth config
    
    # Google OAuth endpoints
    path('auth/google/login/', views.google_oauth_initiate, name='google_oauth_initiate'),  # NEW: Start OAuth flow
    path('auth/google/callback/', views.google_oauth_callback, name='google_oauth_callback'),  # Handle Google redirect
    path('auth/google/', views.google_oauth_login, name='google_oauth_login'),  # API endpoint for frontend
    
    # Other auth endpoints
    path('auth/logout/', views.logout, name='logout'),
    path('auth/profile/', views.user_profile, name='user_profile'),
    
    # User management
    path('users/create/', views.UserCreate.as_view(), name='user_create'),
    path('users/me/', views.UserDetail.as_view(), name='user_detail'),
    
    # Conversion endpoints
    path('conversions/convert/', views.convert_meters_to_feet, name='convert_meters_to_feet'),
    path('conversions/history/', views.conversion_history, name='conversion_history'),
    path('conversions/stats/', views.conversion_stats, name='conversion_stats'),
] 