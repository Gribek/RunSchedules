from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
from django.views import View
from datetime import datetime
from calendar import HTMLCalendar
from RunScheduleApp.forms import *


class MainPageView(View):
    def get(self, request):
        return render(request, 'RunScheduleApp/main_page.html')


class WorkoutPlanAdd(PermissionRequiredMixin, View):
    permission_required = 'RunScheduleApp.add_workoutplan'

    def get(self, request):
        form = WorkoutPlanForm()
        return render(request, 'RunScheduleApp/workout_plan_add.html', {'form': form})

    def post(self, request):
        new_workout_plan = WorkoutPlan()
        form = WorkoutPlanForm(request.POST, instance=new_workout_plan)
        if form.is_valid():
            form.instance.owner = get_user(request)
            new_plan = form.save()
            if form.instance.is_active:
                set_active_workout_plan(new_plan.id, get_user(request))
            return redirect('/workout_list')
        return render(request, 'RunScheduleApp/workout_plan_add.html', {'form': form})


class WorkoutPlanEdit(PermissionRequiredMixin, View):
    permission_required = 'RunScheduleApp.change_workoutplan'

    def get(self, request, plan_id):
        workout_plan = WorkoutPlan.objects.get(pk=plan_id)
        check_workout_plan_owner(workout_plan, get_user(request))
        form = WorkoutPlanEditForm(instance=workout_plan)
        return render(request, 'RunScheduleApp/workout_plan_edit.html', {'form': form, 'plan_id': plan_id})

    def post(self, request, plan_id):
        workout_plan = WorkoutPlan.objects.get(pk=plan_id)
        form = WorkoutPlanEditForm(request.POST, instance=workout_plan)
        if form.is_valid():
            form.save()
            return redirect(f'/plan_details/{plan_id}')
        return render(request, 'RunScheduleApp/workout_plan_edit.html', {'form': form, 'plan_id': plan_id})


class PlanDetailsView(PermissionRequiredMixin, View):
    permission_required = 'RunScheduleApp.view_workoutplan'

    def get(self, request, id):
        workout_plan = WorkoutPlan.objects.get(pk=id)
        check_workout_plan_owner(workout_plan, get_user(request))
        month_number = get_month_number(workout_plan.date_range.lower)
        return render(request, 'RunScheduleApp/plan_details.html',
                      {'workout_plan': workout_plan, 'month_number': month_number})


class WorkoutsList(LoginRequiredMixin, View):
    def get(self, request):
        workout_plans = WorkoutPlan.objects.filter(owner=get_user(request))
        return render(request, 'RunScheduleApp/workoutplan_list.html', {'workout_plans': workout_plans})


class DailyTrainingAdd(PermissionRequiredMixin, View):
    permission_required = 'RunScheduleApp.add_dailytraining'

    def get(self, request, id, date=None):
        workout_plan = WorkoutPlan.objects.get(pk=id)
        check_workout_plan_owner(workout_plan, get_user(request))
        start_date, end_date = get_plan_start_and_end_date(workout_plan)
        form = DailyTrainingForm(initial={'day': date, 'start_date': start_date, 'end_date': end_date})
        return render(request, 'RunScheduleApp/daily_training_add.html', {'form': form, 'plan_id': workout_plan.id})

    def post(self, request, id, date=None):
        new_training = DailyTraining()
        form = DailyTrainingForm(request.POST, instance=new_training)
        workout_plan = WorkoutPlan.objects.get(pk=id)
        if form.is_valid():
            workout = WorkoutPlan.objects.get(pk=id)
            form.instance.workout_plan = workout
            form.save()
            return redirect(f'/plan_details/{id}')
        return render(request, 'RunScheduleApp/daily_training_add.html', {'form': form, 'plan_id': workout_plan.id})


class DailyTrainingEdit(PermissionRequiredMixin, View):
    permission_required = 'RunScheduleApp.change_dailytraining'

    def get(self, request, plan_id, id):
        workout_plan = WorkoutPlan.objects.get(pk=plan_id)
        check_workout_plan_owner(workout_plan, get_user(request))
        daily_training = DailyTraining.objects.get(pk=id)
        start_date, end_date = get_plan_start_and_end_date(workout_plan)
        form = DailyTrainingForm(instance=daily_training, initial={'start_date': start_date, 'end_date': end_date})
        return render(request, 'RunScheduleApp/daily_training_add.html', {'form': form, 'plan_id': plan_id})

    def post(self, request, plan_id, id):
        daily_training = DailyTraining.objects.get(pk=id)
        form = DailyTrainingForm(request.POST, instance=daily_training)
        if form.is_valid():
            form.save()
            return redirect(f'/plan_details/{plan_id}')
        return render(request, 'RunScheduleApp/daily_training_add.html', {'form': form, 'plan_id': plan_id})


