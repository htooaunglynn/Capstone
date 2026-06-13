from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from planner.models import (
    Goal,
    GoalStatus,
    Milestone,
    PracticeSession,
    Priority,
    ProgressNote,
    SessionStatus,
)
from planner.services import calculate_goal_progress


User = get_user_model()


class PlannerModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='test-pass')
        self.other_user = User.objects.create_user(username='bob', password='test-pass')
        self.goal = Goal.objects.create(
            user=self.user,
            title='Learn Django Forms',
            priority=Priority.HIGH,
            status=GoalStatus.ACTIVE,
        )

    def test_goal_can_own_milestones_sessions_and_notes(self):
        milestone = Milestone.objects.create(goal=self.goal, title='Study ModelForms')
        session = PracticeSession.objects.create(
            user=self.user,
            goal=self.goal,
            milestone=milestone,
            scheduled_for=timezone.now() + timedelta(days=1),
            duration_minutes=45,
        )
        note = ProgressNote.objects.create(
            user=self.user,
            goal=self.goal,
            milestone=milestone,
            session=session,
            body='Forms validation is starting to click.',
        )

        self.assertEqual(self.goal.milestones.get(), milestone)
        self.assertEqual(self.goal.practice_sessions.get(), session)
        self.assertEqual(self.goal.progress_notes.get(), note)

    def test_milestones_are_ordered_by_order_then_created_at(self):
        second = Milestone.objects.create(goal=self.goal, title='Second', order=2)
        first = Milestone.objects.create(goal=self.goal, title='First', order=1)

        self.assertEqual(list(self.goal.milestones.all()), [first, second])

    def test_practice_session_rejects_milestone_from_another_goal(self):
        other_goal = Goal.objects.create(user=self.user, title='Learn SQL')
        other_milestone = Milestone.objects.create(goal=other_goal, title='Joins')
        session = PracticeSession(
            user=self.user,
            goal=self.goal,
            milestone=other_milestone,
            scheduled_for=timezone.now() + timedelta(days=1),
            duration_minutes=30,
        )

        with self.assertRaises(ValidationError) as context:
            session.full_clean()

        self.assertIn('milestone', context.exception.message_dict)

    def test_practice_session_rejects_user_that_does_not_own_goal(self):
        session = PracticeSession(
            user=self.other_user,
            goal=self.goal,
            scheduled_for=timezone.now() + timedelta(days=1),
            duration_minutes=30,
        )

        with self.assertRaises(ValidationError) as context:
            session.full_clean()

        self.assertIn('user', context.exception.message_dict)

    def test_practice_session_rejects_zero_duration(self):
        session = PracticeSession(
            user=self.user,
            goal=self.goal,
            scheduled_for=timezone.now() + timedelta(days=1),
            duration_minutes=0,
        )

        with self.assertRaises(ValidationError) as context:
            session.full_clean()

        self.assertIn('duration_minutes', context.exception.message_dict)

    def test_progress_note_rejects_invalid_relationships_and_empty_body(self):
        other_goal = Goal.objects.create(user=self.user, title='Learn APIs')
        other_milestone = Milestone.objects.create(goal=other_goal, title='Serializers')
        other_session = PracticeSession.objects.create(
            user=self.user,
            goal=other_goal,
            scheduled_for=timezone.now() + timedelta(days=1),
            duration_minutes=30,
        )
        note = ProgressNote(
            user=self.other_user,
            goal=self.goal,
            milestone=other_milestone,
            session=other_session,
            body='   ',
        )

        with self.assertRaises(ValidationError) as context:
            note.full_clean()

        errors = context.exception.message_dict
        self.assertIn('body', errors)
        self.assertIn('user', errors)
        self.assertIn('milestone', errors)
        self.assertIn('session', errors)

    def test_goal_progress_helper_returns_expected_counts(self):
        Milestone.objects.create(goal=self.goal, title='Models', is_complete=True)
        Milestone.objects.create(goal=self.goal, title='Forms')
        PracticeSession.objects.create(
            user=self.user,
            goal=self.goal,
            scheduled_for=timezone.now() - timedelta(days=1),
            duration_minutes=60,
            status=SessionStatus.COMPLETED,
        )
        PracticeSession.objects.create(
            user=self.user,
            goal=self.goal,
            scheduled_for=timezone.now() + timedelta(days=1),
            duration_minutes=30,
            status=SessionStatus.PLANNED,
        )

        self.assertEqual(
            calculate_goal_progress(self.goal),
            {
                'goal_id': self.goal.id,
                'percentage': 50,
                'completed_milestones': 1,
                'total_milestones': 2,
                'completed_sessions': 1,
                'total_sessions': 2,
            },
        )
        self.assertEqual(self.goal.progress_percentage, 50)
