from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import time
from django.db import models as djmodels
import random

author = 'Essi Kujansuu, EUI, essi.kujansuu@eui.eu, adapting work of Philipp Chapkovski, UZH, chapkovski@gmail.com'

doc = """
Adaptation of Fehr et al. 1993 auction.
"""


class Constants(BaseConstants):
    name_in_url = 'auctionone'
    players_per_group = 4
    num_rounds = 8
    starting_time = 1200
    num_employers = 2
    num_workers = players_per_group - num_employers
    task_time = 300
    lower_boundary = 30
    upper_boundary = 101
    step = 5
    offer_range = list(range(lower_boundary, upper_boundary, step))
    max_task_amount = 10

class Subsession(BaseSubsession):
    def creating_session(self):
        # before any page is shown we create initial tasks for each of the players
        for p in self.get_players():
            p.get_task()


class Group(BaseGroup):
    auctionenddate = models.FloatField()
    work_end_date = models.FloatField()
    num_contracts_closed = models.IntegerField()
    day_over = models.BooleanField()
    last_message = models.StringField()
    wage_list = models.StringField()
    contracts_dump = models.StringField()

    def time_left(self):
        now = time.time()
        time_left = self.auctionenddate - now
        time_left = round(time_left) if time_left > 0 else 0
        return time_left

    def time_work(self):
            now = time.time()
            time_left = self.work_end_date - now
            time_left = round(time_left) if time_left > 0 else 0
            return time_left

    def set_payoffs(self):
        for person in self.get_players():

            if person.role() == 'employer':
                if person.matched == 0:
                    person.payoff = 0
                else:
                    closed_contract = person.contract.get(accepted=True)
                    person.payoff = 40 - closed_contract.amount + 20 * closed_contract.tasks_corr
            if person.role() == 'worker':
                if person.matched == 0:
                    person.payoff = 20
                else:
                    closed_contract = person.work_to_do.get(accepted=True)
                    person.payoff = closed_contract.amount

    def get_channel_group_name(self):
        return 'auction_group_{}'.format(self.pk)


class Player(BasePlayer):
    treatment = models.StringField()
    wage_offer = models.IntegerField()
    last_correct_answer = models.IntegerField()
    mat1 = models.LongStringField()
    mat2 = models.LongStringField()
    tasks_attempted = models.PositiveIntegerField(initial=0)
    tasks_correct = models.PositiveIntegerField(initial=0)
    matched = models.BooleanField()
    payoff = models.CurrencyField()

    def role(self):
        if self.id_in_group < Constants.num_employers + 1:
            return 'employer'
        else:
            return 'worker'

    def get_personal_channel_name(self):
        return '{}_{}'.format(self.role(), self.id)

    def slicelist(self, l, n):
        return [l[i:i + n] for i in range(0, len(l), n)]

    def get_random_list(self):
        random_upper_boundary = random.randint(50, 99)
        max_len = 100
        return [random.randint(10, random_upper_boundary) for i in range(max_len)]

    def get_task(self):
        string_len = 10
        listx = self.get_random_list()
        listy = self.get_random_list()
        self.last_correct_answer = max(listx) + max(listy)
        listx = self.slicelist(listx, string_len)
        listy = self.slicelist(listy, string_len)
        self.mat1 = str(listx)
        self.mat2 = str(listy)
        return {
            "mat1": listx,
            "mat2": listy,
            "correct_answer": self.last_correct_answer,
        }

class Offer(djmodels.Model):
    employer = djmodels.ForeignKey(Player, related_name='offers')
    amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class JobContract(djmodels.Model):
    employer = djmodels.ForeignKey(Player, related_name='contract', unique=True)
    worker = djmodels.ForeignKey(Player, blank=True, null=True, related_name='work_to_do')
    amount = models.IntegerField()
    accepted = models.BooleanField()
    tasks_corr = models.PositiveIntegerField(initial=0)
    tasks_att = models.PositiveIntegerField(initial=0)
    created_at = models.DateTimeField(auto_now_add=True)
    auctionenddate = models.FloatField()
    day_over = models.BooleanField()
