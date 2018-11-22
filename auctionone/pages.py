from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants, Group, Subsession, JobContract
import time


# 3 helpful page types
class EmployerPage(Page):
    def is_displayed(self):
        return self.player.role() == 'employer' and self.extra_is_displayed()

    def extra_is_displayed(self):
        return True


class WorkerPage(Page):
    def is_displayed(self):
        return self.player.role() == 'worker' and self.extra_is_displayed()

    def extra_is_displayed(self):
        return True


class ActiveWorkerPage(Page):
    def is_displayed(self):
        return self.player.role() == 'worker' and self.player.matched and self.extra_is_displayed()

    def extra_is_displayed(self):
        return True


# ########### the actual pages start here ############# #
class Role(Page):
    def is_displayed(self):
        if self.subsession.round_number == 1:
            return True


class BeforeAuctionWP(WaitPage):
    body_text = "A new round is about to start, please wait for the other players."

    wait_for_all_groups = True


class Auction(Page):
    timeout_seconds = 60
    _allow_custom_attributes = True

    def get_template_names(self):
        if self.player.role() == 'employer':
            return ['auctionone/Auction.html']
        else:
            return ['auctionone/Accept.html']

    def extra_is_displayed(self):
        if self.player.role() == 'employer':
            closed_contract = self.player.contract.filter(accepted=True).exists()
        else:
            closed_contract = self.player.work_to_do.filter(accepted=True).exists()
        return not closed_contract

    def vars_for_template(self):
        active_contracts = JobContract.objects.filter(accepted=False, employer__group=self.group).values('pk', 'amount')
        return {'active_contracts': active_contracts, }


class AfterAuctionWP(WaitPage):
    body_text = "Your decision has been registered, please wait for the other participants."

    def after_all_players_arrive(self):
        for g in self.subsession.get_groups():
            wages = []
            for p in g.get_players():
                if g.get_player_by_id(p.id_in_group).wage_offer:
                    wages.append(g.get_player_by_id(p.id_in_group).wage_offer)
            g.wage_list = str(wages)[1:-1]


class AuctionResultsEmployer(EmployerPage):
    def vars_for_template(self):
        if self.player.matched == 1:
            if self.player.role() == "employer":
                closed_contract = self.player.contract.get(accepted=True)
            return {'wage': closed_contract.amount}


class AuctionResultsWorker(WorkerPage):
    def vars_for_template(self):
        if self.player.matched == 1:
            if self.player.role() == "worker":
                closed_contract = self.player.work_to_do.get(accepted=True)
            return {'wage': closed_contract.amount}


class Start(ActiveWorkerPage):
    ...


class WorkPage(ActiveWorkerPage):
    timer_text = "Time remaining in this stage"
    timeout_seconds = Constants.task_time

    def vars_for_template(self):
        if self.player.role() == "worker":
            closed_contract = self.player.work_to_do.get(accepted=True)
        elif self.player.role() == "employer":
            closed_contract = self.player.contract.get(accepted=True)
        return {'wage': closed_contract.amount}

    def before_next_page(self):
        closed_contract = self.player.work_to_do.get(accepted=True)
        closed_contract.tasks_corr = self.player.tasks_correct
        closed_contract.tasks_att = self.player.tasks_attempted
        closed_contract.save()


class BeforeResultsWP(WaitPage):
    def after_all_players_arrive(self):
        self.group.set_payoffs()


class Results(Page):
    def vars_for_template(self):
        if self.player.role() == "employer":
            closed_contract = self.player.contract.get(accepted=True)
            worker_pk = closed_contract.worker
            partner_payoff = worker_pk.payoff
        else:
            closed_contract = self.player.work_to_do.get(accepted=True)
            employer_pk = closed_contract.employer
            partner_payoff = employer_pk.payoff
        return {'wage': closed_contract.amount,
                'tasks_attempted': closed_contract.tasks_att,
                'tasks_correct': closed_contract.tasks_corr,
                'partner_payoff': partner_payoff}


page_sequence = [
    Role,
    BeforeAuctionWP,
    Auction,
    AfterAuctionWP,
    AuctionResultsEmployer,
    AuctionResultsWorker,
    Start,
    WorkPage,
    BeforeResultsWP,
    Results,
]
