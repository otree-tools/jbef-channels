from .generic import PaginatedListView
from double_auction.models import Contract
from .csv import ExportToCSV


class ContractList(PaginatedListView):
    template_name = 'double_auction/admin/ContractsList.html'
    url_name = 'contracts'
    url_pattern = r'^export/contracts$'
    context_object_name = 'contracts'
    paginate_by = 50
    navbar_active_tag = 'contracts'
    export_activated = True
    export_link_name = 'contract_csv'
    model = Contract
    queryset = Contract.objects.all()


class ContractCSVExport(ExportToCSV):
    filename = 'contracts.csv'
    template_name = 'double_auction/admin/csv/contracts.csv'
    queryset = Contract.objects.all()
    url_name = 'contract_csv'
    url_pattern = r'^export/contracts/csv$'
