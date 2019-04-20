from django.conf.urls import url, include

from auctionone.views import TaskList, JobOfferList, TasksToCSV, JobOfferToCSV

views_to_add = [TaskList, JobOfferList, TasksToCSV, JobOfferToCSV]
urlpatterns = [url(i.url_pattern, i.as_view(), name=i.url_name) for i in views_to_add]
