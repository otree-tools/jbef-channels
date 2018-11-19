from django.db import models
import json



class ListField(models.CharField):
    def __init__(
            self,
            *,
            max_length=10000,
            blank=False,
            **kwargs):

        kwargs.setdefault('help_text', '')
        kwargs.setdefault('null', True)

        super().__init__(
            max_length=max_length,
            blank=blank,
            **kwargs)

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)

    def to_python(self, value):
        if isinstance(value, list):
            return value

        if value is None:
            return value

        return json.loads(value)

    def get_prep_value(self, value):
        return json.dumps(value)


