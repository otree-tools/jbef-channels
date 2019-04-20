from .generic import StatementListView
from double_auction.models import Bid
from .csv import ExportToCSV


class BidList(StatementListView):
    url_name = 'bids'
    url_pattern = r'^export/double_auction/bids$'
    navbar_active_tag = 'bids'
    export_activated = True
    export_link_name = 'bid_csv'
    model = Bid
    queryset = Bid.objects.all()
    title = 'Bids'


class BidCSVExport(ExportToCSV):
    filename = 'bids.csv'
    template_name = 'double_auction/admin/csv/statements.csv'
    queryset = Bid.objects.all()
    url_name = 'bid_csv'
    url_pattern = r'^export/double_auction/bids/csv$'
