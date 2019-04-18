from .generic import PaginatedListView
from double_auction.models import Contract


class ContractList(PaginatedListView):
    template_name = 'double_auction/admin/ContractsList.html'
    url_name = 'contracts'
    url_pattern = r'^export/contracts$'
    context_object_name = 'contracts'
    paginate_by = 50
    navbar_active_tag = 'contracts'
    export_activated = True
    model = Contract
    queryset = Contract.objects.all()
