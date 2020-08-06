from django.shortcuts import render, redirect
from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.base import RedirectView
from django.http import HttpResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext as _
from django.contrib.auth import logout
# from .forms import UserDeleteForm
from .models import Profile, Project
from .forms import RegisterForm, ProfilePicForm, NewProjectForm
from bootstrap_modal_forms.generic import BSModalCreateView
# Create your views here.


class Redirect(RedirectView):
    permanent = False
    query_string = True
    pattern_name = 'landingNoneSelected'

class LandingNoneSelected(LoginRequiredMixin,View):  # Will later add: LoginRequredMixin
    login_url = 'login'
    template_name = "landing_none_selected.html"

    def get(self, request):
        project = "Project one"
        project_2 = "Project two"
        context = {
            'some_value': project,
            'some_other_value': project_2,
        }
        return render(request, self.template_name, context)


class Landing(LoginRequiredMixin,View):  # Will later add: LoginRequredMixin
    login_url = 'login'
    template_name = "landing.html"

    def get(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=kwargs['pk'])
        context = {'project': project}
        return render(request, self.template_name, context)


class Account(LoginRequiredMixin,View):  # Will later add: LoginRequredMixin
    login_url = 'login'
    template_name = "user/account.html"

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        context = {"profile":profile}
        return render(request, self.template_name, context)

    def post(self, request):
        error_message =""
        try:
            response = request.POST
            user = request.user
            user.first_name = response['fname']
            user.last_name = response['lname']
            user.username = response['username']
            user.email = response['email']
            user.save()
        except:
            error_message = "Username already exists!"

        profile = Profile.objects.get(user=request.user)
        context = {"profile":profile, "error":error_message}

        return render(request, self.template_name, context)
    


class Register(View):
    template_name = "registration/register.html"

    def get(self, request):
        form = RegisterForm()
        context = {'form': form}
        return render(request, self.template_name, context)

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user) #authenticate user and redirect them to landing page
            return redirect('landing')
        context = {'form': form}
        return render(request, self.template_name, context)

class UploadAvatar(LoginRequiredMixin, View):
    login_url = 'login'
    
    def post(self, request):
        form = ProfilePicForm(request.POST, request.FILES)
        m = Profile.objects.get(user=request.user)
        if form.is_valid():
            m.avatar = form.cleaned_data['image']
            m.save()
            return redirect('account')
        m.avatar = None #Delete profile
        m.save()
        return redirect('account')

class UploadProjectAvatar(LoginRequiredMixin, View):
    login_url = 'login'
    template_name = 'project/management/container.html'
    
    def post(self, request, *args, **kwargs):
        project_id = kwargs.get('pk')
        print(project_id)
        form = ProfilePicForm(request.POST, request.FILES)
        project = get_object_or_404(Project, pk=project_id)
        if form.is_valid():
            project.avatar = form.cleaned_data['image']
            project.save()
            return render(request, self.template_name, {'project':project})
        project.avatar = None #Delete profile
        project.save()
        return render(request, self.template_name, {'project':project})
class ProjectSettings(LoginRequiredMixin,View):
    login_url = 'login'
    template_name = "project/management/container.html"

    def get(self, request, *args, **kwargs):
        project_id = kwargs.get('pk')
        project = get_object_or_404(Project, pk=project_id)
        context = {'project': project}
        return render(request, self.template_name, context)


def logout_view(request):
    logout(request)
    return redirect('login')

# def deleteuser(self, request):
#     if request.method == 'POST':
#         delete_form = UserDeleteForm(request.POST, instance=request.user)
#         user = request.user
#         user.delete()
#         messages.info(request, 'Your account has been deleted.')
#         return redirect('login')
#     else:
#         delete_form = UserDeleteForm(instance=request.user)

#     context = {
#         'delete_form': delete_form
#     }

#     return render(request, 'user/delete-account.html', context)

    

    
    def post(self, request, *args, **kwargs):
        project_id = kwargs.get('pk')
        project = get_object_or_404(Project, pk=project_id)
        response = request.POST
        #For Project Detail Tab
        if response.get('section') =='detail':
            project.name = response['title']
            project.description = response['description']
            project.save()
            return render(request, self.template_name, {'project': project})

        context = {'project': project}
        return render(request, self.template_name, context)

class NewProjectView(BSModalCreateView):
    template_name = 'project/new_project.html'
    form_class = NewProjectForm
    success_message = 'Success: Project was created.'
    success_url = reverse_lazy('index')
