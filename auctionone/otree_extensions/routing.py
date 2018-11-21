
from channels.routing import route_class
from .consumers import AuctionTracker, MatrixTracker

# the following line builds a path to our consumer
channel_routing = [route_class(AuctionTracker, path=AuctionTracker.url_pattern),
                   route_class(MatrixTracker, path=MatrixTracker.url_pattern)]

