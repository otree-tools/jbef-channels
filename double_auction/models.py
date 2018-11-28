from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random
import json
from django.db import models as djmodels
from django.db.models import F, Q, Sum, ExpressionWrapper
from django.db.models.signals import post_save, pre_save

from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.core.exceptions import ObjectDoesNotExist
from channels import Group as ChannelGroup

from .exceptions import NotEnoughFunds, NotEnoughItemsToSell

author = ''

doc = """
A double auction for oTree.

Instructions are mostly taken from http://veconlab.econ.virginia.edu/da/da.php, Virginia University.
"""


class Constants(BaseConstants):
    name_in_url = 'double_auction'
    players_per_group = None

    num_rounds = 1
    units_per_seller = 4
    units_per_buyer = 4
    time_per_round = 300
    multiple_unit_trading = False
    price_max_numbers = 10
    price_digits = 2
    initial_quantity = 1
    seller_cost_range = (1, 10)
    buyer_value_range = (1, 10)
    endowment_range = (10, 50)


class Subsession(BaseSubsession):
    num_sellers = models.IntegerField()
    num_buyers = models.IntegerField()

    def creating_session(self):
        self.num_buyers = self.session.config.get('buyers')
        self.num_sellers = self.session.config.get('sellers')
        if self.session.num_participants % (self.num_buyers + self.num_sellers) != 0:
            raise Exception('Number of participants is not divisible by number of sellers and buyers')


class Group(BaseGroup):
    active = models.BooleanField(initial=True)

    def get_channel_group_name(self):
        return 'double_auction_group_{}'.format(self.pk)

    def get_players_by_role(self, role):
        return [p for p in self.get_players() if p.role() == role]

    def get_buyers(self):
        return self.get_players_by_role('buyer')

    def get_sellers(self):
        return self.get_players_by_role('seller')

    def get_contracts(self):
        return Contract.objects.filter(Q(bid__player__group=self) | Q(ask__player__group=self))

    def get_bids(self):
        return Bid.active_statements.filter(player__group=self).order_by('-created_at')

    def get_asks(self):
        return Ask.active_statements.filter(player__group=self).order_by('-created_at')

    def get_spread_html(self):
        return mark_safe(render_to_string('double_auction/includes/spread_to_render.html', {
            'group': self,
        }))

    def no_buyers_left(self) -> bool:
        return not any([p.active for p in self.get_buyers()])

    def no_sellers_left(self) -> bool:
        return not any([p.active for p in self.get_sellers()])

    def is_market_closed(self) -> bool:
        return any(self.no_buyers_left(), self.no_sellers_left())

    def best_ask(self):
        bests = self.get_asks().order_by('price')
        if bests.exists():
            return bests.first()

    def best_bid(self):
        bests = self.get_bids().order_by('price')
        if bests.exists():
            return bests.last()

    def presence_check(self):
        msg = {'market_over': False}
        if self.no_buyers_left():
            # todo: check this out later
            self.active = False
            self.save()
            msg = {'market_over': True,
                   'over_message': 'No buyers left'}

        if self.no_sellers_left():
            self.active = False
            self.save()
            msg = {'market_over': True,
                   'over_message': 'No sellers left'}
        return msg


