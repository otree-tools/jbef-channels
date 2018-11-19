from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
from django.db import models as djmodels
import random
from django.db.models.signals import post_save
from django.db.models import Sum

author = 'Philipp Chapkovski, chapkovski@gmail.com'

doc = """
Negotiations game. Exley, C.L., Niederle, M. and Vesterlund, L., 2016. Knowing when to ask: The cost of leaning in 
(No. w22961). National Bureau of Economic Research.
http://www.nber.org/papers/w22961
"""


class Constants(BaseConstants):
    name_in_url = 'negotiations'
    players_per_group = 2
    num_rounds = 2
    # TODO: DELETE TWO FOLLOWING LINES:
    debug_w_choices = [c(i) for i in [10, 15, 20]]
    debug_f_choices = [c(i) for i in [20, 25]]
    # END DEBUG
    rank_contribution_lookup = {'firm': {1: c(25),
                                         2: c(20), },
                                'worker': {1: c(20),
                                           2: c(15),
                                           3: c(10), }}
    ret_rounds = [1, 2]  # when do we play RET before proceeding to negotiaions
    block_B_start = ret_rounds[1]  # block b starts when they have a second RET (vice versa in fact)

    ret_timeout_seconds = 60 # how many seconds to complete RET
    nego_timeout_seconds = 60 # how many seconds to complete negotiations
    offer_epsilon = 5  # boundaries for wage negotiations
    fine = c(5)  # fine subtractred from payoffs if negotiations failed
    num_digits = 5  # how many 2-digits nums we'll generate for RET
    lb = 10
    ub = 99
    digits_range = (lb, ub)  # the range of numbers to generate tasks for RET
    num_zero_rows = 10  # how many rows of 1/0 are generated for counting zeros RET
    len_zero_row = 5  # how long is each RET counting zero row
    ACCEPT_CHOICES = [(True, 'Accept the suggested wage'),
                      (False, 'Reject the suggested wage and negotiate')]
    task_types = [(1, 'Addition task'), (2, 'Counting task')]
    block_names = ['A', 'B']
    len_A_block = block_B_start - 1
    len_B_block = num_rounds - block_B_start + 1
    block_lengths = {'A': len_A_block,
                     'B': len_B_block, }


class Subsession(BaseSubsession):
    block_round_number = models.IntegerField()
    task_type = models.IntegerField(doc='what kind of RET is performed in this round', choices=Constants.task_types)
    block_name = models.StringField(doc='block name')
    end_of_block_A_round = models.BooleanField(initial=False)

    def creating_session(self):
        self.group_randomly(fixed_id_in_group=True)
        # all the following BS is needed mostly for coherency with zTree design

        if self.round_number < Constants.ret_rounds[1]:
            self.task_type = 1
        else:
            self.task_type = 2

        if self.round_number < Constants.block_B_start:
            self.block_round_number = self.round_number
            self.block_name = Constants.block_names[0]
        else:
            self.block_round_number = self.round_number - Constants.block_B_start + 1
            self.block_name = Constants.block_names[1]
        if self.round_number + 1 == Constants.block_B_start:
            self.end_of_block_A_round = True

    def set_ranking(self):
        # TODO: just in case set some breaks on sessions with less then 4 participants
        if self.round_number in Constants.ret_rounds:
            firms = [p for p in self.get_players() if p.role() == 'firm']
            workers = [p for p in self.get_players() if p.role() == 'worker']
            for f in firms:
                others = [p for p in firms if p != f]
                otter = random.choice(others)
                # the following code is ugly as hell. I should do something with it later.
                if f.ret_performance > otter.ret_performance:
                    f.ret_rank = 1
                elif f.ret_performance < otter.ret_performance:
                    f.ret_rank = 2
                else:
                    f.ret_rank = random.choice([1, 2])
            for w in workers:
                others = [p for p in workers if p != w]
                # this will work even if there is only one extra worker (mostly for debugging)
                otters = random.choices(others, k=2)
                rank_list = sorted([w, ] + otters, key=lambda i: i.ret_performance, reverse=True)
                # we should check there are no ties:
                rank_dict = dict(enumerate(rank_list))
                candidates = [i for i, j in rank_dict.items() if j.ret_performance == w.ret_performance]
                w.ret_rank = random.choice(candidates) + 1
        else:
            for p in self.get_players():
                p.ret_rank = p.in_round(self.round_number - 1).ret_rank
        for p in self.get_players():
            p.set_contribution()
        for g in self.get_groups():
            g.revenue = g.firm.contribution + g.worker.contribution
            g.suggested_wage = random.randint(1, g.worker.contribution)


