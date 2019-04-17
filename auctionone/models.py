from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
from django.db.models.signals import post_save
from django.db import models as djmodels
import random
from channels import Group as ChannelGroup
import json
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from .ret_functions import TwoMatrices
from django.db.models import F

author = ''

doc = """
Adaptation of Fehr et al. 1993 auction.
"""


class Constants(BaseConstants):
    name_in_url = 'auctionone'
    players_per_group = 3
    num_rounds = 8
    num_employers = 1
    num_workers = players_per_group - num_employers
    task_time = 3000  # how much time a worker has to complete the job
    auction_time = 300  # number of seconds before auctioning day is over
    lb = 30  # upper and lower boundaries for job offers
    ub = 101
    step = 5
    offer_range = list(range(lb, ub, step))
    unmatched_worker_payoff = c(20)
    unmatched_employer_payoff = c(0)
    employer_endowment = c(40)
    task_fee = c(20)
    task_difficulty = 5


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    def get_players_by_role(self, role):
        return [p for p in self.get_players() if p.role() == role]

    def get_unmatched_players_by_role(self, role):
        return [p for p in self.get_players_by_role(role) if not p.matched]

    @property
    def open_offers(self):
        return self.offers.filter(worker__isnull=True)

    def num_unmatched_workers(self):
        return len(self.get_unmatched_players_by_role('worker'))

    def num_unmatched_employers(self):
        return len(self.get_unmatched_players_by_role('employer'))

    def is_active(self):
        return self.num_unmatched_employers() > 0 and self.num_unmatched_workers() > 0

    def set_payoffs(self):
        workers, employers = self.get_players_by_role('worker'), self.get_players_by_role('employer')
        for w in workers:
            accepted_offer = w.accepted_offer
            if accepted_offer:
                w.payoff = accepted_offer.amount
            else:
                w.payoff = Constants.unmatched_worker_payoff
        for e in employers:
            accepted_offer = e.accepted_offer
            if accepted_offer:
                worker = accepted_offer.worker
                e.payoff = Constants.employer_endowment - \
                           accepted_offer.amount + \
                           Constants.task_fee * worker.num_tasks_correct
            else:
                e.payoff = Constants.unmatched_employer_payoff

    def get_channel_group_name(self):
        return 'auction_group_{}'.format(self.pk)

    def render_block(self, template, context):
        return mark_safe(render_to_string('auctionone/components/{}.html'.format(template), context))

    def get_active_offers_html(self):
        return self.render_block('open_contracts_block', {'group': self})

    def get_general_info_html(self):
        return self.render_block('general_info_block', {'group': self})


class Player(BasePlayer):
    matched = models.BooleanField(initial=False)

    def role(self):
        if self.id_in_group <= Constants.num_employers:
            return 'employer'
        else:
            return 'worker'

    def get_personal_channel_name(self):
        return '{}_{}'.format(self.role(), self.id)

    @property
    def accepted_offer(self):
        if self.role() == 'employer':
            try:
                return self.offer_made.get(worker__isnull=False)
            except JobOffer.DoesNotExist:
                return
        else:
            try:
                return self.offer_accepted.get(worker__isnull=False)
            except JobOffer.DoesNotExist:
                return

    @property
    def partner(self):
        if self.matched:
            if self.role() == 'employer':
                return self.accepted_offer.worker
            else:
                return self.accepted_offer.employer

    # RET BLOCK::
    @property
    def num_tasks_correct(self):
        return self.tasks.filter(correct_answer=F('answer')).count()

    # this method returns total number of tasks to which a player provided an answer
    @property
    def num_tasks_total(self):
        return self.tasks.filter(answer__isnull=False).count()

    # in the following method we look if there are any unfinished (with no answer) tasks.
    # If yes, we return an unfinished task.
    # If there are no uncompleted tasks we create a new one using a task-generating function from session settings.
    def get_or_create_task(self):
        unfinished_tasks = self.tasks.filter(answer__isnull=True)
        if unfinished_tasks.exists():
            return unfinished_tasks.first()
        else:
            task = Task.create(self, TwoMatrices, **{'difficulty': Constants.task_difficulty})
            task.save()
            return task


class JobOffer(djmodels.Model):
    employer = djmodels.ForeignKey(Player, related_name='offer_made', )
    worker = djmodels.ForeignKey(Player, null=True, related_name='offer_accepted')
    group = djmodels.ForeignKey(Group, related_name='offers')
    amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def post_save(cls, sender, instance, created, *args, **kwargs):
        employer, worker = instance.employer, instance.worker
        group = instance.group
        contract_parties = [employer, worker]
        if instance.worker:
            for p in contract_parties:
                p.matched = True
                p.save()
                p_group = ChannelGroup(p.get_personal_channel_name())
                p_group.send(
                    {'text': json.dumps({
                        'day_over': True,
                    })}
                )

        group_channel = ChannelGroup(group.get_channel_group_name())
        group_message = {}
        if not group.is_active():
            group_message['day_over'] = True
        group_message['open_offers'] = group.get_active_offers_html()
        group_message['general_info'] = group.get_general_info_html()
        group_channel.send({'text': json.dumps(group_message)})


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


post_save.connect(JobOffer.post_save, sender=JobOffer)
