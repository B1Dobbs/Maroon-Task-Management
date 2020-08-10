from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.base import RedirectView
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.utils.translation import ugettext as _
from django.contrib.auth import logout
from rest_framework import status
from .models import Profile, Project, Role, User, Ticket, State, Attribute, Type, AttributeType, RelationshipType
from .forms import RegisterForm, ProfilePicForm, NewProjectForm, UserDeleteForm, TicketForm, UserUpdate, TicketDetailForm
from bootstrap_modal_forms.generic import BSModalCreateView
from django.http import HttpResponse, HttpResponseRedirect
from rest_framework.authtoken.models import Token
# from .forms import UserDeleteForm
from django.db.models import Q
from .filters import TicketFilter
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django import forms
# Create your views here.

# Create your views here.
import json

class Redirect(RedirectView):
    permanent = False
    query_string = True
    pattern_name = 'landing'

class Landing(LoginRequiredMixin,View): 
    login_url = 'login'
    landing_template = "landing.html"
    landing_empty_template = "landing_none_selected.html"

    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            project = get_object_or_404(Project, pk=kwargs['pk'])
            tickets = Ticket.objects.filter(project=project)
            if not request.GET._mutable:
                request.GET._mutable = True
            request.GET['pk'] = project.pk
            myFilter = TicketFilter(request.GET, request=request, queryset=tickets)
            tickets = myFilter.qs
            context = {'project': project, 
                'project': project, 
                'myFilter':myFilter, 
                'tickets':tickets, 
                'template_name': self.landing_template, 
                'ticket_form': TicketForm(), 
                'project_profiles': [ role.profile for role in project.roles.all()], 
                'token':Token.objects.get_or_create(user=request.user)[0]}
            return render(request, self.landing_template, context)
        else:
            return render(request, self.landing_empty_template)

    def post(self, request, *args, **kwargs):
        form = TicketForm(request.POST)
        project = get_object_or_404(Project, pk=kwargs['pk'])
        context = {'project': project, 
                'template_name': self.landing_template, 
                'project_profiles': [ role.profile for role in project.roles.all()]}

        if form.is_valid():
            title = form.cleaned_data.get('title')
            type = form.cleaned_data.get('type')
            state = form.cleaned_data.get('state')
            description = form.cleaned_data.get('description')
            assignees = form.cleaned_data.get('assignees')

            ticket = Ticket(project=project, title=title, type=type, state=state, description=description)
            ticket.save()
            ticket.assignees.set(assignees)
            context['ticket_form'] = TicketForm() 
            url = reverse('landing', kwargs={'pk': project.pk})
            return HttpResponseRedirect(url)
        context['ticket_form'] = form
        return render(request, self.landing_template, context)


