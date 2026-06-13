from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import GoalForm, RegisterForm
from .models import Goal, GoalStatus, Priority
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


@login_required
def goal_list(request):
    goals = Goal.objects.filter(user=request.user)
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    priority_filter = request.GET.get('priority', '').strip()

    if search_query:
        goals = goals.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(category__icontains=search_query)
        )

    if status_filter in GoalStatus.values:
        goals = goals.filter(status=status_filter)

    if priority_filter in Priority.values:
        goals = goals.filter(priority=priority_filter)

    context = {
        'goals': goals,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'status_choices': GoalStatus.choices,
        'priority_choices': Priority.choices,
    }
    return render(request, 'planner/goal_list.html', context)


@login_required
def goal_detail(request, goal_id):
    goal = get_object_or_404(
        Goal.objects.prefetch_related(
            'milestones',
            'practice_sessions',
            'progress_notes',
        ),
        id=goal_id,
        user=request.user,
    )
    return render(request, 'planner/goal_detail.html', {'goal': goal})


@login_required
def goal_create(request):
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, 'Goal created.')
            return redirect('goal_detail', goal_id=goal.id)
    else:
        form = GoalForm()

    return render(
        request,
        'planner/goal_form.html',
        {'form': form, 'title': 'Create goal', 'submit_label': 'Create goal'},
    )


@login_required
def goal_edit(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)

    if request.method == 'POST':
        form = GoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Goal updated.')
            return redirect('goal_detail', goal_id=goal.id)
    else:
        form = GoalForm(instance=goal)

    return render(
        request,
        'planner/goal_form.html',
        {
            'form': form,
            'goal': goal,
            'title': 'Edit goal',
            'submit_label': 'Save changes',
        },
    )


@login_required
def goal_delete(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)

    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Goal deleted.')
        return redirect('goal_list')

    return render(request, 'planner/goal_confirm_delete.html', {'goal': goal})


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
