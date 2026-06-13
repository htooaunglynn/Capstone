from django.urls import path

from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('accounts/login/', views.PlannerLoginView.as_view(), name='login'),
    path('accounts/logout/', views.logout_page, name='logout'),
    path('accounts/register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('goals/', views.goal_list, name='goal_list'),
    path('goals/new/', views.goal_create, name='goal_create'),
    path('goals/<int:goal_id>/', views.goal_detail, name='goal_detail'),
    path('goals/<int:goal_id>/edit/', views.goal_edit, name='goal_edit'),
    path('goals/<int:goal_id>/delete/', views.goal_delete, name='goal_delete'),
    path('goals/<int:goal_id>/milestones/new/', views.milestone_create, name='milestone_create'),
    path('milestones/<int:milestone_id>/edit/', views.milestone_edit, name='milestone_edit'),
    path('milestones/<int:milestone_id>/delete/', views.milestone_delete, name='milestone_delete'),
    path('api/auth/register/', views.AuthRegisterAPIView.as_view(), name='api_auth_register'),
    path('api/auth/login/', views.AuthLoginAPIView.as_view(), name='api_auth_login'),
    path('api/auth/refresh/', views.AuthRefreshAPIView.as_view(), name='api_auth_refresh'),
    path('api/auth/logout/', views.AuthLogoutAPIView.as_view(), name='api_auth_logout'),
    path('api/auth/me/', views.AuthMeAPIView.as_view(), name='api_auth_me'),
    path('api/milestones/<int:milestone_id>/toggle/', views.api_milestone_toggle, name='api_milestone_toggle'),
    path('api/milestones/reorder/', views.api_milestone_reorder, name='api_milestone_reorder'),
]
