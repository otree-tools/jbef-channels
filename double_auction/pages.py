from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants, Item
import random


class IntroWp(WaitPage):
    group_by_arrival_time = True

    def get_players_for_group(self, waiting_players):
        if len(waiting_players) >= self.subsession.num_sellers + self.subsession.num_buyers:
            return waiting_players


class GeneratingInitialsWP(WaitPage):
    def after_all_players_arrive(self):
        c = Constants
        g = self.group
        for s in g.get_sellers():
            # we create slots for both sellers and buyers, but for sellers we fill them with items
            # and also pregenerate costs. For buyers they are initially empty
            for i in range(c.units_per_seller):
                slot = s.slots.create(cost=random.randint(*c.seller_cost_range))
                item = Item(slot=slot, quantity=Constants.initial_quantity)
                item.save()

        for b in g.get_buyers():
            for i in range(Constants.units_per_buyer):
                b.endowment = random.randrange(*c.endowment_range)
                b.slots.create(value=random.randint(*c.buyer_value_range))


class Market(Page):
    timeout_seconds = Constants.time_per_round

    def is_displayed(self):
        return self.player.active and self.group.active

    def vars_for_template(self):
        c = self.player.get_form_context()
        c['asks'] = self.group.get_asks()
        c['bids'] = self.group.get_bids()
        c['repository'] = self.player.get_repo_context()
        c['contracts'] = self.player.get_contracts_queryset()

        return c


class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(self):
        pass


class Results(Page):
    pass


page_sequence = [
    IntroWp,
    GeneratingInitialsWP,
    Market,
    # ResultsWaitPage,
    # Results
]
