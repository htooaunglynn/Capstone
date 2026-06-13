from django.urls import path

from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('accounts/login/', views.PlannerLoginView.as_view(), name='login'),
    path('accounts/logout/', views.logout_page, name='logout'),
    path('accounts/register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/auth/register/', views.AuthRegisterAPIView.as_view(), name='api_auth_register'),
    path('api/auth/login/', views.AuthLoginAPIView.as_view(), name='api_auth_login'),
    path('api/auth/refresh/', views.AuthRefreshAPIView.as_view(), name='api_auth_refresh'),
    path('api/auth/logout/', views.AuthLogoutAPIView.as_view(), name='api_auth_logout'),
    path('api/auth/me/', views.AuthMeAPIView.as_view(), name='api_auth_me'),
]
