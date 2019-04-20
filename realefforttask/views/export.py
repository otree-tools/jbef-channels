from django.views.generic import ListView
from realefforttask.models import Task


class TaskListView(ListView):
    url_pattern = r'^export/realefforttask/tasks$'
    url_name = 'realefforttask_export'
    template_name = 'realefforttask/admin/TaskList.html'
    display_name = 'Real effort tasks data'
    title = 'Tasks'
    context_object_name = 'tasks'
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
