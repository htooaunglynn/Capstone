"""Query and domain helpers for SkillSprint."""


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
