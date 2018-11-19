from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants
import channels
import json


def vars_for_all_templates(self):
    curblock_len = getattr(Constants, 'len_{}_block'.format(self.subsession.block_name))
    return {'curblock_len': curblock_len}


class TypePage(Page):
    start_block_page = None
    template_name = 'negotiations/TypePage.html'


class TypeAnnouncement(TypePage):
    start_block_page = True

    def is_displayed(self):
        return self.round_number in Constants.ret_rounds


class TaskInstructions(Page):
    def is_displayed(self):
        return self.round_number in Constants.ret_rounds


class BeforeWorkWP(WaitPage):
    def vars_for_template(self):
        return {'body_text': 'Please wait for the {}'.format(self.player.get_another().role())}


class WorkPage(Page):
    timer_text = 'Time left to complete the task:'
    timeout_seconds = Constants.ret_timeout_seconds
    _allow_custom_attributes = True

    def get_timeout_mins(self):
        return round(self.timeout_seconds / 60, 2)

    def is_displayed(self):
        return self.round_number in Constants.ret_rounds

    def vars_for_template(self):
        if self.subsession.task_type == 1:
            r = {'num_digits': range(Constants.num_digits),
                 'min_digits': Constants.lb * Constants.num_digits,
                 'max_digits': Constants.ub * Constants.num_digits}
        if self.subsession.task_type == 2:
            r = {'min_digits': 0,
                 'max_digits': Constants.num_zero_rows * Constants.len_zero_row
                 }
        return r

    def before_next_page(self):
        self.player.ret_performance = self.player.num_correct
        self.player.dump_tasks = json.dumps(list(self.player.tasks.all().values()))


class TaskPossibleResults(TypePage):
    def before_next_page(self):
        # TODO: do something smarter than this BS with the fact that ret performance exists only in RET rounds
        if self.round_number not in Constants.ret_rounds:
            self.player.ret_performance = self.player.in_round(self.round_number - 1).ret_performance


class RankingWP(WaitPage):
    wait_for_all_groups = True

    def after_all_players_arrive(self):
        self.subsession.set_ranking()


class RankingResults(Page):
    ...


class PreChoice(Page):
    def is_displayed(self):
        return self.session.config.get('treatment') == 'choice' and self.player.role() == 'worker'


class Choice(Page):
    form_model = 'group'
    form_fields = ['accept_initial']

    def is_displayed(self):
        return self.session.config.get('treatment') == 'choice' and self.player.role() == 'worker'


class BeforeNegoWP(WaitPage):
    def vars_for_template(self):
        return {'body_text': 'Please wait for the {}'.format(self.player.get_another().role())}


class Negotiations(Page):
    timeout_seconds = Constants.nego_timeout_seconds

    def is_displayed(self):
        if self.session.config.get('treatment') == 'always':
            return True
        return not self.group.accept_initial

    def vars_for_template(self):
        # the following we need to limit input of offers
        return {
            'lb': int(max(self.group.suggested_wage - Constants.offer_epsilon, 0)),
            'ub': int(self.group.suggested_wage + Constants.offer_epsilon),
        }

    def before_next_page(self):
        if self.timeout_happened:
            # TODO: do something with this message which can be misleading if someone works on this project later
            channels.Group(self.group.get_channel_group_name()).send(
                {'text': json.dumps({'accept': True})})
            self.group.negotiations_failed = True


class AfterNegoWP(WaitPage):
    def after_all_players_arrive(self):
        self.group.set_payoffs()


class Results(Page):
    ...


class BeforeNextRound(Page):
    def is_displayed(self):
        if not self.subsession.end_of_block_A_round:
            return self.round_number < Constants.num_rounds
        else:
            return True

    def vars_for_template(self):
        curblock_len = getattr(Constants, 'len_{}_block'.format(self.subsession.block_name))
        return {'curblock_len': curblock_len}


class FinalResults(Page):
    def is_displayed(self):
        return self.round_number == Constants.num_rounds


page_sequence = [
    TypeAnnouncement,
    TaskInstructions,
    BeforeWorkWP,
    WorkPage,
    TaskPossibleResults,
    RankingWP,
    RankingResults,
    PreChoice,
    Choice,
    BeforeNegoWP,
    Negotiations,
    AfterNegoWP,
    Results,
    BeforeNextRound,
    # FinalResults,
]
