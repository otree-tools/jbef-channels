from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants


class WorkPage(Page):
    timer_text = 'Time left to complete this round:'
    timeout_seconds = Constants.task_time


page_sequence = [
    WorkPage,
]
