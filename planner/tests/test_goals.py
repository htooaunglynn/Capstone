from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from planner.models import Goal, GoalStatus, Priority


User = get_user_model()


class GoalCrudTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='test-pass-123')
        self.other_user = User.objects.create_user(username='bob', password='test-pass-123')
        self.goal = Goal.objects.create(
            user=self.user,
            title='Learn Django Forms',
            description='Practice validation and form rendering.',
            category='Django',
            priority=Priority.HIGH,
            status=GoalStatus.ACTIVE,
        )
        self.other_goal = Goal.objects.create(
            user=self.other_user,
            title='Learn SQL',
            category='Databases',
            priority=Priority.LOW,
            status=GoalStatus.PAUSED,
        )

    def test_goal_list_requires_login(self):
        response = self.client.get(reverse('goal_list'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('goal_list')}")

    def test_goal_list_shows_only_current_users_goals(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('goal_list'))

        self.assertContains(response, self.goal.title)
        self.assertNotContains(response, self.other_goal.title)

    def test_goal_list_supports_search_status_and_priority_filters(self):
        Goal.objects.create(
            user=self.user,
            title='Learn Python Testing',
            category='Python',
            priority=Priority.LOW,
            status=GoalStatus.ARCHIVED,
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('goal_list'),
            {'q': 'django', 'status': GoalStatus.ACTIVE, 'priority': Priority.HIGH},
        )

        self.assertContains(response, self.goal.title)
        self.assertNotContains(response, 'Learn Python Testing')

    def test_goal_detail_is_user_scoped(self):
        self.client.force_login(self.user)

        own_response = self.client.get(reverse('goal_detail', args=[self.goal.id]))
        other_response = self.client.get(reverse('goal_detail', args=[self.other_goal.id]))

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(other_response.status_code, 404)

    def test_user_can_create_goal(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('goal_create'),
            {
                'title': 'Learn REST APIs',
                'description': 'Build authenticated API endpoints.',
                'category': 'Backend',
                'priority': Priority.MEDIUM,
                'status': GoalStatus.ACTIVE,
                'target_date': '2026-07-01',
            },
        )

        goal = Goal.objects.get(title='Learn REST APIs')
        self.assertEqual(goal.user, self.user)
        self.assertRedirects(response, reverse('goal_detail', args=[goal.id]))

    def test_user_can_update_own_goal_but_not_another_users_goal(self):
        self.client.force_login(self.user)

        update_response = self.client.post(
            reverse('goal_edit', args=[self.goal.id]),
            {
                'title': 'Master Django Forms',
                'description': self.goal.description,
                'category': self.goal.category,
                'priority': Priority.MEDIUM,
                'status': GoalStatus.PAUSED,
                'target_date': '',
            },
        )
        blocked_response = self.client.post(
            reverse('goal_edit', args=[self.other_goal.id]),
            {
                'title': 'Changed',
                'description': '',
                'category': '',
                'priority': Priority.HIGH,
                'status': GoalStatus.ACTIVE,
                'target_date': '',
            },
        )

        self.goal.refresh_from_db()
        self.other_goal.refresh_from_db()
        self.assertRedirects(update_response, reverse('goal_detail', args=[self.goal.id]))
        self.assertEqual(self.goal.title, 'Master Django Forms')
        self.assertEqual(blocked_response.status_code, 404)
        self.assertEqual(self.other_goal.title, 'Learn SQL')

    def test_user_can_delete_own_goal_but_not_another_users_goal(self):
        self.client.force_login(self.user)

        blocked_response = self.client.post(reverse('goal_delete', args=[self.other_goal.id]))
        delete_response = self.client.post(reverse('goal_delete', args=[self.goal.id]))

        self.assertEqual(blocked_response.status_code, 404)
        self.assertRedirects(delete_response, reverse('goal_list'))
        self.assertFalse(Goal.objects.filter(id=self.goal.id).exists())
        self.assertTrue(Goal.objects.filter(id=self.other_goal.id).exists())
