import json

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import GoalForm, MilestoneForm, PracticeSessionForm, RegisterForm
from .models import Goal, GoalStatus, Milestone, PracticeSession, Priority, SessionStatus
from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    MeSerializer,
    RefreshSerializer,
    RegisterSerializer,
    token_payload,
    user_payload,
)
from .services import calculate_goal_progress, dashboard_session_summary


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
    return render(request, 'planner/dashboard.html', dashboard_session_summary(request.user))


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
def milestone_create(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)

    if request.method == 'POST':
        form = MilestoneForm(request.POST)
        if form.is_valid():
            milestone = form.save(commit=False)
            milestone.goal = goal
            milestone.save()
            messages.success(request, 'Milestone created.')
            return redirect('goal_detail', goal_id=goal.id)
    else:
        next_order = goal.milestones.count() + 1
        form = MilestoneForm(initial={'order': next_order})

    return render(
        request,
        'planner/milestone_form.html',
        {
            'form': form,
            'goal': goal,
            'title': 'Create milestone',
            'submit_label': 'Create milestone',
        },
    )


@login_required
def milestone_edit(request, milestone_id):
    milestone = get_object_or_404(
        Milestone.objects.select_related('goal'),
        id=milestone_id,
        goal__user=request.user,
    )

    if request.method == 'POST':
        form = MilestoneForm(request.POST, instance=milestone)
        if form.is_valid():
            form.save()
            messages.success(request, 'Milestone updated.')
            return redirect('goal_detail', goal_id=milestone.goal_id)
    else:
        form = MilestoneForm(instance=milestone)

    return render(
        request,
        'planner/milestone_form.html',
        {
            'form': form,
            'goal': milestone.goal,
            'milestone': milestone,
            'title': 'Edit milestone',
            'submit_label': 'Save changes',
        },
    )


@login_required
def milestone_delete(request, milestone_id):
    milestone = get_object_or_404(
        Milestone.objects.select_related('goal'),
        id=milestone_id,
        goal__user=request.user,
    )
    goal = milestone.goal

    if request.method == 'POST':
        milestone.delete()
        messages.success(request, 'Milestone deleted.')
        return redirect('goal_detail', goal_id=goal.id)

    return render(
        request,
        'planner/milestone_confirm_delete.html',
        {'goal': goal, 'milestone': milestone},
    )


@login_required
def session_list(request):
    sessions = (
        PracticeSession.objects
        .select_related('goal', 'milestone')
        .filter(user=request.user)
        .order_by('scheduled_for')
    )
    return render(request, 'planner/session_list.html', {'sessions': sessions})


@login_required
def session_create(request, goal_id=None):
    goal = None
    if goal_id is not None:
        goal = get_object_or_404(Goal, id=goal_id, user=request.user)

    if request.method == 'POST':
        form = PracticeSessionForm(request.POST, user=request.user, goal=goal)
        if form.is_valid():
            practice_session = form.save(commit=False)
            practice_session.user = request.user
            practice_session.goal = form.cleaned_data['goal']
            practice_session.full_clean()
            practice_session.save()
            messages.success(request, 'Practice session created.')
            return redirect('goal_detail', goal_id=practice_session.goal_id)
    else:
        form = PracticeSessionForm(user=request.user, goal=goal)

    return render(
        request,
        'planner/session_form.html',
        {
            'form': form,
            'goal': goal,
            'title': 'Schedule practice session',
            'submit_label': 'Schedule session',
        },
    )


@login_required
def session_edit(request, session_id):
    practice_session = get_object_or_404(
        PracticeSession.objects.select_related('goal', 'milestone'),
        id=session_id,
        user=request.user,
    )

    if request.method == 'POST':
        form = PracticeSessionForm(request.POST, instance=practice_session, user=request.user)
        if form.is_valid():
            practice_session = form.save(commit=False)
            practice_session.user = request.user
            practice_session.full_clean()
            practice_session.save()
            messages.success(request, 'Practice session updated.')
            return redirect('goal_detail', goal_id=practice_session.goal_id)
    else:
        form = PracticeSessionForm(instance=practice_session, user=request.user)

    return render(
        request,
        'planner/session_form.html',
        {
            'form': form,
            'goal': practice_session.goal,
            'practice_session': practice_session,
            'title': 'Edit practice session',
            'submit_label': 'Save changes',
        },
    )


@login_required
def session_delete(request, session_id):
    practice_session = get_object_or_404(
        PracticeSession.objects.select_related('goal'),
        id=session_id,
        user=request.user,
    )
    goal = practice_session.goal

    if request.method == 'POST':
        practice_session.delete()
        messages.success(request, 'Practice session deleted.')
        return redirect('goal_detail', goal_id=goal.id)

    return render(
        request,
        'planner/session_confirm_delete.html',
        {'goal': goal, 'practice_session': practice_session},
    )


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