class Player(BasePlayer):
    active = models.BooleanField(initial=True)
    endowment = models.CurrencyField(initial=0)

    def role(self):

        if self.id_in_group <= self.subsession.num_sellers:
            return 'seller'
        else:
            return 'buyer'

    def set_payoff(self):
        contracts = self.get_contracts_queryset()
        self.payoff = self.endowment
        if contracts:
            sum_contracts = sum([p.profit for p in contracts])
            self.payoff += sum_contracts

    def is_active(self):
        if self.role() == 'buyer':
            return self.endowment > 0 and self.has_free_slots()
        else:
            return self.get_full_slots().exists()

    def get_items(self):
        return Item.objects.filter(slot__owner=self)

    def get_slots(self):
        return self.slots.all()

    def has_free_slots(self):
        return self.slots.filter(item__isnull=True).exists()

    def get_free_slot(self):
        if self.has_free_slots():
            return self.slots.filter(item__isnull=True).order_by('-value').first()

    def get_full_slots(self):
        return self.slots.filter(item__isnull=False)

    def presence_check(self):
        msg = {'market_over': False}

        if not self.is_active():
            if self.role() == 'buyer':
                if self.endowment <= 0:
                    msg = {'market_over': True,
                           'over_message': 'No funds left for trading'}
                if not self.has_free_slots():
                    msg = {'market_over': True,
                           'over_message': 'No slots available for trading left'}
            else:
                msg = {'market_over': True,
                       'over_message': 'No items available for trading left'}
        return msg

    def get_repo_context(self):
        repository = self.get_slots().annotate(quantity=F('item__quantity'))
        if self.role() == 'seller':
            r = repository.order_by('cost')
        else:
            r = repository.order_by('-value')
        return r

    def get_repo_html(self):
        return mark_safe(render_to_string('double_auction/includes/repo_to_render.html', {
            'repository': self.get_repo_context()
        }))

    def get_asks_html(self):
        asks = self.group.get_asks()
        return mark_safe(render_to_string('double_auction/includes/asks_to_render.html',
                                          {'asks': asks,
                                           'player': self}))

    def get_bids_html(self):
        bids = self.group.get_bids()
        return mark_safe(render_to_string('double_auction/includes/bids_to_render.html',
                                          {
                                              'bids': bids,
                                              'player': self}
                                          ))

    def get_contracts_queryset(self):
        contracts = self.get_contracts()
        if self.role() == 'seller':
            cost_value = F('cost')
            formula = (F('item__contract__price') - cost_value) * F('item__quantity')
        else:
            cost_value = F('value')
            formula = (cost_value - F('item__contract__price')) * F('item__quantity')

        r = contracts.annotate(profit=ExpressionWrapper(formula, output_field=models.CurrencyField()),
                               cost_value=cost_value,
                               )

        return r

    def get_contracts_html(self):

        return mark_safe(render_to_string('double_auction/includes/contracts_to_render.html', {
            'contracts': self.get_contracts_queryset()
        }))

    def get_form_context(self):
        if self.role() == 'buyer':
            no_statements = not self.get_bids().exists()
            no_slots_or_funds = self.endowment <= 0 or not self.has_free_slots()
        else:
            no_slots_or_funds = not self.get_full_slots().exists()
            no_statements = not self.get_asks().exists()

        return {'no_slots_or_funds': no_slots_or_funds,
                'no_statements': no_statements, }

    def get_form_html(self):
        context = self.get_form_context()
        context['player'] = self
        return mark_safe(render_to_string('double_auction/includes/form_to_render.html', context))

    def profit_block_html(self):
        return mark_safe(render_to_string('double_auction/includes/profit_to_render.html', {'player': self}))

    def get_contracts(self):
        return Contract.objects.filter(Q(bid__player=self) | Q(ask__player=self))

    def get_bids(self):
        return self.bids.all()

    def get_asks(self):
        return Ask.active_statements.filter(player=self)
        # return self.asks.all()

    def action_name(self):
        if self.role() == 'buyer':
            return 'bid'
        return 'ask'

    def get_last_statement(self):
        try:
            if self.role() == 'seller':
                return self.asks.filter(active=True).latest('created_at')
            else:
                return self.bids.filter(active=True).latest('created_at')
        except ObjectDoesNotExist:
            # todo: think a bit what happens if last bid is non existent?
            return

    def item_to_sell(self):
        full_slots = self.get_full_slots().order_by('cost')
        if full_slots.exists():
            return full_slots.first().item

    def get_personal_channel_name(self):
        return '{}_{}'.format(self.role(), self.id)


class BaseRecord(djmodels.Model):
    quantity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    player = djmodels.ForeignKey(to=Player,
                                 related_name="%(class)ss", )

    class Meta:
        abstract = True


