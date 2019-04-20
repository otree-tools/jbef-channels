from django.conf.urls import url, include

from auctionone.views import TaskList, JobOfferList, TaskListCSV, JobOfferListCSV

views_to_add = [TaskList, JobOfferList, TaskListCSV, JobOfferListCSV]
urlpatterns = [url(i.url_pattern, i.as_view(), name=i.url_name) for i in views_to_add]
