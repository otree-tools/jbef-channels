from .consumers import TaskTracker
from django.urls import re_path

websocket_routes = [re_path(TaskTracker.url_pattern, TaskTracker), ]