class ActiveStatementManager(djmodels.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(active=True, player__active=True)


class BaseStatement(BaseRecord):
    price = djmodels.DecimalField(max_digits=Constants.price_max_numbers, decimal_places=Constants.price_digits)
    # initially all bids and asks are active. when the contracts are created with their participation they got passive
    active = models.BooleanField(initial=True)
    active_statements = ActiveStatementManager()

    class Meta:
        abstract = True

    def __str__(self):
        return '{}. Price:{}, Quantity:{}. Created at: {}. Updated at: {}'. \
            format(self.__class__.__name__, self.price, self.quantity, self.created_at, self.updated_at)

    def as_dict(self):
        return {'price': str(self.price),
                'quantity': self.quantity}


class Ask(BaseStatement):
    @classmethod
    def pre_save(cls, sender, instance, *args, **kwargs):
        items_available = Item.objects.filter(slot__owner=instance.player)
        if items_available.count() == 0:
            raise NotEnoughFunds(instance.player)
        num_items_available = items_available.aggregate(num_items=Sum('quantity'))
        if num_items_available['num_items'] < int(instance.quantity):
            raise NotEnoughFunds(instance.player)

    # TODO: move both sginsls (ask, bid) under one method
    @classmethod
    def post_save(cls, sender, instance, created, *args, **kwargs):
        if not created:
            return
        group = instance.player.group
        bids = Bid.active_statements.filter(player__group=group, price__gte=instance.price).order_by('created_at')
        if bids.exists():
            bid = bids.last()  ## think about it??
            item = instance.player.item_to_sell()
            if item:
                # we convert to float because in the bd decimals are stored as strings (at least in post_save they are)
                Contract.create(bid=bid,
                                ask=instance,
                                price=min([bid.price, float(instance.price)]),
                                item=item)


class Bid(BaseStatement):
    @classmethod
    def pre_save(cls, sender, instance, *args, **kwargs):
        if instance.player.endowment < float(instance.price) * int(instance.quantity):
            raise NotEnoughFunds(instance.player)

    @classmethod
    def post_save(cls, sender, instance, created, *args, **kwargs):
        if not created:
            return
        group = instance.player.group
        asks = Ask.active_statements.filter(player__group=group, price__lte=instance.price).order_by('created_at')
        if asks.exists():
            ask = asks.last()  ## think about it??
            # todo: redo all this mess
            item = ask.player.item_to_sell()
            if item:
                Contract.create(bid=instance,
                                ask=ask,
                                price=min([float(instance.price), ask.price]),
                                item=item)



class Slot(djmodels.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = djmodels.ForeignKey(to=Player, related_name="slots", )
    cost = models.FloatField(doc='this is defined for sellers only', null=True)
    value = models.FloatField(doc='for buyers only', null=True)


class Item(djmodels.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slot = djmodels.OneToOneField(to=Slot, related_name='item')
    quantity = models.IntegerField()


class Contract(djmodels.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # the o2o field to item should be reconsidered if we make quantity flexible
    item = djmodels.OneToOneField(to=Item)
    bid = djmodels.OneToOneField(to=Bid)
    ask = djmodels.OneToOneField(to=Ask)
    price = djmodels.DecimalField(max_digits=Constants.price_max_numbers, decimal_places=Constants.price_digits)
    cost = models.CurrencyField()
    value = models.CurrencyField()

    def get_seller(self):
        return self.ask.player

    def get_buyer(self):
        return self.bid.player

    def __str__(self):
        return '{}. Price:{}, Quantity:{}. BID by: {}. ASK BY: {}'. \
            format(self.__class__.__name__, str(self.price), self.item.quantity, self.bid.player.id, self.ask.player.id)

    @classmethod
    def create(cls, item, bid, ask, price):
        buyer = bid.player
        seller = ask.player
        cost = item.slot.cost
        new_slot = buyer.get_free_slot()
        item.slot = new_slot
        value = new_slot.value
        contract = cls(item=item, bid=bid, ask=ask, price=price, cost=cost, value=value)
        bid.active = False
        ask.active = False
        ask.save()
        bid.save()
        item.save()
        buyer.endowment -= contract.price
        contract_parties = [buyer, seller]
        contract.save()

        for p in contract_parties:
            p.set_payoff()
            p.active = p.is_active()
            p.save()
            p_group = ChannelGroup(p.get_personal_channel_name())
            p_group.send(
                {'text': json.dumps({
                    'repo': p.get_repo_html(),
                    'contracts': p.get_contracts_html(),
                    'form': p.get_form_html(),
                    'profit': p.profit_block_html(),
                    'presence': p.presence_check(),
                })}
            )
        group = buyer.group
        group_channel = ChannelGroup(group.get_channel_group_name())
        group_channel.send({'text': json.dumps({'presence': group.presence_check()})})

        return contract


post_save.connect(Ask.post_save, sender=Ask)
post_save.connect(Bid.post_save, sender=Bid)
pre_save.connect(Ask.pre_save, sender=Ask)
pre_save.connect(Bid.pre_save, sender=Bid)
