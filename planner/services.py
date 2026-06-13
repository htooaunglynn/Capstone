"""Query and domain helpers for SkillSprint."""

from django.utils import timezone

from .models import Goal, GoalStatus, Milestone, PracticeSession, SessionStatus


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


def dashboard_session_summary(user, limit=5):
    now = timezone.now()
    upcoming_sessions = (
        PracticeSession.objects
        .select_related('goal', 'milestone')
        .filter(user=user, scheduled_for__gte=now)
        .exclude(status__in=[SessionStatus.COMPLETED, SessionStatus.SKIPPED])
        .order_by('scheduled_for')[:limit]
    )

    return {
        'active_goals': Goal.objects.filter(user=user, status=GoalStatus.ACTIVE)[:limit],
        'upcoming_sessions': upcoming_sessions,
        'active_goals_count': Goal.objects.filter(user=user, status=GoalStatus.ACTIVE).count(),
        'upcoming_sessions_count': PracticeSession.objects.filter(
            user=user,
            scheduled_for__gte=now,
        ).exclude(status__in=[SessionStatus.COMPLETED, SessionStatus.SKIPPED]).count(),
        'completed_sessions_count': PracticeSession.objects.filter(
            user=user,
            status=SessionStatus.COMPLETED,
        ).count(),
        'overdue_milestones_count': Milestone.objects.filter(
            goal__user=user,
            due_date__lt=timezone.localdate(),
            is_complete=False,
        ).count(),
    }
