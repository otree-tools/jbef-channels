from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants


class ChoosingDiff(Page):
    form_model = 'player'
    form_fields = ['difficulty']

    def vars_for_template(self):
        frm = self.get_form()
        f = frm['difficulty']

        return {'data': zip(Constants.diff_choices, f)}


class WorkPage(Page):
    timer_text = 'Time left to complete this round:'
    timeout_seconds = Constants.task_time

    def vars_for_template(self):
        return {"task": self.player.get_task()}

    def before_next_page(self):
        self.player.dump_tasks()
        self.player.set_payoff()


class Results(Page):
    ...


page_sequence = [
    WorkPage,
    Results,
]
