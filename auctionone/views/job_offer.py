from .generic import PaginatedListView
from .csv import ExportToCSV
from auctionone.models import JobOffer


class JobOfferList(PaginatedListView):
    template_name = 'auctionone/admin/JobOfferList.html'
    url_name = 'gift_exchange_offers'
    url_pattern = r'^export/gift_exchange/job_offers$'
    context_object_name = 'job_offers'
    paginate_by = 50
    navbar_active_tag = 'job_offers'
    export_activated = True
    export_link_name = 'job_offers_csv'
    queryset = JobOffer.objects.all()


class JobOfferToCSV(ExportToCSV):
    filename = 'job_offers.csv'
    template_name = 'auctionone/admin/csv/job_offers.csv'
    queryset = JobOffer.objects.all()
    url_name = 'job_offers_csv'
    url_pattern = r'^export/gift_exchange/job_offers/csv$'
