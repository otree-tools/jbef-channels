from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range,
)

from django.db import models as djmodels
from django.db.models import F
from . import ret_functions

author = 'Philipp Chapkovski, chapkovski@gmail.com'

doc = """
    multi-round real effort task
"""


class Constants(BaseConstants):
    name_in_url = 'realefforttask'
    players_per_group = None
    num_rounds = 3
    task_time = 3000


class Subsession(BaseSubsession):
    def creating_session(self):
        self.session.vars['task_fun'] = getattr(ret_functions, self.session.config['task'])
        self.session.vars['task_params'] = self.session.config.get('task_params', {})
        for p in self.get_players():
            p.get_or_create_task()


class Group(BaseGroup):
    ...


class Player(BasePlayer):
    tasks_dump = models.LongStringField(doc='to store all tasks with answers, diff level and feedback')

    @property
    def num_tasks_correct(self):
        return self.tasks.filter(correct_answer=F('answer')).count()

    @property
    def num_tasks_total(self):
        return self.tasks.filter(answer__isnull=False).count()

    def get_or_create_task(self):
        unfinished_tasks = self.tasks.filter(answer__isnull=True)
        if unfinished_tasks.exists():
            return unfinished_tasks.first()
        else:
            task = Task.create(self, self.session.vars['task_fun'], **self.session.vars['task_params'])
            task.save()
            return task


class Task(djmodels.Model):
    class Meta:
        ordering = ['-created_at']

    player = djmodels.ForeignKey(to=Player, related_name='tasks')
    body = models.LongStringField()
    html_body = models.LongStringField()
    correct_answer = models.StringField()
    answer = models.StringField(null=True)
    created_at = djmodels.DateTimeField(auto_now_add=True)
    updated_at = djmodels.DateTimeField(auto_now=True)

    @classmethod
    def create(cls, player, fun, **params):
        proto_task = fun(**params)
        task = cls(player=player,
                   body=proto_task.body,
                   html_body=proto_task.html_body,
                   correct_answer=proto_task.correct_answer)
        return task
