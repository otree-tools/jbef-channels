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


class WP(WaitPage):
    body_text = "A new round is about to start, please wait for the other players."

    wait_for_all_groups = True

    def after_all_players_arrive(self):
        for bunch in self.subsession.get_groups():
            bunch.auctionenddate = time.time() + Constants.starting_time + 5


class CountDown(Page):
    timeout_seconds = 5
    timer_text = "The next stage starts in 5 seconds:  "


class Auction(EmployerPage):
    def extra_is_displayed(self):
        closed_contract = self.player.contract.filter(accepted=True).exists()
        return not any([self.group.day_over, closed_contract])

    def vars_for_template(self):
        active_contracts = JobContract.objects.filter(accepted=False, employer__group=self.group).values('pk', 'amount')
        return {'time_left': self.group.time_left(),
                'active_contracts': active_contracts,
                }


class Accept(WorkerPage):
    def extra_is_displayed(self):
        closed_contract = self.player.work_to_do.filter(accepted=True).exists()
        return not any([self.group.day_over, closed_contract])

    def vars_for_template(self):
        active_contracts = JobContract.objects.filter(accepted=False, employer__group=self.group).values('pk', 'amount')
        return {'time_left': self.group.time_left(),
                'active_contracts': active_contracts}


class WPage(WaitPage):
    body_text = "Your decision has been registered, please wait for the other participants."

    def after_all_players_arrive(self):
        for g in self.subsession.get_groups():
            wages = []
            for p in g.get_players():
                if g.get_player_by_id(p.id_in_group).wage_offer:
                    wages.append(g.get_player_by_id(p.id_in_group).wage_offer)
            print(wages)
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



class WaitP(WaitPage):
    template_name = 'auctionone/WaitP.html'

    def vars_for_template(self):
        self.group.work_end_date = time.time() + Constants.task_time + 30
        return {'time_left': self.group.time_work(),
                'wage': 0}

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
                'partner_payoff': partner_payoff }


page_sequence = [
    Role,
    WP, CountDown,
    Auction, Accept,
    WPage,
    AuctionResultsEmployer, AuctionResultsWorker,
    Start, WorkPage,
    WaitP,
    Results,
]