from channels.routing import route_class
from .consumers import TaskTracker

# the following line builds a path to our consumer
channel_routing = [route_class(TaskTracker, path=TaskTracker.url_pattern), ]
