from django.contrib import admin

from .models import Goal, Milestone, PracticeSession, ProgressNote


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'priority', 'status', 'target_date', 'created_at')
    list_filter = ('priority', 'status', 'created_at')
    search_fields = ('title', 'description', 'category', 'user__username')


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'goal', 'order', 'due_date', 'is_complete', 'created_at')
    list_filter = ('is_complete', 'due_date', 'created_at')
    search_fields = ('title', 'notes', 'goal__title')


@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    list_display = (
        'goal',
        'user',
        'milestone',
        'scheduled_for',
        'duration_minutes',
        'status',
    )
    list_filter = ('status', 'scheduled_for', 'created_at')
    search_fields = ('goal__title', 'milestone__title', 'notes', 'user__username')


@admin.register(ProgressNote)
class ProgressNoteAdmin(admin.ModelAdmin):
    list_display = ('goal', 'user', 'milestone', 'session', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('body', 'goal__title', 'milestone__title', 'user__username')
