from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Project, Role, Ticket, Attribute, Comment, File
from django import forms
from bootstrap_modal_forms.forms import BSModalModelForm

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)

        for fieldname in ['username', 'email','password1', 'password2']:
            self.fields[fieldname].help_text = None

    def clean(self):
       super(UserCreationForm, self).clean()
       email = self.cleaned_data.get('email')
       if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email address already exists")
       return self.cleaned_data


class ProfilePicForm(forms.Form):
    image = forms.ImageField()
    class Meta:
        model = Profile    
        fields = ('avatar')

class UserDeleteForm(forms.ModelForm):
     class Meta:
         model = User
         fields = []   #Form has only submit button.  Empty "fields" list still necessary, though.
class NewProjectForm(BSModalModelForm):
    class Meta:
        model = Project
        fields = ['name']

class UserUpdate(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',)
    
class TicketForm(BSModalModelForm):
    description = forms.CharField(required=False)
    class Meta:
        model = Ticket
        fields = ['title','type','assignees','description']

class TicketDetailForm(forms.ModelForm):
    description = forms.CharField(required=False)
    class Meta:
        model = Ticket
        fields = ['title', 'state','type','assignees','description']

class AddRole(forms.ModelForm):
    username = forms.CharField(required=True)
    project_pk = forms.CharField(required=True)
    class Meta:
        model = Role
        fields = ['username', 'role','project_pk']

    def validate(self, data):
        print("Validating user")
        username = self.cleaned_data['username']
        if not User.objects.filter(username = username).exists():
            raise forms.ValidationError("User does not exist!") 
        profile = Profile.objects.get(user=User.objects.get(username=username))
        project = Project.objects.get(pk=data['project_pk'])
        if Role.objects.filter(profile=profile, project=project).exists():
            raise forms.ValidationError("User and Role already exist!")

    def save(self, project, commit=True):
        profile = Profile.objects.get(user=User.objects.get(username=self.username))
        role = Role(profile=profile, role=self.role, project=project)
        if commit:
            role.save()
        return role