class DailyTrainingDelete(PermissionRequiredMixin, View):
    permission_required = 'RunScheduleApp.delete_dailytraining'

    def get(self, request, id):
        daily_training = DailyTraining.objects.get(pk=id)
        check_workout_plan_owner(daily_training.workout_plan, get_user(request))
        daily_training.delete()
        return redirect(f'/plan_details/{daily_training.workout_plan.id}')


class SelectActivePlanView(PermissionRequiredMixin, View):
    permission_required = 'RunScheduleApp.view_workoutplan'

    @staticmethod
    def get_user_plans(request):
        all_user_plans = WorkoutPlan.objects.filter(owner=request.user)
        plan_name_array = []
        plan_id_array = []
        for plan in all_user_plans:
            plan_id_array.append(plan.plan_name)
            plan_name_array.append(plan.id)
        return tuple(zip(plan_name_array, plan_id_array))

    def get(self, request):
        plans_tuple = SelectActivePlanView.get_user_plans(request)
        form = SelectActivePlanFrom(choices=plans_tuple)
        return render(request, 'RunScheduleApp/select_plan.html', {'form': form})

    def post(self, request):
        plans_tuple = SelectActivePlanView.get_user_plans(request)
        form = SelectActivePlanFrom(request.POST, choices=plans_tuple)
        if form.is_valid():
            new_active_plan_id = form.cleaned_data.get('active_plan')
            set_active_workout_plan(new_active_plan_id, request.user)
            return redirect('/workout_list')
        return render(request, 'RunScheduleApp/select_plan.html', {'form': form})


class CurrentWorkoutPlanView(LoginRequiredMixin, View):
    def get(self, request, month_number_requested):
        if not WorkoutPlan.objects.filter(owner=get_user(request)).filter(is_active=True).exists():
            return render(request, 'RunScheduleApp/current_workout_plan.html', {'workout_plan': ''})
        workout_plan = WorkoutPlan.objects.filter(owner=get_user(request)).filter(is_active=True)[0]

        # Month numbers indicates numbers of the following months in the training plan - 1.
        # Number of the first month of workout plan is always equal to 0.
        # present_month_number indicate number for the present month (according to date) in training workout plan.
        plan_start_date, plan_end_date = get_plan_start_and_end_date(workout_plan)
        last_month_number = get_last_month_number(plan_start_date, plan_end_date)
        present_month_number = get_month_number(plan_start_date)

        # Creating a new object of WorkoutCalendar class.
        month, year = CurrentWorkoutPlanView.get_month_and_year(month_number_requested, plan_start_date)
        cal = WorkoutCalendar(workout_plan, month, year).formatmonth(year, month)

        ctx = {'workout_plan': workout_plan,
               'calendar': mark_safe(cal),
               'month_number_requested': month_number_requested,
               'last_month_number': str(last_month_number),
               'present_month_number': present_month_number
               }
        return render(request, 'RunScheduleApp/current_workout_plan.html', ctx)

    @staticmethod
    def get_month_and_year(month_number_requested, plan_start_date):
        plan_first_month = plan_start_date.month
        plan_first_year = plan_start_date.year
        # Variables month and year for WorkoutCalendar formatmonth method.
        month = plan_first_month + int(month_number_requested)
        year = plan_first_year
        # Recalculation mechanism for plans exceeding a calendar year.
        if month > 12:
            year = plan_first_year + int(month / 12)
            month = month % 12
            if month == 0:  # Amendment for december, for which the rest from dividing by 12 is always 0
                month = 12
                year -= 1
        return month, year


class WorkoutCalendar(HTMLCalendar):
    cssclass_month = 'month table'

    def __init__(self, workout_plan, month_number, year_number):
        super(WorkoutCalendar, self).__init__()
        self.month_number = month_number
        self.year_number = year_number
        self.workout_plan = workout_plan
        self.workout_plan_start_date, self.workout_plan_end_date = get_plan_start_and_end_date(workout_plan)
        self.training_dict = self.get_trainings_dict()

    def formatday(self, day, weekday):
        """
        Return a day as a table cell.
        """
        if day == 0:  # Table cells for days 'outside' the month.
            return '<td class="noday">&nbsp;</td>'

        if str(day) in self.training_dict:  # Training days.
            bg_color = self.set_bg_color(day, True)
            edit_day_link = self.create_training_day_edit_link(day)
            return '<td bgcolor= "%s" class="%s"><a href="%s">%d<br>%s</a></td>' % (
                bg_color, self.cssclasses[weekday], edit_day_link, day, self.training_dict[str(day)])

        else:  # Non-training days.
            bg_color = self.set_bg_color(day, False)
            edit_day_link = f"/daily_training_add/{self.workout_plan.id}/{self.create_date(day)}"
            return '<td bgcolor= "%s" class="%s"><a href="%s">%d</a></td>' % (
                bg_color, self.cssclasses[weekday], edit_day_link, day)

    def formatmonth(self, theyear, themonth, withyear=True):
        """
        Return a formatted month as a table.
        """
        v = []
        a = v.append
        a(
            '<table id="fixedheight" style="table-layout: fixed" border="0" cellpadding="0" cellspacing="0" class="%s">'
            % self.cssclass_month)
        a('\n')
        a(self.formatmonthname(theyear, themonth, withyear=withyear))
        a('\n')
        a(self.formatweekheader())
        a('\n')
        for week in self.monthdays2calendar(theyear, themonth):
            a(self.formatweek(week))
            a('\n')
        a('</table>')
        a('\n')
        return ''.join(v)

    def create_training_day_edit_link(self, day):
        date = self.create_date(day)
        daily_training_id = DailyTraining.objects.filter(workout_plan=self.workout_plan).get(
            day=date).id
        edit_day_link = f'/daily_training_edit/{self.workout_plan.id}/{daily_training_id}'
        return edit_day_link

    def create_date(self, day):
        date = f"{self.year_number}-{self.month_number}-{day}"  # Creates a full date for this day.
        date_format_datetime = datetime.strptime(date, "%Y-%m-%d").date()
        return date_format_datetime

    def set_bg_color(self, day, is_training_day):
        date = self.create_date(day)
        if date == self.workout_plan_start_date:
            return 'greenyellow'
        elif date == self.workout_plan_end_date:
            return '#ff6666'
        if is_training_day:
            return '#798EF6'
        else:
            return ''

    def get_trainings_dict(self):
        trainings = self.workout_plan.dailytraining_set.filter(day__year=self.year_number).filter(
            day__month=self.month_number).order_by('day')
        training_dict = {}
        for training in trainings:
            training_dict.update({f'{training.day.day}': training.name()})
        return training_dict


