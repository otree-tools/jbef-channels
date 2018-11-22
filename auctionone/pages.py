from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants, Group, Subsession

import time


class ActiveWorkerPage(Page):
    def is_displayed(self):
        return self.player.role() == 'worker' and self.player.matched and self.extra_is_displayed()

    def extra_is_displayed(self):
        return True


# ########### the actual pages start here ############# #
class Role(Page):
    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        return {
            'lb': c(Constants.offer_range[0]),
            'ub': c(Constants.offer_range[-1]),
            'num_numbers': Constants.task_difficulty ** 2
        }


class BeforeAuctionWP(WaitPage):
    body_text = "A new round is about to start, please wait for the other players."


class Auction(Page):
    timeout_seconds = Constants.auction_time

    def is_displayed(self):
        return not self.player.matched and self.group.is_active()


class AfterAuctionWP(WaitPage):
    body_text = "Your decision has been registered, please wait for the other participants."


class AuctionResults(Page):
    pass


class Start(ActiveWorkerPage):
    def before_next_page(self):
        self.player.get_or_create_task()


#
class WorkPage(ActiveWorkerPage):
    timer_text = "Time remaining in this stage"
    timeout_seconds = Constants.task_time


class BeforeResultsWP(WaitPage):
    def after_all_players_arrive(self):
        self.group.set_payoffs()


class ResultsMatched(Page):
    def is_displayed(self):
        return self.player.matched


class ResultsUnmatched(Page):
    def is_displayed(self):
        return not self.player.matched


page_sequence = [
    Role,
    BeforeAuctionWP,
    Auction,
    AfterAuctionWP,
    AuctionResults,
    Start,
    WorkPage,
    BeforeResultsWP,
    ResultsMatched,
    ResultsUnmatched,
]
