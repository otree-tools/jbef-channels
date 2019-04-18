from django.views.generic import ListView
from django.http import HttpResponse
from django.template import loader, Context


class ExportToCSV(ListView):
    content_type = 'text/csv'
    filename = None


    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type=self.content_type)
        response['Content-Disposition'] = f'attachment; filename="{self.filename}"'
        t = loader.get_template(self.template_name)
        c = {
            'data': self.get_queryset(),
        }
        response.write(t.render(c))
        return response


