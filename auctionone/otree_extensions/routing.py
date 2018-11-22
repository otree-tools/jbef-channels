from channels.routing import route_class
from .consumers import AuctionTracker, TaskTracker

# the following line builds a path to our consumer
channel_routing = [route_class(AuctionTracker, path=AuctionTracker.url_pattern),
                   route_class(TaskTracker, path=TaskTracker.url_pattern), ]
