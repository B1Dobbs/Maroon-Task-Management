import django_filters
from django_filters import DateFilter, CharFilter, ChoiceFilter, ModelChoiceFilter
from django.shortcuts import get_object_or_404
from .models import *

def types(request):
    if request is None:
        return Type.objects.none()
    project = get_object_or_404(Project, pk=request.GET['pk'])
    return project.ticket_template.types.all()

def states(request):
    if request is None:
        return Type.objects.none()
    project = get_object_or_404(Project, pk=request.GET['pk'])
    return project.ticket_template.states.all()

def assignees(request):
    if request is None:
        return Type.objects.none()
    project = get_object_or_404(Project, pk=request.GET['pk'])
    return Profile.objects.filter(roles__project=project)

class TicketFilter(django_filters.FilterSet):
    
    title = CharFilter(field_name="title", lookup_expr='icontains')
    type = ModelChoiceFilter(field_name="type", queryset=types)
    state = ModelChoiceFilter(field_name="state", queryset=states)
    assignees = ModelChoiceFilter(field_name="assignees", queryset=assignees)
    class Meta:
        model = Ticket
        fields = ['type','state','title','assignees']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super(TicketFilter, self).__init__(data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['assignees'].field.widget.attrs.update({'class': 'selectpicker'})