class Account(LoginRequiredMixin,View):
    login_url = 'login'
    template_name = "user/account.html"

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        token = Token.objects.get(user=request.user)
        form = UserUpdate()
        context = {"profile":profile, "user_token":token, 'form':form}
        return render(request, self.template_name, context)

    def post(self, request):
        form = UserUpdate(data=request.POST, instance=request.user)
        token = Token.objects.get(user=request.user)
        if form.is_valid():
            form.save()
            profile = Profile.objects.get(user=request.user)
            context = {"profile":profile, "user_token":token}
            return render(request, self.template_name, context)
        profile = Profile.objects.get(user=request.user)
        context = {"profile":profile,"user_token":token, 'form':form}
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
        #print(project_id)
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
        #print(project.ticket_template.states.all())
        profile = Profile.objects.get(user=request.user)
        role = Role.objects.get(profile= profile, project= project)
        # is_admin = role =='is_admin'
        states = State.objects.filter(ticket_template=project.ticket_template).all()
        types = Type.objects.filter(ticket_template=project.ticket_template)
        attributes = AttributeType.objects.filter(ticket_template=project.ticket_template)
        relationships = RelationshipType.objects.filter(ticket_template=project.ticket_template)
        admin = Role.objects.filter(project=project,role="is_admin")
        collaborators = Role.objects.filter(project=project, role="is_normal")
        context = {'project': project, 'role':role, 'states': states, 'types': types, 'attributes': attributes, 'relationships': relationships, 'admin':admin,'collaborators':collaborators}
        return render(request, self.template_name, context)
   
    def post(self, request, *args, **kwargs):
        project_id = kwargs.get('pk')
        project = get_object_or_404(Project, pk=project_id)
        response = request.POST
        #For Update Project in Detatil Tab
        if response.get('section') =='edit_project':
            project.name = response['title']
            project.description = response['description']
            project.save()
            #return render(request, self.template_name, {'project': project})
        #For Upload Profile Picture
        if response.get('section') == 'upload_pic':
            project_id = kwargs.get('pk')
            form = ProfilePicForm(request.POST, request.FILES)
            project = get_object_or_404(Project, pk=project_id)
            if form.is_valid():
                project.avatar = form.cleaned_data['image']
                project.save()
                #return render(request, self.template_name, {'project':project})
            else:
                project.avatar = None #Delete profile
                project.save()
        if response.get('section') =='delete_project':
            project.delete()   
            return redirect('landing')
        if response.get('section') == 'ticket_template':
            #print(response)
            project_id = kwargs.get('pk')
            #print(project_id)
            project = get_object_or_404(Project, pk=project_id)
            
            #Update/Create States
            state_queryset = State.objects.filter(ticket_template=project.ticket_template).all()

            num_states = int(response.get('state-number'))
            for state in state_queryset[num_states:]:
                state.delete()

            for i in range(0, num_states):
                if i < len(state_queryset):
                    state = state_queryset[i]
                    state.state_name = remove_empty_string(response.get('state-name' + str(i+1)))
                    state.color = response.get('state-color' + str(i+1))
                    state.position = int(response.get('state-position' + str(i+1)))
                    state.save()
                else:
                    state = State(ticket_template=project.ticket_template, state_name=remove_empty_string(response.get('state-name' + str(i+1))), color=response.get('state-color' + str(i+1)), position=int(response.get('state-position' + str(i+1))))
                    state.save()

            #Update/Create Types
            type_queryset = Type.objects.filter(ticket_template=project.ticket_template).all()

            num_types = int(response.get('type-number'))
            for type_obj in type_queryset[num_types:]:
                type_obj.delete()

            for i in range(0, num_types):
                if i < len(type_queryset):
                    type_obj = type_queryset[i]
                    type_obj.type_name = remove_empty_string(response.get('type-name' + str(i+1)))
                    type_obj.color = response.get('type-color' + str(i+1))
                    type_obj.save()
                else:
                    type_obj = Type(ticket_template=project.ticket_template, type_name=remove_empty_string(response.get('type-name' + str(i+1))), color=response.get('type-color' + str(i+1)))
                    type_obj.save()

            #Update/Create AttributeType
            attribute_queryset = AttributeType.objects.filter(ticket_template=project.ticket_template).all()

            num_attributes = int(response.get('attribute-number'))
            for attribute_type in attribute_queryset[num_attributes:]:
                attribute_type.delete()

            for i in range(0, num_attributes):
                if i < len(attribute_queryset):
                    attribute_type = attribute_queryset[i]
                    attribute_type.name = remove_empty_string(response.get('attribute-name' + str(i+1)))
                    attribute_type.save()
                else:
                    attribute_type = AttributeType(ticket_template=project.ticket_template, name=remove_empty_string(response.get('attribute-name' + str(i+1))))
                    attribute_type.save()

            #Update/Create RelationshipType
            relationship_queryset = RelationshipType.objects.filter(ticket_template=project.ticket_template).all()

            num_relationships = int(response.get('relationship-number'))
            for relationship_type in relationship_queryset[num_relationships:]:
                relationship_type.delete()

            for i in range(0, num_relationships):
                if i < len(relationship_queryset):
                    relationship_type = relationship_queryset[i]
                    relationship_type.name = remove_empty_string(response.get('relationship-name' + str(i+1)))
                    relationship_type.save()
                else:
                    relationship_type = RelationshipType(ticket_template=project.ticket_template, name=remove_empty_string(response.get('relationship-name' + str(i+1))))
                    relationship_type.save()

        #Demote user from project
        if response.get('section') == 'demote_user':
            username = response.get('username')
            user = User.objects.get(username=username)
            profile = Profile.objects.get(user=user)
            role = Role.objects.get(project=project, profile=profile)
            role.role = "is_normal"
            role.save()
  
        #Delete user from project
        if response.get('section') == 'delete_user':
            username = response.get('username')
            user = User.objects.get(username=username)
            profile = Profile.objects.get(user=user)
            project.roles.get(profile=profile).delete()
            project.save()

        #Add User to project
        if response.get('section') == "add_user":
            project = get_object_or_404(Project, pk=project_id)
            username = response.get('username')
            roles = response.get('role')
            if not User.objects.filter(username = username).exists():
                return HttpResponseNotFound("<h1>User does not exist!</h1>")            
            user = User.objects.get(username=username)
            profile = Profile.objects.get(user=user)
            if Role.objects.filter(profile=profile, project=project).exists():
                return HttpResponseBadRequest("<h1>User and Role already exist!</h1>")
            role = Role(profile=profile, role=roles, project=project)
            role.save()

        url = reverse('project', kwargs={'pk': kwargs.get('pk')})
        return HttpResponseRedirect(url)

