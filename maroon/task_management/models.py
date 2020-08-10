from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from colorful.fields import RGBColorField
from .upload_paths import get_file_upload_path
import os

#Refence:https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING) 
    avatar = models.ImageField(upload_to="avatars/users",help_text="Profile picture", blank=True )

    def get_user_projects(self, admin=None):
        query = Role.objects.filter(profile=self)
        if admin is True:
            query = query.filter(role="is_admin")
        elif admin is False:
            query = query.filter(role="is_normal")
        
        projects = []
        for role in query:
            projects.append(role.project)

        return projects

    def __str__(self):
        return self.user.username + " " + self.user.email

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        Token.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Project(models.Model):
    name = models.CharField(max_length=30, blank=False)
    description = models.TextField(max_length=200, blank=True)
    avatar = models.ImageField(upload_to="avatars/projects",help_text="Project Avatar", blank=True )
    max_ticket_id = models.IntegerField(default=0)
    
    #function to override model.save(). Does not override Model.objects.create(kwargs)
    def save(self, *args, **kwargs):
        user = None
        if kwargs.get('user'):
            user = kwargs.pop('user')
        created = False
        if not self.pk:
            created = True  
        super().save(*args, **kwargs)  # Call the "real" save() method.
        if created and user != None:
            profile = Profile.objects.get(user=user)
            Role.objects.create(profile=profile, project= self)
            TicketTemplate.objects.create(project=self)

    def __str__(self):
        return self.name

ROLES_CHOICES = (
    ("is_admin", "Admin"),
    ("is_normal","Normal"),
)
class Role(models.Model):
    role = models.CharField(max_length=10,choices=ROLES_CHOICES, default="is_admin", help_text="User role")
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="roles")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="roles")


class TicketTemplate(models.Model):
    # The project that this template will be applied to
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="ticket_template")

    def __str__(self):
        return self.project.name

class State(models.Model):
    # The ticket template that contains these states
    ticket_template = models.ForeignKey(TicketTemplate, on_delete=models.CASCADE, related_name="states")

    # The name of the state
    state_name = models.TextField(max_length=50)

    #color
    color = RGBColorField(default="#0000FF")

    # The position of the state relative to a specific ticket_template's other states
    position = models.IntegerField(default=-1)
    
    class Meta:
        ordering = ["position"]

    def __str__(self):
        return self.state_name

class Type(models.Model):
    # The ticket template that contains these types
    ticket_template = models.ForeignKey(TicketTemplate, on_delete=models.CASCADE, related_name="types")   

    # The name of the type
    type_name = models.TextField(max_length=50)
    
    #color
    color = RGBColorField(default="#0000FF")
    def __str__(self):
        return self.type_name

class AttributeType(models.Model):
    # The ticket template the attribute belongs to
    ticket_template = models.ForeignKey(TicketTemplate, on_delete=models.CASCADE, related_name="attributeTypes")
    # The name of the attribute
    name = models.TextField()

    def __str__(self):
        return self.name

class RelationshipType(models.Model):
    # Name of the relationship type
    name = models.TextField()
    # The ticket template the relationship belongs to
    ticket_template = models.ForeignKey(TicketTemplate, on_delete=models.CASCADE, related_name="relationshipTypes")

    def __str__(self):
        return self.name

class Comment(models.Model):
    # The ticket of the comment
    ticket = models.ForeignKey("Ticket", on_delete=models.CASCADE, related_name="comments")
    # The author of the comment
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")

    # The text of the comment
    body = models.TextField()
    # The date that the comment was created
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_date"]


class Ticket(models.Model):
    # The project of the ticket
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tickets")
    # The author of the ticket
    assignees = models.ManyToManyField(Profile, related_name="assignees", blank=True)

    #The ticket id within the project
    id_in_project = models.IntegerField(editable=False, default=0)

    # The title of the Ticket
    title = models.CharField(max_length=50)
    # The description of the Ticket
    description = models.CharField(max_length=200, default="")
    # The last date that the ticket was updated
    updated_date = models.DateTimeField(auto_now=True)
    # The date that the ticket was created
    created_date = models.DateTimeField(auto_now_add=True)
    #state of ticket
    state = models.ForeignKey(State, on_delete=models.SET_NULL, related_name="tickets", null=True)
    #type of ticket
    type = models.ForeignKey(Type, on_delete=models.SET_NULL, related_name="tickets", null=True)
  
    class Meta:
        ordering = ["created_date"]
        
    def save(self, *args, **kwargs):
        if self.pk == None:
            self.id_in_project = self.project.max_ticket_id + 1
            self.project.max_ticket_id = self.id_in_project
            self.project.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    #To display attributes that may not exist for a ticket yet but are 
    #part of the ticket template
    def get_attribute_dict(self):
        attribute_dict = {}
        for attributeType in self.project.ticket_template.attributeTypes.all():
            if self.attributes.filter(attribute_type=attributeType).exists():
                attribute_dict[attributeType.name] = self.attributes.get(attribute_type=attributeType).value
            else:
                attribute_dict[attributeType.name] = ""
        return attribute_dict

class Attribute(models.Model):
    # The parent of the attribute
    attribute_type = models.ForeignKey(AttributeType, on_delete=models.CASCADE, related_name="attributes")
    # For simplicity value will be a text field to accept any alphanumeric value
    value = models.TextField()
    # For ticket to have more than one Attributes
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attributes", blank=True)

class Relationship(models.Model):
    # The parent of the attribute
    relationship_type = models.ForeignKey(RelationshipType, on_delete=models.CASCADE, related_name="relationships")
    # Ticket that has the relationships
    ticket_1 = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="relationships", blank=True, null=True)
    # Other ticket that is in this instance of a relationship
    ticket_2 = models.ForeignKey(Ticket, on_delete=models.DO_NOTHING, related_name="related_ticket", blank=True)

    def __str__(self):
        return self.relationship_type.name

class File(models.Model):
    # The parent of the file
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="files")

    # The name of the File
    name = models.CharField(max_length=200)
    # The file
    file = models.FileField(upload_to=get_file_upload_path)
    # The date that the file was created
    created_date = models.DateTimeField(auto_now_add=True)

    def filesize(self):
        return os.path.getsize(self.file.path)

