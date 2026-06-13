from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from planner.models import Goal, Milestone, PracticeSession, ProgressNote


User = get_user_model()


class ProgressNoteCrudTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='test-pass-123')
        self.other_user = User.objects.create_user(username='bob', password='test-pass-123')
        self.goal = Goal.objects.create(user=self.user, title='Learn Django Forms')
        self.milestone = Milestone.objects.create(goal=self.goal, title='Study ModelForms')
        self.session = PracticeSession.objects.create(
            user=self.user,
            goal=self.goal,
            milestone=self.milestone,
            scheduled_for=timezone.now() + timedelta(days=1),
            duration_minutes=45,
        )
        self.other_goal = Goal.objects.create(user=self.other_user, title='Learn SQL')
        self.other_milestone = Milestone.objects.create(goal=self.other_goal, title='Study joins')
        self.other_session = PracticeSession.objects.create(
            user=self.other_user,
            goal=self.other_goal,
            scheduled_for=timezone.now() + timedelta(days=1),
            duration_minutes=30,
        )
        self.note = ProgressNote.objects.create(
            user=self.user,
            goal=self.goal,
            milestone=self.milestone,
            session=self.session,
            body='Forms validation is starting to click.',
        )
        self.other_note = ProgressNote.objects.create(
            user=self.other_user,
            goal=self.other_goal,
            body='Private SQL note.',
        )

    def test_note_list_requires_login(self):
        response = self.client.get(reverse('progress_note_list'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('progress_note_list')}")

    def test_note_list_shows_only_current_users_notes(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('progress_note_list'))

        self.assertContains(response, self.note.body)
        self.assertNotContains(response, self.other_note.body)

    def test_note_list_filters_by_search_and_goal(self):
        second_goal = Goal.objects.create(user=self.user, title='Learn APIs')
        second_note = ProgressNote.objects.create(
            user=self.user,
            goal=second_goal,
            body='JWT refresh needs careful testing.',
        )
        self.client.force_login(self.user)

        search_response = self.client.get(reverse('progress_note_list'), {'q': 'JWT'})
        goal_response = self.client.get(reverse('progress_note_list'), {'goal': self.goal.id})

        self.assertContains(search_response, second_note.body)
        self.assertNotContains(search_response, self.note.body)
        self.assertContains(goal_response, self.note.body)
        self.assertNotContains(goal_response, second_note.body)

    def test_user_can_create_note_for_own_goal(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('goal_note_create', args=[self.goal.id]),
            {
                'goal': self.goal.id,
                'milestone': self.milestone.id,
                'session': self.session.id,
                'body': 'ModelForm clean methods need another pass.',
            },
        )

        created = ProgressNote.objects.get(body='ModelForm clean methods need another pass.')
        self.assertEqual(created.user, self.user)
        self.assertEqual(created.goal, self.goal)
        self.assertEqual(created.milestone, self.milestone)
        self.assertEqual(created.session, self.session)
        self.assertRedirects(response, reverse('goal_detail', args=[self.goal.id]))

    def test_user_cannot_create_note_for_another_users_goal(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('goal_note_create', args=[self.other_goal.id]),
            {
                'goal': self.other_goal.id,
                'milestone': '',
                'session': '',
                'body': 'Should not save.',
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(ProgressNote.objects.filter(body='Should not save.').exists())

    def test_note_form_rejects_wrong_milestone_and_session(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('goal_note_create', args=[self.goal.id]),
            {
                'goal': self.goal.id,
                'milestone': self.other_milestone.id,
                'session': self.other_session.id,
                'body': 'Invalid relationships.',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select a valid choice')
        self.assertFalse(ProgressNote.objects.filter(body='Invalid relationships.').exists())

    def test_note_form_rejects_blank_body(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('goal_note_create', args=[self.goal.id]),
            {
                'goal': self.goal.id,
                'milestone': '',
                'session': '',
                'body': '   ',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Progress note body cannot be empty.')

    def test_user_can_edit_and_delete_own_note_but_not_another_users_note(self):
        self.client.force_login(self.user)

        blocked_update = self.client.post(
            reverse('progress_note_edit', args=[self.other_note.id]),
            {
                'goal': self.other_goal.id,
                'milestone': '',
                'session': '',
                'body': 'Changed.',
            },
        )
        update_response = self.client.post(
            reverse('progress_note_edit', args=[self.note.id]),
            {
                'goal': self.goal.id,
                'milestone': self.milestone.id,
                'session': self.session.id,
                'body': 'Updated note.',
            },
        )
        blocked_delete = self.client.post(reverse('progress_note_delete', args=[self.other_note.id]))
        self.note.refresh_from_db()
        delete_response = self.client.post(reverse('progress_note_delete', args=[self.note.id]))

        self.assertEqual(blocked_update.status_code, 404)
        self.assertRedirects(update_response, reverse('goal_detail', args=[self.goal.id]))
        self.assertEqual(self.note.body, 'Updated note.')
        self.assertEqual(blocked_delete.status_code, 404)
        self.assertRedirects(delete_response, reverse('goal_detail', args=[self.goal.id]))
        self.assertFalse(ProgressNote.objects.filter(id=self.note.id).exists())
        self.assertTrue(ProgressNote.objects.filter(id=self.other_note.id).exists())
