"""Query and domain helpers for SkillSprint."""

from datetime import timedelta

from django.utils import timezone

from .models import Goal, GoalStatus, Milestone, PracticeSession, ProgressNote, SessionStatus


def calculate_goal_progress(goal):
    """Return milestone and session completion counts for a goal."""
    total_milestones = goal.milestones.count()
    completed_milestones = goal.milestones.filter(is_complete=True).count()
    total_sessions = goal.practice_sessions.count()
    completed_sessions = goal.practice_sessions.filter(status='COMPLETED').count()
    percentage = 0

    if total_milestones:
        percentage = round((completed_milestones / total_milestones) * 100)

    return {
        'goal_id': goal.id,
        'percentage': percentage,
        'completed_milestones': completed_milestones,
        'total_milestones': total_milestones,
        'completed_sessions': completed_sessions,
        'total_sessions': total_sessions,
    }


def dashboard_session_summary(user, limit=5, status_filter='', date_range=''):
    now = timezone.now()
    today = timezone.localdate()
    session_filters = {
        'user': user,
        'scheduled_for__gte': now,
    }
    milestone_filters = {
        'goal__user': user,
        'due_date__lt': today,
        'is_complete': False,
    }

    if date_range == 'week':
        end = now + timedelta(days=7)
        session_filters['scheduled_for__lt'] = end
        milestone_filters['due_date__gte'] = today - timedelta(days=7)
    elif date_range == 'month':
        end = now + timedelta(days=30)
        session_filters['scheduled_for__lt'] = end
        milestone_filters['due_date__gte'] = today - timedelta(days=30)

    active_goals = Goal.objects.filter(user=user, status=GoalStatus.ACTIVE)
    if status_filter in GoalStatus.values:
        active_goals = Goal.objects.filter(user=user, status=status_filter)

    upcoming_sessions_queryset = (
        PracticeSession.objects
        .select_related('goal', 'milestone')
        .filter(**session_filters)
        .exclude(status__in=[SessionStatus.COMPLETED, SessionStatus.SKIPPED])
        .order_by('scheduled_for')
    )
    overdue_milestones = (
        Milestone.objects
        .select_related('goal')
        .filter(**milestone_filters)
        .order_by('due_date', 'order')
    )
    recent_notes = (
        ProgressNote.objects
        .select_related('goal', 'milestone', 'session')
        .filter(user=user)
        .order_by('-created_at')[:limit]
    )
    upcoming_sessions = (
        upcoming_sessions_queryset[:limit]
    )
    completed_sessions_count = PracticeSession.objects.filter(
        user=user,
        status=SessionStatus.COMPLETED,
    ).count()
    total_sessions_count = PracticeSession.objects.filter(user=user).count()
    completed_milestones_count = Milestone.objects.filter(
        goal__user=user,
        is_complete=True,
    ).count()
    total_milestones_count = Milestone.objects.filter(goal__user=user).count()

    return {
        'active_goals': active_goals[:limit],
        'upcoming_sessions': upcoming_sessions,
        'overdue_milestones': overdue_milestones[:limit],
        'recent_notes': recent_notes,
        'active_goals_count': active_goals.count(),
        'upcoming_sessions_count': upcoming_sessions_queryset.count(),
        'completed_sessions_count': completed_sessions_count,
        'overdue_milestones_count': overdue_milestones.count(),
        'recent_notes_count': ProgressNote.objects.filter(user=user).count(),
        'completed_milestones_count': completed_milestones_count,
        'total_milestones_count': total_milestones_count,
        'total_sessions_count': total_sessions_count,
        'milestone_completion_percentage': round(
            (completed_milestones_count / total_milestones_count) * 100
        ) if total_milestones_count else 0,
        'session_completion_percentage': round(
            (completed_sessions_count / total_sessions_count) * 100
        ) if total_sessions_count else 0,
        'status_filter': status_filter,
        'date_range': date_range,
        'status_choices': GoalStatus.choices,
    }


def dashboard_summary_payload(summary):
    return {
        'active_goals_count': summary['active_goals_count'],
        'upcoming_sessions_count': summary['upcoming_sessions_count'],
        'completed_sessions_count': summary['completed_sessions_count'],
        'overdue_milestones_count': summary['overdue_milestones_count'],
        'recent_notes_count': summary['recent_notes_count'],
        'completed_milestones_count': summary['completed_milestones_count'],
        'total_milestones_count': summary['total_milestones_count'],
        'total_sessions_count': summary['total_sessions_count'],
        'milestone_completion_percentage': summary['milestone_completion_percentage'],
        'session_completion_percentage': summary['session_completion_percentage'],
    }
