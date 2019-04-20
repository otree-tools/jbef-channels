from django.conf.urls import url
from realefforttask.views import TasksToCSV

views_to_add = [TasksToCSV]
urlpatterns = [url(i.url_pattern, i.as_view(), name=i.url_name) for i in views_to_add]