def json_success(message, data=None, response_status=200):
    return JsonResponse(
        {
            'ok': True,
            'message': message,
            'data': data or {},
        },
        status=response_status,
    )


def json_error(message, errors=None, response_status=400):
    return JsonResponse(
        {
            'ok': False,
            'message': message,
            'errors': errors or {},
        },
        status=response_status,
    )


def request_json(request):
    if not request.body:
        return {}

    try:
        return json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError as exc:
        raise ValidationError({'json': ['Request body must be valid JSON.']}) from exc


def milestone_payload(milestone):
    return {
        'id': milestone.id,
        'title': milestone.title,
        'notes': milestone.notes,
        'due_date': milestone.due_date.isoformat() if milestone.due_date else None,
        'order': milestone.order,
        'is_complete': milestone.is_complete,
        'completed_at': milestone.completed_at.isoformat() if milestone.completed_at else None,
    }


def session_payload(practice_session):
    return {
        'id': practice_session.id,
        'goal_id': practice_session.goal_id,
        'milestone_id': practice_session.milestone_id,
        'scheduled_for': practice_session.scheduled_for.isoformat(),
        'duration_minutes': practice_session.duration_minutes,
        'status': practice_session.status,
        'status_display': practice_session.get_status_display(),
        'notes': practice_session.notes,
        'completed_at': practice_session.completed_at.isoformat() if practice_session.completed_at else None,
    }


@login_required
@require_POST
def api_milestone_toggle(request, milestone_id):
    milestone = get_object_or_404(
        Milestone.objects.select_related('goal'),
        id=milestone_id,
        goal__user=request.user,
    )

    try:
        payload = request_json(request)
    except ValidationError as exc:
        return json_error('Invalid JSON.', exc.message_dict)

    is_complete = payload.get('is_complete')
    if not isinstance(is_complete, bool):
        return json_error(
            'Validation failed.',
            {'is_complete': ['This field must be true or false.']},
        )

    milestone.is_complete = is_complete
    milestone.completed_at = timezone.now() if is_complete else None
    milestone.save(update_fields=['is_complete', 'completed_at', 'updated_at'])

    return json_success(
        'Milestone updated.',
        {
            'milestone': milestone_payload(milestone),
            'goal_progress': calculate_goal_progress(milestone.goal),
        },
    )


@login_required
@require_POST
def api_milestone_reorder(request):
    try:
        payload = request_json(request)
    except ValidationError as exc:
        return json_error('Invalid JSON.', exc.message_dict)

    goal_id = payload.get('goal_id')
    milestone_ids = payload.get('milestone_ids')

    if not isinstance(goal_id, int) or not isinstance(milestone_ids, list):
        return json_error(
            'Validation failed.',
            {
                'goal_id': ['A goal id is required.'],
                'milestone_ids': ['A list of milestone ids is required.'],
            },
        )

    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    owned_ids = set(goal.milestones.values_list('id', flat=True))
    submitted_ids = set(milestone_ids)

    if owned_ids != submitted_ids or len(milestone_ids) != len(owned_ids):
        return json_error(
            'Validation failed.',
            {'milestone_ids': ['Milestone ids must match this goal exactly.']},
        )

    for order, milestone_id in enumerate(milestone_ids, start=1):
        Milestone.objects.filter(id=milestone_id, goal=goal).update(order=order)

    milestones = goal.milestones.all()
    return json_success(
        'Milestones reordered.',
        {
            'goal_id': goal.id,
            'milestones': [milestone_payload(milestone) for milestone in milestones],
        },
    )


@login_required
@require_POST
def api_session_status(request, session_id):
    practice_session = get_object_or_404(
        PracticeSession.objects.select_related('goal'),
        id=session_id,
        user=request.user,
    )

    try:
        payload = request_json(request)
    except ValidationError as exc:
        return json_error('Invalid JSON.', exc.message_dict)

    new_status = payload.get('status')
    if new_status not in SessionStatus.values:
        return json_error(
            'Validation failed.',
            {'status': ['Unsupported session status.']},
        )

    practice_session.status = new_status
    practice_session.completed_at = timezone.now() if new_status == SessionStatus.COMPLETED else None
    practice_session.full_clean()
    practice_session.save(update_fields=['status', 'completed_at', 'updated_at'])
    dashboard_summary = dashboard_session_summary(request.user)

    return json_success(
        'Practice session updated.',
        {
            'session': session_payload(practice_session),
            'goal_progress': calculate_goal_progress(practice_session.goal),
            'dashboard_summary': {
                'upcoming_sessions_count': dashboard_summary['upcoming_sessions_count'],
                'completed_sessions_count': dashboard_summary['completed_sessions_count'],
            },
        },
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
