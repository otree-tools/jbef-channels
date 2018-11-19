from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random

author = "Philip Chapkovski, chapkovski@gmail.com"


class Constants(BaseConstants):
    name_in_url = 'minimum_ret'
    players_per_group = None
    num_rounds = 1
    ...


class Subsession(BaseSubsession):
    def creating_session(self):
        # before any page is shown we create initial tasks for each of the players
        for p in self.get_players():
            p.create_task()


class Group(BaseGroup):
    ...


class Player(BasePlayer):
    task_body = models.IntegerField()  # here the body of yet unsolved task is stored
    num_tasks_correct = models.IntegerField(initial=0)  # number of tasks correctly solved (initially 0)
    num_tasks_total = models.IntegerField(initial=0)  # total n. of tasks tried (initially 0)
    last_correct_answer = models.IntegerField()  # the correct answer for the task which is not yet solved

    # the following function creates a new task:
    # generates a random number, stores it
    # and also register a correct answer for it
    def create_task(self):
        self.task_body = random.randint(11, 89)
        self.last_correct_answer = 100 - self.task_body
