from channels.routing import route_class
from .consumers import MarketTracker

channel_routing = [
    route_class(MarketTracker, path=MarketTracker.url_pattern),

]
