from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range,
)

from django.db import models as djmodels
from django.db.models.signals import post_save
from django.db.models import F
import json
from random import randint
from django.core import serializers

author = 'Philipp Chapkovski, chapkovski@gmail.com'

doc = """
    multi-round real effort task
"""


class DifficultyLevel(int):
    def __init__(self, level):
        self.level = level

    def get_difficulty_level(self):
        return '{0}X{0}'.format(self.level)

    def get_fee(self):
        return self.level * Constants.fee_per_square


class Constants(BaseConstants):
    name_in_url = 'realefforttask'
    players_per_group = None
    num_rounds = 3
    task_time = 30
    lb = 30
    ub = 101
    fee_per_square = c(1)
    diff_choices = [DifficultyLevel(i) for i in range(2, 13)]


class Subsession(BaseSubsession):
    ...


class Group(BaseGroup):
    ...


class Player(BasePlayer):
    last_correct_answer = models.IntegerField()
    tasks_dump = models.LongStringField(doc='to store all tasks with answers, diff level and feedback')
    difficulty = models.IntegerField(doc='level of difficulty of tasks in this period',
                                     choices=Constants.diff_choices,
                                     widget=widgets.RadioSelect)
    def create_task(self):
        ...
        # we create task body here

    def get_task(self):
        ...
        # if task body is null, we create task. if it is not null we retrieve another task


    num_tasks_incorrect
    num_tasks_total
    num_tasks_incorrect


    def dump_tasks(self):
        # this method will request all completed tasks and dump them to player's field
        # just for the convenience and following analysis.
        # theoretically we don't need to store 'updated_at' field because it is already sorted by this field
        # but just in case
        q = self.finished_tasks
        data = list(q.values('difficulty',
                             'correct_answer',
                             'answer',
                             'get_feedback',
                             'updated_at'))
        # the following loop we need to avoid issues with converting dateteime to string
        for d in data:
            d['updated_at'] = str(d['updated_at'])
        self.tasks_dump = json.dumps(data)

    def get_corresponding_dif_level(self):
        return next(x for x in Constants.diff_choices if x == self.difficulty)

    def get_fee(self):
        return self.get_corresponding_dif_level().get_fee()

    def get_difficulty_level(self):
        return self.get_corresponding_dif_level().get_difficulty_level()

    def set_payoff(self):
        self.payoff = self.num_tasks_correct * self.get_fee()


def slicelist(l, n):
    return [l[i:i + n] for i in range(0, len(l), n)]


def get_random_list(max_len):
    low_upper_bound = 50
    high_upper_bound = 99
    return [randint(10, randint(low_upper_bound, high_upper_bound)) for i in range(max_len)]


class Task(djmodels.Model):
    class Meta:
        ordering = ['updated_at']

    player = djmodels.ForeignKey(to=Player, related_name='tasks')
    difficulty = models.IntegerField(doc='difficulty level')
    body = models.LongStringField(doc='task body - just in case')
    correct_answer = models.IntegerField(doc='right answer')
    answer = models.IntegerField(doc='user\'s answer', null=True)
    get_feedback = models.BooleanField(doc='whether user chooses to get feedback', null=True, initial=False)
    created_at = djmodels.DateTimeField(auto_now_add=True)
    updated_at = djmodels.DateTimeField(auto_now=True)

    @classmethod
    def post_create(cls, sender, instance, created, *args, **kwargs):
        # this presumably is considered the safest method to update newly created items
        # so we catch the new task, we add there the body based on difficulty level,
        # and the correct answer.
        if not created:
            return
        diff = instance.player.difficulty
        listx = get_random_list(diff ** 2)
        listy = get_random_list(diff ** 2)
        instance.correct_answer = max(listx) + max(listy)
        listx = slicelist(listx, diff)
        listy = slicelist(listy, diff)
        instance.body = json.dumps({'listx': listx, 'listy': listy})
        instance.save()

    def get_dict(self):
        # this method is needed to push the task to the page via consumers
        body = json.loads(self.body)
        return {
            "mat1": body['listx'],
            "mat2": body['listy'],
            "correct_answer": self.correct_answer,
            "difficulty": self.difficulty,
            'modal_show': False,
        }


post_save.connect(Task.post_create, sender=Task)