class LoginView(View):

    def get(self, request):
        form = LoginForm()
        return render(request, 'RunScheduleApp/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('user')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next = request.GET.get('next')
                if next is not None:
                    return redirect(next)
                return redirect('/')
            else:
                return render(request, 'RunScheduleApp/login.html', {'form': form})
        return render(request, 'RunScheduleApp/login.html', {'form': form})


class LogoutView(View):
    def get(self, request):
        if request.user.is_authenticated:
            logout(request)
            return redirect('/')
        else:
            return HttpResponse('Nie jesteś zalogowany')


class RegistrationView(View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, 'RunScheduleApp/registration.html', {'form': form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            name = form.cleaned_data.get('name')
            surname = form.cleaned_data.get('surname')
            email = form.cleaned_data.get('email')
            User.objects.create_user(username=username, password=password, email=email, first_name=name,
                                     last_name=surname)
            new_user = User.objects.get(username=username)
            permission_list = [
                'add_dailytraining',
                'change_dailytraining',
                'delete_dailytraining',
                'view_dailytraining',
                'add_workoutplan',
                'change_workoutplan',
                'delete_workoutplan',
                'view_workoutplan',
            ]
            permissions = [Permission.objects.get(codename=i) for i in
                           permission_list]  # Create list of permission type objects.
            new_user.user_permissions.set(permissions)
            return redirect('/login')
        return render(request, 'RunScheduleApp/registration.html', {'form': form})


class UserProfileView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'RunScheduleApp/user_profile.html')


class PasswordChangeView(LoginRequiredMixin, View):
    def get(self, request):
        form = PasswordChangeForm()
        return render(request, 'RunScheduleApp/password_change.html', {'form': form})

    def post(self, request):
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data.get('new_password')
            if not request.user.is_authenticated:
                return redirect('/')
            current_user = request.user
            current_user.set_password(new_password)
            current_user.save()
            return redirect('/login')
        return render(request, 'RunScheduleApp/password_change.html', {'form': form})


class EditUserView(LoginRequiredMixin, View):
    def get(self, request):
        current_user = request.user
        form = EditUserForm(instance=current_user)
        return render(request, 'RunScheduleApp/edit_user_profile.html', {'form': form})

    def post(self, request):
        form = EditUserForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('/profile')
        return render(request, 'RunScheduleApp/edit_user_profile.html', {'form': form})


def get_plan_start_and_end_date(workout_plan):
    start_date = workout_plan.date_range.lower
    end_date = workout_plan.date_range.upper
    return start_date, end_date


# Calculates month number for present month (according to date).
def get_month_number(plan_start_date):
    day_now = datetime.today().date()
    month_counter = (day_now.year - plan_start_date.year) * 12 + day_now.month - plan_start_date.month
    return month_counter


# Calculates month number for the last month of current workout plan.
def get_last_month_number(plan_start_date, plan_end_date):
    month_max_number = (plan_end_date.year - plan_start_date.year) * 12 + plan_end_date.month - plan_start_date.month
    return month_max_number


def get_user(request):
    return request.user


def check_workout_plan_owner(workout_plan, user):
    if workout_plan.owner != user:
        raise PermissionDenied


def set_active_workout_plan(new_active_plan_id, user):
    WorkoutPlan.objects.filter(owner=user).filter(is_active=True).update(is_active=False)
    new_active_plan = WorkoutPlan.objects.get(pk=new_active_plan_id)
    new_active_plan.is_active = True
    new_active_plan.save()
    return None