class Group(BaseGroup):
    revenue = models.CurrencyField()
    suggested_wage = models.CurrencyField()
    accept_initial = models.BooleanField(widget=widgets.RadioSelect,
                                         choices=Constants.ACCEPT_CHOICES,
                                         doc='in choice treatment did the worker accepted the wage suggested by comp')
    negotiations_failed = models.BooleanField(widget=widgets.RadioSelectHorizontal,
                                              doc='set to True if negotiations ended without accepting the wage')
    wage_accepted = models.CurrencyField(doc='a bit of doubling: to store the wage amount accepted ')

    def get_channel_group_name(self):
        return 'nego_group_{}'.format(self.pk)

    @property
    def firm(self):
        return self.get_player_by_role('firm')

    @property
    def worker(self):
        return self.get_player_by_role('worker')

    def get_offers_by_firm(self):
        return self.offers.filter(sender=self.firm)

    def get_offers_by_worker(self):
        return self.offers.filter(sender=self.worker)

    def set_payoffs(self):
        if self.negotiations_failed:
            self.wage_accepted = self.suggested_wage
            self.firm.payoff = self.revenue - self.suggested_wage - Constants.fine
            self.worker.payoff = self.suggested_wage - Constants.fine
            return
        if self.accept_initial:
            self.wage_accepted = self.suggested_wage
        else:
            accepted_offer = self.offers.filter(accept=True).first()
            self.wage_accepted = accepted_offer.amount
        self.firm.payoff = self.revenue - self.wage_accepted
        self.worker.payoff = self.wage_accepted


class Player(BasePlayer):
    ret_performance = models.IntegerField(doc='points earned during ret')
    ret_rank = models.IntegerField(doc='ranking within a subsession/subsample; 2-sample for firms, '
                                       '3-sample for workers')
    contribution = models.CurrencyField()
    # DEBUG TODO  - something smarter, take from Jordan's project
    dump_tasks = models.LongStringField()
    num_answered = models.IntegerField(initial=0)
    num_correct = models.IntegerField(initial=0)
    num_incorrect = models.IntegerField(initial=0)

    # END DEBUG

    def set_contribution(self):
        self.contribution = Constants.rank_contribution_lookup[self.role()][self.ret_rank]

    def get_another(self):
        return self.get_others_in_group()[0]

    def role(self):
        if self.id_in_group == 1:
            return 'worker'
        return 'firm'


class Offer(djmodels.Model):
    class Meta:
        ordering = ['-created_at']

    group = djmodels.ForeignKey(to=Group, related_name='offers')
    sender = djmodels.ForeignKey(to=Player, related_name='offers_sent')
    receiver = djmodels.ForeignKey(to=Player, related_name='offers_received')
    amount = models.IntegerField()
    accept = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def as_dict(self):
        return {'sender': self.sender.role(),
                'amount': self.amount}


class Task(djmodels.Model):
    task_type = models.IntegerField()
    player = djmodels.ForeignKey(to=Player, related_name='tasks')
    correct_answer = models.IntegerField()
    answer = models.IntegerField(null=True)

    def get_body(self):
        if self.task_type == 1:
            return list(self.digits.all().values_list('digit', flat=True))
        else:
            return list(self.zeroes.all().values_list('zstring', flat=True))

    def as_dict(self):
        return {'task_type': self.task_type,
                'correct_answer': self.correct_answer,
                'body': self.get_body()}

    @classmethod
    def post_create(cls, sender, instance, created, *args, **kwargs):
        if not created:
            return
        if instance.task_type == 1:
            digits = [Digit(digit=random.randint(*Constants.digits_range), task=instance) for i in
                      range(Constants.num_digits)]
            instance.digits.bulk_create(digits)
            instance.correct_answer = instance.digits.all().aggregate(Sum('digit'))['digit__sum']
        if instance.task_type == 2:
            for i in range(Constants.num_zero_rows):
                zstring = ''.join([str(random.choice([0, 1])) for i in range(Constants.len_zero_row)])
                instance.zeroes.create(zstring=zstring, num_zeroes=zstring.count('0'))
            instance.correct_answer = instance.zeroes.all().aggregate(Sum('num_zeroes'))['num_zeroes__sum']
        instance.save()


class Digit(djmodels.Model):
    task = djmodels.ForeignKey(to=Task, related_name='digits')
    digit = models.IntegerField()


class ZeroString(djmodels.Model):
    task = djmodels.ForeignKey(to=Task, related_name='zeroes')
    zstring = models.LongStringField()
    num_zeroes = models.IntegerField()


post_save.connect(Task.post_create, sender=Task)