class CreateProject(LoginRequiredMixin, BSModalCreateView):
    login_url = 'login' 
    template_name = 'landing.html'
    form_class = NewProjectForm
    #success_message = 'Success: Project was created.'
    #success_url = reverse_lazy('index')

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        #Processes request if valid
        if form.is_valid():
            # form.save()
            name = form.cleaned_data.get('name')
            project = Project(name=name)
            project.save(user=request.user)
            #context = {'project': project, 'new_project_form': form}
            #Redirect to new project
            return redirect('landing', pk=project.pk) #render(request, self.template_name, context)

        #If invalid, show form is not working because you would need to 
        #reload previous page and pass POST data as well.
        #Decided to redirect to previous page for now
        next = request.POST.get('next', '/')
        return HttpResponseRedirect(next)
        #context = {'project': Project.objects.get(pk=kwargs.get('pk')),'new_project_form': form}
        #return redirect('landing', pk=kwargs.get('pk'), form=form )
        #return render(request, self.template_name, context)

def deleteuser(request):
    if request.method == 'POST':
        delete_form = UserDeleteForm(request.POST, instance=request.user)
        user = request.user
        user.is_active = False
        user.save()
        messages.info(request, 'Your account has been deleted.')
        return redirect('login')
    else:
        delete_form = UserDeleteForm(instance=request.user)

    context = {
        'delete_form': delete_form
    }

    return render(request, 'user/delete.html', context)

class AccessSettings(LoginRequiredMixin,View):
    login_url = 'login'
    template_name = "project/management/container.html"

    def get(self, request, *args, **kwargs):
        project_id = kwargs.get('pk')
        project = get_object_or_404(Project, pk=project_id)
        profile = Profile.objects.get(user=request.user)
        role = Role.objects.get(profile= profile, project= project).role
        # users = User.objects.all().filter(profile= profile)
        # is_admin = role =='is_admin'
        print(role)
        context = {'project': project, 'role':role}
        return render(request, self.template_name, context)
    
    def add_user_to_project(request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        if request.method == "POST":
            form = AddUserForm(request.POST)
            if form.is_valid():
                project.users.add(form.cleaned_data["user"])
                return redirect("access")
        else:
            form = AddUserForm()
        return render(request, "add_user.html", {"project": project, "form": form})

class TicketDetail(LoginRequiredMixin,View):
    login_url = 'login'
    template_name = "ticket/ticket_detail.html"
    form_class = TicketDetailForm

    def get(self, request, *args, **kwargs):
        ticket = Ticket.objects.get(pk=kwargs.get('pk'))
        form = TicketDetailForm(initial=ticket.__dict__)
        context = {
            'form': form, 
            'ticket': ticket,
            'ticket_id': ticket.id_in_project,
            'project':ticket.project,
            'project_profiles': [ role.profile for role in ticket.project.roles.all()],
            'token':Token.objects.get(user=request.user)
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):

        #Getting attributes straight from post request, django form ignores extra fields in post request
        ticket = Ticket.objects.get(pk=kwargs.get('pk'))
        for attributeType in ticket.project.ticket_template.attributeTypes.all():
            attr_value = request.POST.get(attributeType.name)
            attribute, created = Attribute.objects.get_or_create(attribute_type=attributeType, ticket=ticket)
            attribute.value = attr_value
            attribute.save()

        #Handle rest of form here
        form = self.form_class(request.POST, instance=ticket)
        if form.is_valid():
            form.save()    
            #Redirect after valid form
            url = reverse('ticket', kwargs={'pk': kwargs.get('pk')})
            return HttpResponseRedirect(url)
        context = {
            'form': form, 
            'ticket': ticket, 
            'project':ticket.project,
            'project_profiles': [ role.profile for role in ticket.project.roles.all()],
            'token':Token.objects.get(user=request.user)
        }
        return render(request, self.template_name, context)

def remove_empty_string(string):
    if not string:
        string = 'Placeholder'
    return string
