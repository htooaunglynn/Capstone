from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from planner.models import Goal, Milestone, PracticeSession, Priority, SessionStatus


User = get_user_model()


class PracticeSessionCrudTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='test-pass-123')
        self.other_user = User.objects.create_user(username='bob', password='test-pass-123')
        self.goal = Goal.objects.create(
            user=self.user,
            title='Learn Django Forms',
            priority=Priority.HIGH,
        )
        self.milestone = Milestone.objects.create(goal=self.goal, title='Study ModelForms')
        self.other_goal = Goal.objects.create(user=self.other_user, title='Learn SQL')
        self.other_milestone = Milestone.objects.create(goal=self.other_goal, title='Study joins')
        self.practice_session = PracticeSession.objects.create(
            user=self.user,
            goal=self.goal,
            milestone=self.milestone,
            scheduled_for=timezone.now() + timedelta(days=1),
            duration_minutes=45,
        )
        self.other_session = PracticeSession.objects.create(
            user=self.other_user,
            goal=self.other_goal,
            scheduled_for=timezone.now() + timedelta(days=1),
            duration_minutes=30,
        )

    def test_session_list_requires_login(self):
        response = self.client.get(reverse('session_list'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('session_list')}")

    def test_session_list_shows_only_current_users_sessions(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('session_list'))

        self.assertContains(response, self.goal.title)
        self.assertNotContains(response, self.other_goal.title)

    def test_session_list_filters_by_search_status_and_date_range(self):
        self.client.force_login(self.user)
        PracticeSession.objects.create(
            user=self.user,
            goal=self.goal,
            scheduled_for=timezone.now() - timedelta(days=3),
            duration_minutes=30,
            status=SessionStatus.COMPLETED,
            notes='Older completed review.',
        )

        search_response = self.client.get(reverse('session_list'), {'q': 'ModelForms'})
        status_response = self.client.get(reverse('session_list'), {'status': SessionStatus.COMPLETED})
        upcoming_response = self.client.get(reverse('session_list'), {'range': 'upcoming'})

        self.assertContains(search_response, self.goal.title)
        self.assertEqual(list(status_response.context['sessions']), list(
            PracticeSession.objects.filter(user=self.user, status=SessionStatus.COMPLETED)
        ))
        self.assertContains(upcoming_response, self.goal.title)
        self.assertNotContains(upcoming_response, 'Older completed review.')

    def test_user_can_create_session_for_own_goal(self):
        self.client.force_login(self.user)
        scheduled_for = timezone.now() + timedelta(days=2)

        response = self.client.post(
            reverse('goal_session_create', args=[self.goal.id]),
            {
                'goal': self.goal.id,
                'milestone': self.milestone.id,
                'scheduled_for': scheduled_for.strftime('%Y-%m-%dT%H:%M'),
                'duration_minutes': 60,
                'status': SessionStatus.PLANNED,
                'notes': 'Build a sample form.',
            },
        )

        created = PracticeSession.objects.get(notes='Build a sample form.')
        self.assertEqual(created.user, self.user)
        self.assertEqual(created.goal, self.goal)
        self.assertEqual(created.milestone, self.milestone)
        self.assertRedirects(response, reverse('goal_detail', args=[self.goal.id]))

    def test_user_cannot_create_session_for_another_users_goal(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('goal_session_create', args=[self.other_goal.id]),
            {
                'goal': self.other_goal.id,
                'milestone': '',
                'scheduled_for': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
                'duration_minutes': 30,
                'status': SessionStatus.PLANNED,
                'notes': 'Should not save.',
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(PracticeSession.objects.filter(notes='Should not save.').exists())

    def test_session_form_rejects_milestone_from_another_goal(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('goal_session_create', args=[self.goal.id]),
            {
                'goal': self.goal.id,
                'milestone': self.other_milestone.id,
                'scheduled_for': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
                'duration_minutes': 30,
                'status': SessionStatus.PLANNED,
                'notes': 'Invalid pairing.',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select a valid choice')
        self.assertFalse(PracticeSession.objects.filter(notes='Invalid pairing.').exists())

    def test_user_can_edit_and_delete_own_session_but_not_another_users_session(self):
        self.client.force_login(self.user)

        blocked_update = self.client.post(
            reverse('session_edit', args=[self.other_session.id]),
            {
                'goal': self.other_goal.id,
                'milestone': '',
                'scheduled_for': (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'),
                'duration_minutes': 90,
                'status': SessionStatus.PLANNED,
                'notes': 'Changed.',
            },
        )
        update_response = self.client.post(
            reverse('session_edit', args=[self.practice_session.id]),
            {
                'goal': self.goal.id,
                'milestone': self.milestone.id,
                'scheduled_for': (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'),
                'duration_minutes': 90,
                'status': SessionStatus.RESCHEDULED,
                'notes': 'Moved later.',
            },
        )
        blocked_delete = self.client.post(reverse('session_delete', args=[self.other_session.id]))
        self.practice_session.refresh_from_db()
        self.other_session.refresh_from_db()
        delete_response = self.client.post(reverse('session_delete', args=[self.practice_session.id]))

        self.assertEqual(blocked_update.status_code, 404)
        self.assertRedirects(update_response, reverse('goal_detail', args=[self.goal.id]))
        self.assertEqual(self.practice_session.duration_minutes, 90)
        self.assertEqual(self.practice_session.status, SessionStatus.RESCHEDULED)
        self.assertEqual(blocked_delete.status_code, 404)
        self.assertRedirects(delete_response, reverse('goal_detail', args=[self.goal.id]))
        self.assertFalse(PracticeSession.objects.filter(id=self.practice_session.id).exists())
        self.assertTrue(PracticeSession.objects.filter(id=self.other_session.id).exists())


class PracticeSessionApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='test-pass-123')
        self.other_user = User.objects.create_user(username='bob', password='test-pass-123')
        self.goal = Goal.objects.create(user=self.user, title='Learn Django Forms')
        self.other_goal = Goal.objects.create(user=self.other_user, title='Learn SQL')
        self.practice_session = PracticeSession.objects.create(
            user=self.user,
            goal=self.goal,
            scheduled_for=timezone.now() + timedelta(days=1),
            duration_minutes=45,
        )
        self.other_session = PracticeSession.objects.create(
            user=self.other_user,
            goal=self.other_goal,
            scheduled_for=timezone.now() + timedelta(days=1),
            duration_minutes=30,
        )

    def test_status_update_requires_login(self):
        response = self.client.post(
            reverse('api_session_status', args=[self.practice_session.id]),
            {'status': SessionStatus.COMPLETED},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 302)

    def test_status_update_persists_and_returns_progress(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('api_session_status', args=[self.practice_session.id]),
            {'status': SessionStatus.COMPLETED},
            content_type='application/json',
        )

        self.practice_session.refresh_from_db()
        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(body['ok'])
        self.assertEqual(self.practice_session.status, SessionStatus.COMPLETED)
        self.assertIsNotNone(self.practice_session.completed_at)
        self.assertEqual(body['data']['session']['status'], SessionStatus.COMPLETED)
        self.assertEqual(body['data']['goal_progress']['completed_sessions'], 1)
        self.assertEqual(body['data']['dashboard_summary']['completed_sessions_count'], 1)

    def test_status_update_rejects_invalid_status_and_other_users_session(self):
        self.client.force_login(self.user)

        invalid_response = self.client.post(
            reverse('api_session_status', args=[self.practice_session.id]),
            {'status': 'DONE'},
            content_type='application/json',
        )
        blocked_response = self.client.post(
            reverse('api_session_status', args=[self.other_session.id]),
            {'status': SessionStatus.COMPLETED},
            content_type='application/json',
        )

        self.assertEqual(invalid_response.status_code, 400)
        self.assertFalse(invalid_response.json()['ok'])
        self.assertEqual(blocked_response.status_code, 404)
