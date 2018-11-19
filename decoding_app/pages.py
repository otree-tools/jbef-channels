from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants
import json
import random
from datetime import date, datetime


# Some functions to deal with datetime serialization


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


# end of datetime ser function block

# stub classes  for orange and blue players
class OPPage(Page):
    def is_displayed(self):
        return self.player.role() == 'orange'


class BPPage(Page):
    def is_displayed(self):
        return self.player.role() == 'blue'


class RETPage(Page):
    template_name = 'decoding_app/WorkPage.html'
    _allow_custom_attributes = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_index'] = self._index_in_pages
        return context

    def vars_for_template(self):
        unanswered_tasks = self.player.get_unfinished_tasks()
        if unanswered_tasks.exists():
            task = unanswered_tasks.first()
        else:
            task = self.player.tasks.create()
        t = zip(task.digits, task.letters)
        return {'num_digits': range(Constants.num_digits),
                'task': t,
                'question': ''.join(task.question)}


class Consent(Page):
    form_model = 'player'
    form_fields = ['consent_agree']


class Intro1(Page):
    ...


class RoleAnnouncement(Page):
    def vars_for_template(self):
        return {'role': '{} player'.format(self.player.role())}


class TaskPresented(Page):
    ...


class TaskProcedure(Page):
    ...


class Practice(RETPage):
    title = 'Decoding task: practice round'
    timeout_seconds = Constants.practice_task_time_seconds

    def before_next_page(self):
        self.player.practice_tasks_solved = self.player.num_correct
        self.player.dump_practice_tasks = json.dumps(list(self.player.get_answered_tasks().values()),
                                                     default=json_serial)


class CompensationExplained(Page):
    ...


class CompensationSummary(Page):
    ...


class ControlQuestions(Page):
    form_model = 'player'
    form_fields = ['cq1', 'cq2', 'cq3']

    def cq1_error_message(self, value):
        if self.group.treatment == 'absolute' and value == 1:
            return """
                Your selection is incorrect. Blue Player earnings are dependent only on what
                they, themselves, submit as their REPORTED
                """
        if self.group.treatment == 'relative' and value == 0:
            return """
                Your selection is incorrect. Blue Player earnings are dependent on what all three
                Blue Players within a group submit as their REPORTED
                """

    def cq2_error_message(self, value):
        if value == 0:
            return """
            Your selection is incorrect. The Orange Player chooses whether or not to
            enact the REPORTING RULE
            """

    def cq3_error_message(self, value):
        if value != 3:
            err_msg = {
                1: """
                Your selection is incorrect. The Orange Player will never participate in the
                live round of the Decoding Task. The correct answer is C: if the REPORTING RULE is enacted,
                Blue Players are required to report the actual number of puzzles they solved correctly.
                """,
                2: """
                Your selection is incorrect. The Decoding Task puzzles are always 8 digits
                long. The correct answer is C: if the REPORTING RULE is enacted, Blue Players are required to
                report the actual number of puzzles they solved correctly.
                """,
                4: """
                Your selection is incorrect. All Blue Players will participate in the live
                round of the Decoding Task. The correct answer is C: if the REPORTING RULE is enacted,
                Blue Players are required to report the actual number of puzzles they solved correctly.
                """
            }
            return err_msg[value]


class OrangeRuleEnacting(OPPage):
    form_model = 'group'
    form_fields = ['reporting_rule']

    def before_next_page(self):
        if self.group.reporting_rule:
            self.group.task_field = 'tasks_solved'
        else:
            self.group.task_field = 'tasks_reported'


class RuleEnactingWP(WaitPage):
    # here BPs wait for OP decision about reporting rule. And OP will also wait here for BPs if someone of them
    # gets stuck on control questions or something. That means the content of this wp should differ for different
    # roles
    ...


class BeforeDecodingTask(BPPage):
    # This one is shown only to BPs. OP skips it
    ...


class OPChoosingPractice(OPPage):
    # op goes directly here to choose whether he should practice while waiting
    timeout_seconds = 60
    form_model = 'player'
    form_fields = ['op_practice_while_wait']


class BeforeTaskWP(WaitPage):
    # here all players wait to begin performing task
    ...


class Task(RETPage):
    timeout_seconds = Constants.task_time_seconds
    title = 'Decoding task: LIVE round'

    # BPs do some tasks. OP is waiting - if he didn't choose to practice
    def is_displayed(self):
        if self.player.role() == 'orange':
            self.title = 'Decoding task: Practice round'
        return self.player.role() == 'blue' or self.player.op_practice_while_wait is True

    def before_next_page(self):
        if self.player.role() == 'blue':
            self.player.tasks_solved = self.player.num_correct
        else:
            self.player.op_tasks_solved = self.player.num_correct
        self.player.dump_live_tasks = json.dumps(list(self.player.get_answered_tasks().values()),
                                                 default=json_serial)


class AfterTaskWP(WaitPage):
    # op should wait  here for all bps make their tasks
    # if some bps manage to finish earlier (they should't because of the wp in the beginning of the task)
    # they also end up here with the message 'let's wait for other BPs finishing their tasks'
    ...


class OPWhileBPReport(OPPage):
    ...


class BPReport(BPPage):
    form_model = 'player'
    form_fields = ['tasks_reported',
                   'bp_rule_preference'
                   ]

    def vars_for_template(self):
        return {
            'min_rep': 0,
            'max_rep': self.player.tasks_solved * Constants.max_report_coef,

        }

    def tasks_reported_max(self):
        return self.player.tasks_solved * Constants.max_report_coef


class AfterReportingWP(WaitPage):
    # OP waits here while BPs make their reporting decisions. Fast BPs also wait here (with slightly different message)
    def after_all_players_arrive(self):
        self.group.set_task_payoffs()


class ReportingRuleAnnouncement(Page):
    def vars_for_template(self):
        stage1_in_real = self.player.task_payoff.to_real_world_currency(self.session)
        tot_so_far = self.session.config['participation_fee'] + stage1_in_real
        return {
            'stage1_in_real': stage1_in_real,
            'tot_so_far': tot_so_far,
        }


        # OP and BPs are announced about the rule enacted.


class RDChoice(BPPage):
    form_model = 'player'
    form_fields = ['rd_choice']


class RDAmount(BPPage):
    form_model = 'player'
    form_fields = ['rd_amount']

    def is_displayed(self):
        return super().is_displayed() and self.player.rd_choice != 0

    def rd_amount_max(self):
        return self.player.task_payoff * Constants.rp_coef


class OPWhileBPReward(OPPage):
    ...


class AfterRDWP(WaitPage):
    # OP waits here for BPs punishment/reward decisions. Fast BPs also wait here for decision of others
    def after_all_players_arrive(self):
        self.group.set_final_payoffs()


class Results(Page):
    ...


page_sequence = [
    Consent,
    Intro1,
    RoleAnnouncement,
    TaskPresented,
    TaskProcedure,
    Practice,
    CompensationExplained,
    CompensationSummary,
    ControlQuestions,
    OrangeRuleEnacting,
    RuleEnactingWP,
    BeforeDecodingTask,
    OPChoosingPractice,
    BeforeTaskWP,
    Task,
    AfterTaskWP,
    OPWhileBPReport,
    BPReport,
    AfterReportingWP,
    ReportingRuleAnnouncement,
    RDChoice,
    RDAmount,
    OPWhileBPReward,
    AfterRDWP,
]
