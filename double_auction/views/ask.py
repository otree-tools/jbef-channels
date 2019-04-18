from .generic import StatementListView
from double_auction.models import Ask
from .csv import ExportToCSV


class AskList(StatementListView):
    url_name = 'asks'
    url_pattern = r'^export/asks$'
    navbar_active_tag = 'asks'
    export_activated = True
    export_link_name = 'ask_csv'
    model = Ask
    queryset = Ask.objects.all()
    title = 'Asks'


class AskCSVExport(ExportToCSV):
    filename = 'asks.csv'
    template_name = 'double_auction/admin/csv/statements.csv'
    queryset = Ask.objects.all()
    model = Ask
    url_name = 'ask_csv'
    url_pattern = r'^export/asks/csv$'
