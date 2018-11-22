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
    num_rounds = 1
    # this parameter defines how much time a user will stay on a RET page per round (in seconds)
    task_time = 3000


class Subsession(BaseSubsession):
    def creating_session(self):
        # we look for a corresponding Task Generator in our library (ret_functions) that contain all task-generating
        # functions. So the name of the generator in 'task_fun' parameter from settings.py should coincide with an
        # actual task-generating class from ret_functions.
        self.session.vars['task_fun'] = getattr(ret_functions, self.session.config['task'])
        # If a task generator gets some parameters (like a level of difficulty, or number of rows in a matrix etc.)
        # these parameters should be set in 'task_params' settings of an app, in a form of dictionary. For instance:
        # 'task_params': {'difficulty': 5}
        self.session.vars['task_params'] = self.session.config.get('task_params', {})

        # for each player we call a function (defined in Player's model) called get_or_create_task
        # this is done so that when a RET page is shown to a player for the first time they would already have a task
        # to work on
        for p in self.get_players():
            p.get_or_create_task()


class Group(BaseGroup):
    ...


class Player(BasePlayer):
    # here we store all tasks solved in this specific round - for further analysis
    tasks_dump = models.LongStringField(doc='to store all tasks with answers, diff level and feedback')

    # this method returns number of correct tasks solved in this round
    @property
    def num_tasks_correct(self):
        return self.tasks.filter(correct_answer=F('answer')).count()

    # this method returns total number of tasks to which a player provided an answer
    @property
    def num_tasks_total(self):
        return self.tasks.filter(answer__isnull=False).count()

    # in the following method we look if there are any unfinished (with no answer) tasks. If yes, we return an unfinished
    # task. If there are no uncompleted tasks we create a new one using a task-generating function from session settings
    def get_or_create_task(self):
        unfinished_tasks = self.tasks.filter(answer__isnull=True)
        if unfinished_tasks.exists():
            return unfinished_tasks.first()
        else:
            task = Task.create(self, self.session.vars['task_fun'], **self.session.vars['task_params'])
            task.save()
            return task

# This is a custom model that contain information about individual tasks. Each player in each round can have as many
# tasks as they tried to solve (we can call for the set of all tasks  solved by a player by calling for instance
# player.tasks.all()
# Each task has a body field, html_body - actual html code shown at each page, correct answer and an answer provided by
# a player. In addition there are two automatically updated/created fields that track time of creation and of an update
# These fields can be used to track how long each player works on each task
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

    # the following method creates a new task, and requires as an input a task-generating function and (if any) some
    # parameters fed into task-generating function.
    @classmethod
    def create(cls, player, fun, **params):
        proto_task = fun(**params)
        task = cls(player=player,
                   body=proto_task.body,
                   html_body=proto_task.html_body,
                   correct_answer=proto_task.correct_answer)
        return task
