from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import RegisterForm
from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    MeSerializer,
    RefreshSerializer,
    RegisterSerializer,
    token_payload,
    user_payload,
)


def landing(request):
    return render(request, 'planner/landing.html')


class PlannerLoginView(LoginView):
    template_name = 'planner/auth/login.html'
    redirect_authenticated_user = True


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to SkillSprint.')
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'planner/auth/register.html', {'form': form})


@require_POST
def logout_page(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('landing')


@login_required
def dashboard(request):
    return render(request, 'planner/dashboard.html')


def api_success(message, data=None, response_status=status.HTTP_200_OK):
    return Response(
        {
            'ok': True,
            'message': message,
            'data': data or {},
        },
        status=response_status,
    )


def api_error(message, errors=None, response_status=status.HTTP_400_BAD_REQUEST):
    return Response(
        {
            'ok': False,
            'message': message,
            'errors': errors or {},
        },
        status=response_status,
    )


class AuthRegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error('Validation failed.', serializer.errors)

        user = serializer.save()
        return api_success(
            'Registration successful.',
            {
                'user': user_payload(user),
                'tokens': token_payload(user),
            },
            status.HTTP_201_CREATED,
        )


class AuthLoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return api_error('Login failed.', serializer.errors)

        user = serializer.validated_data['user']
        return api_success(
            'Login successful.',
            {
                'user': user_payload(user),
                'tokens': token_payload(user),
            },
        )


class AuthRefreshAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error('Token refresh failed.', serializer.errors)

        return api_success(
            'Token refreshed.',
            {'tokens': serializer.validated_data['tokens']},
        )


class AuthLogoutAPIView(APIView):
    def post(self, request):
        serializer = LogoutSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return api_error('Logout failed.', serializer.errors)

        try:
            serializer.save()
        except Exception as exc:
            return api_error('Logout failed.', getattr(exc, 'detail', {'refresh': [str(exc)]}))

        return api_success('Logout successful.')


class AuthMeAPIView(APIView):
    def get(self, request):
        serializer = MeSerializer(request.user)
        return api_success('Authenticated user loaded.', {'user': serializer.data})
