from django.views.generic import ListView
from django.http import HttpResponse
from django.template import loader
from realefforttask.models import Task

class TasksToCSV(ListView):
    content_type = 'text/csv'
    filename = 'tasks.csv'
    template_name = 'realefforttask/admin/csv/tasks.csv'
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



