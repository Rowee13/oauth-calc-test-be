from django.urls import path
from . import views

urlpatterns = [
    # Authentication endpoints
    path('auth/google/', views.google_oauth_login, name='google_oauth_login'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/profile/', views.user_profile, name='user_profile'),
    
    # User management
    path('users/create/', views.UserCreate.as_view(), name='user_create'),
    path('users/me/', views.UserDetail.as_view(), name='user_detail'),
    
    # Legacy callback (if using allauth redirect flow)
    path('auth/google/callback/', views.google_login_callback, name='google_login_callback'),
] 