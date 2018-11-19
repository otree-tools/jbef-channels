from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)

from django.db import models as djmodels
import random
from django.db.models.signals import post_save
from .fields import ListField
import string
import itertools
from survey.fields import AgreeField
from otree.common_internal import random_chars_10
author = 'Philipp Chapkovski, chapkovski@gmail.com'

doc = """
Decoding game for Jordan Samet
"""


class Constants(BaseConstants):
    name_in_url = 'decoding_app'
    players_per_group = 4
    num_rounds = 1
    treatments = ['relative', 'absolute']
    practice_task_time_seconds = 4 * 60  # how long does the Practice task lasts in seconds
    task_time_seconds = 4 * 60  # how long does the LIVE task lasts in seconds
    max_report_coef = 2  # by how much the BP can exxagerate their earnings
    task_fee_reported = c(.5)
    task_fee_solved = c(1)
    rel_achiever_salary = c(19)
    rel_low_salary = c(6)
    # task_fee_achiever = c(2)
    rp_coef = 2  # coefficient of reward/punishment efficiency
    ###### RET BLOCK #######
    task_len = 8
    num_digits = 10
    num_letters = 10
    ###### END OF RET BLOCK #######
    ###### CHOICES BLOCK #######
    RULE_ENACTMENT_CHOICES = [(True, 'Yes, I choose to enact the RULE'),
                              (False, 'No, I choose not to enact the RULE'), ]
    CQ1_CHOICES = [(1, 'True'),
                   (0, 'False'), ]

    CQ2_CHOICES = [(0, 'Blue player'), (1, 'Orange player')]
    CQ3_CHOICES = [
        (1, 'A. The Orange Player must participate in the Decoding Task in the Live Round'),
        (2, 'B. The Decode puzzles will be 12 digits long instead of 8 digits long'),
        (3, 'C. The Blue Players’ report will equal the actual number of puzzles solved correctly.'),
        (4, 'D. One of the Blue Players will be randomly selected to sit out '
            '(i.e. not participate in) the Live Round of the Decoding Task'),
    ]

    RD_CHOICES = [(-1, 'Decrease Orange Player’s Earnings'),
                  (0, 'No Change'),
                  (1, 'Increase Orange Player’s Earnings')]


###### END OFCHOICES BLOCK #######


# ERR MESSAGES:
no_treatment_err = 'no such treatment'


class Subsession(BaseSubsession):
    def creating_session(self):
        if self.round_number == 1:
            for p in self.get_players():
                p._role = p.role()
        if self.session.config.get('random'):
            ts = Constants.treatments.copy()
            random.shuffle(ts)
            cycle_ts = itertools.cycle(ts)
            for g in self.get_groups():
                g.treatment = next(cycle_ts)
        else:
            session_treatment = self.session.config.get('treatment')
            assert session_treatment in Constants.treatments, no_treatment_err
            for g in self.get_groups():
                g.treatment = session_treatment
        for g in self.get_groups():
            g.code = random_chars_10()
            rew_punisher = random.choice(g.BPs)
            g.chosen_rew_punisher = rew_punisher.id_in_group


class Group(BaseGroup):
    code = models.StringField(doc='unique identifier for group')
    treatment = models.StringField()
    reporting_rule = models.BooleanField(doc='OP decision about enacting reporting rule',
                                         label='Please make your choice',
                                         choices=Constants.RULE_ENACTMENT_CHOICES,
                                         widget=widgets.RadioSelect
                                         )
    chosen_rew_punisher = models.IntegerField(doc='who among BPs are chosen to implement reward/punishment decision')
    bp_achiever = models.IntegerField(doc='id in group of a BP  with the largest number of points earned')
    op_reward_punishment = models.CurrencyField(doc='effect on OP payoff from chosen rew punisher decision')
    task_field = models.StringField(doc='field name used for payofss calculation based on reporting rule chosen '
                                        'by OP')

    @property
    def OP(self):
        return self.get_player_by_role('orange')

    @property
    def BPs(self):
        return [p for p in self.get_players() if p.role() == 'blue']

    def set_task_payoffs(self):
        task_field = self.task_field

        if self.treatment == 'absolute':
            for b in self.BPs:
                b.task_payoff = getattr(b, task_field) * Constants.task_fee_reported
        else:
            self.set_bp_achiever()
            for b in self.BPs:
                if b.id_in_group == self.bp_achiever:
                    b.task_payoff = Constants.rel_achiever_salary  # Constants.task_fee_achiever
                else:
                    b.task_payoff = Constants.rel_low_salary  # Constants.task_fee_reported
        sum_reported = sum([getattr(b, task_field) for b in self.BPs])
        sum_solved = sum([b.tasks_solved for b in self.BPs])
        self.OP.task_payoff = sum_solved * Constants.task_fee_solved - sum_reported * Constants.task_fee_reported

    def set_reward_punishment(self):
        rp = self.get_player_by_id(self.chosen_rew_punisher)
        self.op_reward_punishment = rp.rd_choice * (rp.rd_amount or 0)
        self.OP.stage2_payoff = self.op_reward_punishment
        rp.stage2_payoff -= abs(self.op_reward_punishment) / Constants.rp_coef

    def set_bp_achiever(self):
        # find max achiever among bps
        tf = self.task_field
        max_tasks = max([getattr(b, tf) for b in self.BPs])
        achievers = self.player_set.filter(**{tf: max_tasks})
        self.bp_achiever = random.choice(achievers).id_in_group

    def set_final_payoffs(self):
        self.set_reward_punishment()
        for b in self.BPs:
            b.payoff += b.task_payoff + b.stage2_payoff
        self.OP.payoff = max(self.OP.task_payoff + self.OP.stage2_payoff, 0)


