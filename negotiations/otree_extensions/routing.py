from channels.routing import route_class
from .consumers import OfferTracker, TaskTracker

channel_routing = [
    route_class(OfferTracker, path=OfferTracker.url_pattern),
    route_class(TaskTracker, path=TaskTracker.url_pattern),
]
