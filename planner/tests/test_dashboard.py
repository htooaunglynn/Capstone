from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from planner.models import Goal, GoalStatus, Milestone, PracticeSession, ProgressNote, SessionStatus


User = get_user_model()


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='test-pass-123')
        self.other_user = User.objects.create_user(username='bob', password='test-pass-123')
        self.active_goal = Goal.objects.create(
            user=self.user,
            title='Learn Django Forms',
            status=GoalStatus.ACTIVE,
        )
        self.paused_goal = Goal.objects.create(
            user=self.user,
            title='Learn APIs',
            status=GoalStatus.PAUSED,
        )
        self.other_goal = Goal.objects.create(
            user=self.other_user,
            title='Other private goal',
            status=GoalStatus.ACTIVE,
        )
        Milestone.objects.create(goal=self.active_goal, title='Done milestone', is_complete=True)
        Milestone.objects.create(
            goal=self.active_goal,
            title='Overdue milestone',
            due_date=timezone.localdate() - timedelta(days=1),
        )
        Milestone.objects.create(
            goal=self.other_goal,
            title='Other overdue milestone',
            due_date=timezone.localdate() - timedelta(days=1),
        )
        PracticeSession.objects.create(
            user=self.user,
            goal=self.active_goal,
            scheduled_for=timezone.now() + timedelta(days=1),
            duration_minutes=45,
        )
        PracticeSession.objects.create(
            user=self.user,
            goal=self.active_goal,
            scheduled_for=timezone.now() - timedelta(days=1),
            duration_minutes=45,
            status=SessionStatus.COMPLETED,
        )
        PracticeSession.objects.create(
            user=self.other_user,
            goal=self.other_goal,
            scheduled_for=timezone.now() + timedelta(days=1),
            duration_minutes=30,
        )
        ProgressNote.objects.create(user=self.user, goal=self.active_goal, body='Private user note.')
        ProgressNote.objects.create(user=self.other_user, goal=self.other_goal, body='Other private note.')

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_dashboard_shows_only_current_users_data_and_counts(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'Learn Django Forms')
        self.assertContains(response, 'Overdue milestone')
        self.assertContains(response, 'Private user note.')
        self.assertNotContains(response, 'Other private goal')
        self.assertNotContains(response, 'Other overdue milestone')
        self.assertNotContains(response, 'Other private note.')
        self.assertEqual(response.context['active_goals_count'], 1)
        self.assertEqual(response.context['upcoming_sessions_count'], 1)
        self.assertEqual(response.context['completed_sessions_count'], 1)
        self.assertEqual(response.context['overdue_milestones_count'], 1)
        self.assertEqual(response.context['recent_notes_count'], 1)
        self.assertEqual(response.context['milestone_completion_percentage'], 50)
        self.assertEqual(response.context['session_completion_percentage'], 50)

    def test_dashboard_filters_goal_status(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'), {'status': GoalStatus.PAUSED})

        self.assertEqual(response.context['active_goals_count'], 1)
        self.assertContains(response, 'Learn APIs')
        self.assertNotContains(response, 'Learn Django Forms</a> &middot; 50%')

    def test_dashboard_summary_api_returns_global_shape(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('api_dashboard_summary'), {'range': 'week'})
        body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(body['ok'])
        self.assertEqual(body['message'], 'Dashboard summary loaded.')
        self.assertEqual(body['data']['summary']['active_goals_count'], 1)
        self.assertEqual(body['data']['summary']['upcoming_sessions_count'], 1)
        self.assertEqual(body['data']['summary']['overdue_milestones_count'], 1)
        self.assertEqual(len(body['data']['recent_notes']), 1)
