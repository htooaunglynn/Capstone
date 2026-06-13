from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from planner.models import Goal, Milestone, Priority


User = get_user_model()


class MilestoneCrudTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='test-pass-123')
        self.other_user = User.objects.create_user(username='bob', password='test-pass-123')
        self.goal = Goal.objects.create(
            user=self.user,
            title='Learn Django Forms',
            priority=Priority.HIGH,
        )
        self.other_goal = Goal.objects.create(user=self.other_user, title='Learn SQL')
        self.milestone = Milestone.objects.create(
            goal=self.goal,
            title='Study ModelForms',
            notes='Read docs and build one form.',
            order=1,
        )
        self.other_milestone = Milestone.objects.create(
            goal=self.other_goal,
            title='Study joins',
            order=1,
        )

    def test_milestone_create_requires_login(self):
        response = self.client.get(reverse('milestone_create', args=[self.goal.id]))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('milestone_create', args=[self.goal.id])}",
        )

    def test_user_can_create_milestone_for_own_goal(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('milestone_create', args=[self.goal.id]),
            {
                'title': 'Render errors',
                'notes': 'Practice invalid form states.',
                'due_date': '2026-07-02',
                'order': 2,
            },
        )

        milestone = Milestone.objects.get(title='Render errors')
        self.assertEqual(milestone.goal, self.goal)
        self.assertRedirects(response, reverse('goal_detail', args=[self.goal.id]))

    def test_user_cannot_create_milestone_for_another_users_goal(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('milestone_create', args=[self.other_goal.id]),
            {
                'title': 'Changed',
                'notes': '',
                'due_date': '',
                'order': 2,
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Milestone.objects.filter(goal=self.other_goal, title='Changed').exists())

    def test_goal_detail_shows_milestones_and_actions(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('goal_detail', args=[self.goal.id]))

        self.assertContains(response, self.milestone.title)
        self.assertContains(response, reverse('milestone_create', args=[self.goal.id]))
        self.assertContains(response, reverse('milestone_edit', args=[self.milestone.id]))

    def test_user_can_edit_own_milestone_but_not_another_users_milestone(self):
        self.client.force_login(self.user)

        update_response = self.client.post(
            reverse('milestone_edit', args=[self.milestone.id]),
            {
                'title': 'Master ModelForms',
                'notes': self.milestone.notes,
                'due_date': '',
                'order': 3,
            },
        )
        blocked_response = self.client.post(
            reverse('milestone_edit', args=[self.other_milestone.id]),
            {
                'title': 'Changed',
                'notes': '',
                'due_date': '',
                'order': 1,
            },
        )

        self.milestone.refresh_from_db()
        self.other_milestone.refresh_from_db()
        self.assertRedirects(update_response, reverse('goal_detail', args=[self.goal.id]))
        self.assertEqual(self.milestone.title, 'Master ModelForms')
        self.assertEqual(self.milestone.order, 3)
        self.assertEqual(blocked_response.status_code, 404)
        self.assertEqual(self.other_milestone.title, 'Study joins')

    def test_user_can_delete_own_milestone_but_not_another_users_milestone(self):
        self.client.force_login(self.user)

        blocked_response = self.client.post(reverse('milestone_delete', args=[self.other_milestone.id]))
        delete_response = self.client.post(reverse('milestone_delete', args=[self.milestone.id]))

        self.assertEqual(blocked_response.status_code, 404)
        self.assertRedirects(delete_response, reverse('goal_detail', args=[self.goal.id]))
        self.assertFalse(Milestone.objects.filter(id=self.milestone.id).exists())
        self.assertTrue(Milestone.objects.filter(id=self.other_milestone.id).exists())


class MilestoneApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='test-pass-123')
        self.other_user = User.objects.create_user(username='bob', password='test-pass-123')
        self.goal = Goal.objects.create(user=self.user, title='Learn Django Forms')
        self.other_goal = Goal.objects.create(user=self.other_user, title='Learn SQL')
        self.first = Milestone.objects.create(goal=self.goal, title='First', order=1)
        self.second = Milestone.objects.create(goal=self.goal, title='Second', order=2)
        self.other_milestone = Milestone.objects.create(goal=self.other_goal, title='Other', order=1)

    def test_toggle_requires_login(self):
        response = self.client.post(
            reverse('api_milestone_toggle', args=[self.first.id]),
            {'is_complete': True},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 302)

    def test_toggle_updates_completion_and_progress(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('api_milestone_toggle', args=[self.first.id]),
            {'is_complete': True},
            content_type='application/json',
        )

        self.first.refresh_from_db()
        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(body['ok'])
        self.assertTrue(self.first.is_complete)
        self.assertIsNotNone(self.first.completed_at)
        self.assertEqual(body['data']['goal_progress']['percentage'], 50)

    def test_toggle_rejects_invalid_payload_and_other_users_milestone(self):
        self.client.force_login(self.user)

        invalid_response = self.client.post(
            reverse('api_milestone_toggle', args=[self.first.id]),
            {'is_complete': 'yes'},
            content_type='application/json',
        )
        blocked_response = self.client.post(
            reverse('api_milestone_toggle', args=[self.other_milestone.id]),
            {'is_complete': True},
            content_type='application/json',
        )

        self.assertEqual(invalid_response.status_code, 400)
        self.assertFalse(invalid_response.json()['ok'])
        self.assertEqual(blocked_response.status_code, 404)

    def test_reorder_persists_new_order(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('api_milestone_reorder'),
            {
                'goal_id': self.goal.id,
                'milestone_ids': [self.second.id, self.first.id],
            },
            content_type='application/json',
        )

        self.first.refresh_from_db()
        self.second.refresh_from_db()
        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(body['ok'])
        self.assertEqual(self.second.order, 1)
        self.assertEqual(self.first.order, 2)
        self.assertEqual(
            [milestone['id'] for milestone in body['data']['milestones']],
            [self.second.id, self.first.id],
        )

    def test_reorder_rejects_milestones_outside_goal(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('api_milestone_reorder'),
            {
                'goal_id': self.goal.id,
                'milestone_ids': [self.first.id, self.other_milestone.id],
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])
