from task_management import models
from api import serializers
from rest_framework import generics
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import authentication
from django.shortcuts import get_object_or_404
import json
from api.permissions import ProjectAdmin, ProjectCollaborator
from datetime import datetime

class TokenAuthView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)


class ProfileCreate(generics.CreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer

    def post(self, request, format=None):
        body = json.loads(request.body)
        serializer = serializers.UserSerializer(data=body)
        serializer.is_valid()
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ProfileDetail(TokenAuthView, generics.RetrieveUpdateDestroyAPIView):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer

    def put(self, request, *args, **kwargs):
        body = json.loads(request.body)
        user = models.User.objects.get(username = request.user.username)
        serializer = serializers.UserSerializer(instance=user, data=body)
        serializer.is_valid()
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        user = models.User.objects.get(username = request.user.username)
        user.is_active = False
        user.save()
        return Response("Profile successfully deleted", status=status.HTTP_202_ACCEPTED)

    def get_object(self):
        return self.request.user
    
# For retrieving all projects and creating a project
class ProjectList(TokenAuthView, generics.ListCreateAPIView):
    serializer_class = serializers.ProjectSerializer
    queryset = models.Project.objects.all()

    def get_queryset(self):
        """
        This view should set the list of projects
        for the currently authenticated user.
        """ 
        return models.Profile.objects.get(user=self.request.user).get_user_projects()

    def post(self, request, format=None):
        #print(pretty_request(request))
        body = json.loads(request.body)

        project = models.Project(name=body['name'], description=body['description'])
        project.save(user=request.user)
        serializer = serializers.ProjectSerializer(project)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        

# For retrieving, updating, or detroying a project
class ProjectDetail(TokenAuthView, generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    permission_classes = [ProjectAdmin]

    def put(self, request, *args, **kwargs):
        body = json.loads(request.body)

        project = get_object_or_404(models.Project, pk=self.kwargs['pk'])

        serializer = serializers.ProjectSerializer(project, data=body)
        serializer.is_valid()
        serializer.save()
        # Update Ticket Template
        template_serializer = serializers.TicketTemplateSerializer(instance=project.ticket_template, data=body['ticket_template'])
        template_serializer.is_valid()
        template_serializer.save()
        serializer.data.ticket_template = template_serializer.data
        # Update the roles
        serialized_roles = []
        for role in body['roles']:
            role_serializer = serializers.RoleSerializer(instance=project, data=role)
            role_serializer.is_valid()
            role_serializer.save()
            #serialized_roles.append({'role': role_serializer.validated_data['role'], 'username': role_serializer.validated_data['profile']})

        serializer.delete_removed_roles(project, body['roles'])
        #The roles data sent back is not getting assigned correctly
        #Don't this the following line works
        serializer.data['roles'] = role_serializer.data

        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        

# For retrieving all projects and creating a project
class TicketList(TokenAuthView, generics.ListCreateAPIView):
    serializer_class = serializers.TicketSerializer
    queryset = models.Ticket.objects.all()
    permission_classes = [ProjectCollaborator]

    def get_queryset(self):
        """
        This view should set the list of projects
        for the currently authenticated user.
        """ 
        project = get_object_or_404(models.Project, pk=self.kwargs['pk'])
        return models.Ticket.objects.filter(project=project)

    def post(self, request, *args, **kwargs):
        request.data['project_pk'] = self.kwargs['pk']
        return super().post(request, *args, **kwargs)
        
class TicketDetail(TokenAuthView, generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Ticket.objects.all()
    serializer_class = serializers.TicketSerializer
    permission_classes = [ProjectCollaborator]

    def get_object(self):
        print("Getting object")
        project = get_object_or_404(models.Project, pk=self.kwargs['pk'])
        return get_object_or_404(models.Ticket, project=project, id_in_project=self.kwargs['ticket_pk'])

    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)
        return Response("Ticket successfully deleted", status=status.HTTP_202_ACCEPTED)

class TicketUpdateState(TokenAuthView, APIView):
    permission_classes = [ProjectCollaborator]

    def post(self, request, **kwargs):

        #Get state out of request body
        body = json.loads(request.body)
        state = body['state']
        
        #Get project from url
        project = get_object_or_404(models.Project, pk=self.kwargs['pk'])

        #Get ticket by project id and confirm state is valid
        try: 
            ticket = project.tickets.get(id_in_project=self.kwargs['ticket_pk'])
        except:
            return Response("Ticket not found", status=status.HTTP_404_NOT_FOUND)
        #print(project.ticket_template.states.all().values('state_name'))
        if project.ticket_template.states.all().filter(state_name=state).exists():
            #Update state
            ticket.state = project.ticket_template.states.all().get(state_name=state)
            ticket.save()
            return Response("Ticket state updated", status=status.HTTP_202_ACCEPTED)
        
        #State not valid
        return Response("The state is not valid", status=status.HTTP_406_NOT_ACCEPTABLE)

class TicketObjectView(generics.ListCreateAPIView, generics.DestroyAPIView,):
    def get_ticket(self, **kwargs):
        project = get_object_or_404(models.Project, pk=kwargs['pk'])
        return project.tickets.get(id_in_project=kwargs['ticket_pk'])

    def delete(self, request, *args, **kwargs):
        obj = getattr(self.get_ticket(**kwargs), self.ticket_attribute).get(pk=kwargs[self.url_pk])
        obj.delete()
        return Response("Deleted successfully.", status=status.HTTP_202_ACCEPTED)

    def get_queryset(self):
        kwargs = self.kwargs
        return getattr(self.get_ticket(**kwargs), self.ticket_attribute).all()

class Comment(TokenAuthView, TicketObjectView):
    queryset = models.Comment.objects.all()
    serializer_class = serializers.CommentSerializer
    permission_classes = [ProjectCollaborator]
    ticket_attribute = "comments"
    url_pk = "comment_pk"

    def post(self, request, *args, **kwargs):
        body = json.loads(request.body)
        comment = models.Comment(ticket=self.get_ticket(**kwargs), author=request.user, body=body['body'], created_date=datetime.now())
        comment.save()
        serializer = self.serializer_class(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class Link(TokenAuthView, TicketObjectView):
    queryset = models.Relationship.objects.all()
    serializer_class = serializers.LinkSerializer
    permission_classes = [ProjectCollaborator]
    ticket_attribute = "relationships"
    url_pk = "link_pk"

    def post(self, request, *args, **kwargs):
        body = json.loads(request.body)
        project = get_object_or_404(models.Project, pk=kwargs['pk'])
        ticket_2 = project.tickets.get(id_in_project=body['related_ticket_project_pk'])

        #Check if Relationship already exists
        if models.Relationship.objects.filter(ticket_2=ticket_2, ticket_1=self.get_ticket(**kwargs)).exists():
            return Response("The relationship already exists", status=status.HTTP_208_ALREADY_REPORTED)

        #Check if relationship eists and create the link
        if project.ticket_template.relationshipTypes.filter(name=body['link_type']).exists():
            relationship_type = project.ticket_template.relationshipTypes.get(name=body['link_type'])

            link = models.Relationship(ticket_1=self.get_ticket(**kwargs), ticket_2=ticket_2, relationship_type=relationship_type)
            link.save()
            serializer = self.serializer_class(link)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        #Relationship not valid
        return Response("The relationship is not valid", status=status.HTTP_406_NOT_ACCEPTABLE)

class File(TokenAuthView, TicketObjectView):
    queryset = models.File.objects.all()
    serializer_class = serializers.FileSerializer
    permission_classes = [ProjectCollaborator]
    ticket_attribute = "files"
    url_pk = "file_pk"

    def post(self, request, *args, **kwargs):
        if 'file' not in request.data:
            raise ParseError("Empty content")
        file = request.data['file']

        ticket = self.get_ticket(**kwargs)
    
        file_obj = models.File(ticket=ticket, file=file, name=file.name, created_date=datetime.now())
        file_obj.save()
        serializer = self.serializer_class(file_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    '''For printing post requests if needed.'''
def pretty_request(request):
    headers = ''
    for header, value in request.META.items():
        if not header.startswith('HTTP'):
            continue
        header = '-'.join([h.capitalize() for h in header[5:].lower().split('_')])
        headers += '{}: {}\n'.format(header, value)

    return (
        '{method} HTTP/1.1\n'
        'Content-Length: {content_length}\n'
        'Content-Type: {content_type}\n'
        '{headers}\n\n'
        '{body}'
    ).format(
        method=request.method,
        content_length=request.META['CONTENT_LENGTH'],
        content_type=request.META['CONTENT_TYPE'],
        headers=headers,
        body=request.body,
    )
