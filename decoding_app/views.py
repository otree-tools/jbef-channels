from otree.models import Session
from django.views.generic import TemplateView, ListView
from django.shortcuts import render
from .models import Task
from django.http import HttpResponse
from django.template import Context, loader
from django.db.models import DurationField, ExpressionWrapper, F


# the view to get a list of all sessions
class AllSessionsList(TemplateView):
    template_name = 'tasks_export/all_session_list.html'
    url_name = 'tasks_sessions_list'
    url_pattern = r'^tasks_sessions_list/$'
    display_name = 'Exporting tasks data'

    def get(self, request, *args, **kwargs):
        all_sessions = Session.objects.all()
        tasks_sessions = [i for i in all_sessions if 'decoding_app' in i.config['app_sequence']]
        return render(request, self.template_name, {'sessions': tasks_sessions})


class TaskMixin(object):
    def get_queryset(self):
        session_code = self.kwargs['pk']
        expression = F('updated_at') - F('created_at')
        wrapped_expression = ExpressionWrapper(expression, DurationField())
        annot_tasks = Task.objects.annotate(delta=wrapped_expression)
        return annot_tasks.filter(player__session__code=session_code, answer__isnull=False).order_by(
            'updated_at')


class ListTasksView(TaskMixin, ListView):
    template_name = 'tasks_export/tasks_list.html'
    url_name = 'tasks_list'
    url_pattern = r'^session/(?P<pk>[a-zA-Z0-9_-]+)/tasks/$'
    model = Task
    context_object_name = 'tasks'


class TasksCSVExport(TaskMixin, TemplateView):
    template_name = 'tasks_export/tasks.txt'
    url_name = 'tasks_export'
    url_pattern = r'^session/(?P<pk>[a-zA-Z0-9_-]+)/tasks_export/$'
    response_class = HttpResponse
    content_type = 'text/csv'

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        session_code = self.kwargs['pk']
        filename = '{}_tasks_data.csv'.format(session_code)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        tasks = self.get_queryset()
        t = loader.get_template(self.template_name)
        c = {
            'tasks': tasks,
        }
        response.write(t.render(c))
        return response
