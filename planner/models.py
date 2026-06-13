from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Priority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'


class GoalStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    PAUSED = 'PAUSED', 'Paused'
    COMPLETED = 'COMPLETED', 'Completed'
    ARCHIVED = 'ARCHIVED', 'Archived'


class SessionStatus(models.TextChoices):
    PLANNED = 'PLANNED', 'Planned'
    COMPLETED = 'COMPLETED', 'Completed'
    SKIPPED = 'SKIPPED', 'Skipped'
    RESCHEDULED = 'RESCHEDULED', 'Rescheduled'


class Goal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='goals',
    )
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=60, blank=True)
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    status = models.CharField(
        max_length=20,
        choices=GoalStatus.choices,
        default=GoalStatus.ACTIVE,
    )
    target_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'priority']),
            models.Index(fields=['target_date']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title

    @property
    def completed_milestones_count(self):
        return self.milestones.filter(is_complete=True).count()

    @property
    def total_milestones_count(self):
        return self.milestones.count()

    @property
    def progress_percentage(self):
        total = self.total_milestones_count
        if total == 0:
            return 0
        return round((self.completed_milestones_count / total) * 100)


class Milestone(models.Model):
    goal = models.ForeignKey(
        Goal,
        on_delete=models.CASCADE,
        related_name='milestones',
    )
    title = models.CharField(max_length=120)
    notes = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_complete = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['goal', 'order']),
            models.Index(fields=['due_date']),
            models.Index(fields=['is_complete']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title


class PracticeSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='practice_sessions',
    )
    goal = models.ForeignKey(
        Goal,
        on_delete=models.CASCADE,
        related_name='practice_sessions',
    )
    milestone = models.ForeignKey(
        Milestone,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='practice_sessions',
    )
    scheduled_for = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.PLANNED,
    )
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_for']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['goal', 'status']),
            models.Index(fields=['scheduled_for']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.goal.title} on {self.scheduled_for:%Y-%m-%d %H:%M}'

    def clean(self):
        errors = {}

        if self.duration_minutes <= 0:
            errors['duration_minutes'] = 'Duration must be greater than 0.'

        if self.goal_id and self.user_id and self.goal.user_id != self.user_id:
            errors['user'] = 'Session user must match the goal owner.'

        if self.milestone_id and self.goal_id and self.milestone.goal_id != self.goal_id:
            errors['milestone'] = 'Milestone must belong to the selected goal.'

        if errors:
            raise ValidationError(errors)


class ProgressNote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='progress_notes',
    )
    goal = models.ForeignKey(
        Goal,
        on_delete=models.CASCADE,
        related_name='progress_notes',
    )
    milestone = models.ForeignKey(
        Milestone,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='progress_notes',
    )
    session = models.ForeignKey(
        PracticeSession,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='progress_notes',
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['goal', 'created_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'Note for {self.goal.title}'

    def clean(self):
        errors = {}

        if not self.body.strip():
            errors['body'] = 'Progress note body cannot be empty.'

        if self.goal_id and self.user_id and self.goal.user_id != self.user_id:
            errors['user'] = 'Note user must match the goal owner.'

        if self.milestone_id and self.goal_id and self.milestone.goal_id != self.goal_id:
            errors['milestone'] = 'Milestone must belong to the selected goal.'

        if self.session_id and self.goal_id and self.session.goal_id != self.goal_id:
            errors['session'] = 'Session must belong to the selected goal.'

        if errors:
            raise ValidationError(errors)
