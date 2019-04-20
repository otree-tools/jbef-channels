from auctionone.models import Task
from .csv import ExportToCSV
from .generic import PaginatedListView
from django.http import HttpResponse
from django.template import loader

class TaskList(PaginatedListView):
    url_pattern = r'^export/gift_exchange/tasks$'
    url_name = 'gift_exchange_tasks'
    template_name = 'auctionone/admin/TaskList.html'
    title = 'Tasks for Gift Exchange Game'
    context_object_name = 'tasks'
    navbar_active_tag = 'tasks'
    paginate_by = 50
    export_activated = True
    export_link_name = 'task_csv'
    queryset = Task.objects.exclude(answer__isnull=True).order_by('created_at')

    def get_context_data(self, **kwargs):
        c = super().get_context_data(**kwargs)
        c['title'] = self.title
        curpage_num = c['page_obj'].number
        paginator = c['paginator']
        epsilon = 3
        c['allowed_range'] = range(max(1, curpage_num - epsilon), min(curpage_num + epsilon, paginator.num_pages) + 1)
        if self.export_link_name:
            c['export_link'] = self.export_link_name
        c['export_activated'] = self.export_activated or False
        return c


class TasksToCSV(ExportToCSV):
    content_type = 'text/csv'
    filename = 'tasks.csv'
    template_name = 'auctionone/admin/csv/tasks.csv'
    queryset = Task.objects.exclude(answer__isnull=True).order_by('created_at')
    url_name = 'task_csv'
    url_pattern = r'^export/realefforttask/tasks/csv$'

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type=self.content_type)
        response['Content-Disposition'] = f'attachment; filename="{self.filename}"'
        t = loader.get_template(self.template_name)
        c = {
            'data': self.get_queryset(),
        }
        response.write(t.render(c))
        return response
