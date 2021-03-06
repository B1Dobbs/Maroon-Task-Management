from django.urls import path
from . import views

urlpatterns = [
    path('', views.Redirect.as_view()),
    path('landing/', views.Landing.as_view(), name='landing'),
    path('landing/<int:pk>', views.Landing.as_view(), name='landing'),
    path('account', views.Account.as_view(), name='account'),
    path('project/<int:pk>', views.ProjectSettings.as_view(), name='project'),
    path('project/<int:pk>/access', views.AccessSettings.as_view(), name='access'),
    path('register',  views.Register.as_view(), name = 'register'),
    path('user/avatar', views.UploadAvatar.as_view(), name = 'user_avatar'),
    path('project/<int:pk>/avatar', views.UploadProjectAvatar.as_view(), name = 'project_avatar'),
    path('project/create', views.CreateProject.as_view(), name='create_project'), 
    path('delete', views.deleteuser, name='delete'),  
    path('ticket/<int:pk>', views.TicketDetail.as_view(), name='ticket') 
]