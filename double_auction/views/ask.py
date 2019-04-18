from .generic import PaginatedListView
from double_auction.models import Ask


class AskList(PaginatedListView):
    template_name = 'double_auction/admin/AsksList.html'
    url_name = 'asks'
    url_pattern = r'^export/asks$'
    context_object_name = 'asks'
    paginate_by = 50
    navbar_active_tag = 'asks'
    export_activated = True
    model = Ask
    queryset = Ask.objects.all()