class Player(BasePlayer):
    _role = models.StringField(doc='role for export')
    task_payoff = models.CurrencyField(doc='payoff from Stage 1 (tasks)',
                                       initial=0)
    stage2_payoff = models.CurrencyField(doc='payoff from Stage 2 (reward/deduction)',
                                         initial=0)
    dump_practice_tasks = models.LongStringField()
    dump_live_tasks = models.LongStringField()
    practice_tasks_solved = models.IntegerField(initial=0,
                                                doc='tasks solved  during the Practice')
    op_tasks_solved = models.IntegerField(initial=0,
                                          doc='tasks solved by OP during the RET')
    tasks_solved = models.IntegerField(initial=0,
                                       doc='points earned during the RET')
    consent_agree = models.BooleanField(widget=widgets.CheckboxInput)
    tasks_reported = models.IntegerField(min=0)
    op_practice_while_wait = models.BooleanField(doc='if OP chooses to practice while waiting for BPs')
    bp_rule_preference = AgreeField()
    rd_choice = models.IntegerField(choices=Constants.RD_CHOICES, widget=widgets.RadioSelect,
                                    doc='choice to punish (-) or reward(+) or do nothing(0) with OP')
    rd_amount = models.IntegerField(doc='amount of deduction/reward points sent to OP')
    # ######## CONTROL QUESTIONS ########
    cq1 = models.IntegerField(
        label='Each Blue Player’s Stage 1 earnings are dependent on '
              'what the other Blue Player’s submit as their “# REPORTED”',
        choices=Constants.CQ1_CHOICES,
        widget=widgets.RadioSelect, )
    cq2 = models.IntegerField(label='Which Player Type determines whether the REPORTING RULE is enacted?',
                              choices=Constants.CQ2_CHOICES,
                              widget=widgets.RadioSelect, )
    cq3 = models.IntegerField(label='If the REPORTING RULE is enacted:',
                              choices=Constants.CQ3_CHOICES,
                              widget=widgets.RadioSelect,
                              )

    # ######## END OF CONTROL QUESTIONS ########
    # ######## TEMPBLOCK ########
    dump_tasks = models.LongStringField()

    def get_answered_tasks(self):
        # WARNING: the way it is done now it will return correct number of tasks only if method is called
        # by player from the workpage (because otherwise partcipant moves his position in index)
        curpage = self.participant._index_in_pages
        return self.tasks.filter(page_index=curpage, answer__isnull=False)

    @property
    def num_answered(self):
        # WARNING: the way it is done now it will return correct number of tasks only if method is called
        # by player from the workpage (because otherwise partcipant moves his position in index)
        curpage = self.participant._index_in_pages
        return self.get_answered_tasks().count()

    @property
    def num_correct(self):
        return self.get_answered_tasks().filter(is_correct=True).count()

    # ######## END OF TEMPBLOCK ########

    def role(self):
        if self.id_in_group == 1:
            return 'orange'
        else:
            return 'blue'

    def get_unfinished_tasks(self):
        curpage = self.participant._index_in_pages
        return self.tasks.filter(answer__isnull=True, page_index=curpage)


class Task(djmodels.Model):
    player = djmodels.ForeignKey(to=Player, related_name='tasks')
    question = ListField()
    correct_answer = ListField()
    digits = ListField()
    letters = ListField()
    answer = models.StringField(null=True)
    page_index = models.IntegerField()
    page_name = models.StringField(doc='page name of task submission', null=True)
    is_correct = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # todo: the following methods can and should be done through currying
    # https://stackoverflow.com/questions/5730211/how-does-get-field-display-in-django-work
    def get_str(self, field):
        return ''.join(getattr(self, field))

    def get_digits(self):
        return self.get_str('digits')

    def get_letters(self):
        return self.get_str('letters')

    def get_question(self):
        return self.get_str('question')

    def get_correct_answer(self):
        return self.get_str('correct_answer')

    def get_body(self):
        return {
            'question': self.question,
            'digits': self.digits,
            'letters': self.letters,
        }

    def decoding_dict(self):
        keys = self.digits
        values = self.letters
        dictionary = dict(zip(keys, values))
        return dictionary

    def get_decoded(self, to_decode):
        decdict = self.decoding_dict()
        return [decdict[i] for i in to_decode]

    def as_dict(self):
        # TODO: clean the mess with the body
        return {
            'body': self.get_body()
        }

    @classmethod
    def post_create(cls, sender, instance, created, *args, **kwargs):
        if not created:
            return
        instance.page_index = instance.player.participant._index_in_pages
        instance.page_name =  instance.player.participant._url_i_should_be_on().strip().split('/')[-3]
        digs = list(string.digits)
        random.shuffle(digs)
        instance.digits = digs
        lts = random.sample(string.ascii_lowercase, k=Constants.num_letters)
        instance.letters = lts
        instance.question = random.choices(string.digits, k=Constants.task_len)
        instance.correct_answer = instance.get_decoded(instance.question)
        instance.save()


post_save.connect(Task.post_create, sender=Task)
