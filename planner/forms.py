"""Forms for the SkillSprint planner app."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Goal, Milestone, PracticeSession


User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['title', 'description', 'category', 'priority', 'status', 'target_date']
        widgets = {
            'target_date': forms.DateInput(attrs={'type': 'date'}),
        }


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['title', 'notes', 'due_date', 'order']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }


class PracticeSessionForm(forms.ModelForm):
    class Meta:
        model = PracticeSession
        fields = ['goal', 'milestone', 'scheduled_for', 'duration_minutes', 'status', 'notes']
        widgets = {
            'scheduled_for': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, user=None, goal=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fixed_goal = goal

        goals = Goal.objects.none()
        milestones = Milestone.objects.none()

        if user is not None:
            goals = Goal.objects.filter(user=user)
            milestones = Milestone.objects.filter(goal__user=user)

        if goal is not None:
            goals = goals.filter(id=goal.id)
            milestones = goal.milestones.all()
            self.fields['goal'].initial = goal
            self.fields['goal'].disabled = True

        if self.instance.pk and self.instance.goal_id:
            milestones = Milestone.objects.filter(goal=self.instance.goal)

        self.fields['goal'].queryset = goals
        self.fields['milestone'].queryset = milestones
        self.fields['milestone'].required = False

    def clean_goal(self):
        if self.fixed_goal is not None:
            return self.fixed_goal
        return self.cleaned_data['goal']

    def clean(self):
        cleaned_data = super().clean()
        goal = cleaned_data.get('goal')
        milestone = cleaned_data.get('milestone')

        if goal and self.user and goal.user_id != self.user.id:
            self.add_error('goal', 'Select one of your goals.')

        if milestone and goal and milestone.goal_id != goal.id:
            self.add_error('milestone', 'Select a milestone from the chosen goal.')

        return cleaned_data
