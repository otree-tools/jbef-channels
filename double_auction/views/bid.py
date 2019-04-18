from .generic import PaginatedListView
from double_auction.models import Bid


class BidList(PaginatedListView):
    template_name = 'double_auction/admin/BidsList.html'
    url_name = 'bids'
    url_pattern = r'^export/bids$'
    context_object_name = 'bids'
    paginate_by = 50
    navbar_active_tag = 'bids'
    export_activated = True
    model = Bid
    queryset = Bid.objects.all()
