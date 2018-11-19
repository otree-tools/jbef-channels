from django.conf.urls import url, include
from decoding_app import views as v
from django.conf import settings
from django.contrib.auth.decorators import login_required

urlpatterns = [
    url(v.ListTasksView.url_pattern, v.ListTasksView.as_view(), name=v.ListTasksView.url_name),
    url(v.TasksCSVExport.url_pattern, v.TasksCSVExport.as_view(), name=v.TasksCSVExport.url_name),
]
