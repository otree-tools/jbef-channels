from channels.generic.websockets import JsonWebsocketConsumer
from double_auction.models import Constants, Player, Group
from double_auction.exceptions import NotEnoughFunds, NotEnoughItemsToSell
import logging

logger = logging.getLogger(__name__)


class MarketTracker(JsonWebsocketConsumer):
    url_pattern = (r'^/market_channel/(?P<player_pk>[0-9]+)/(?P<group_pk>[0-9]+)$')

    def clean_kwargs(self):
        self.player_pk = self.kwargs['player_pk']
        self.group_pk = self.kwargs['group_pk']

    def connection_groups(self, **kwargs):
        group_name = self.get_group().get_channel_group_name()
        personal_channel = self.get_player().get_personal_channel_name()
        return [group_name, personal_channel]

    def get_player(self):
        self.clean_kwargs()
        return Player.objects.get(pk=self.player_pk)

    def get_group(self):
        self.clean_kwargs()
        return Group.objects.get(pk=self.group_pk)

    def receive(self, text=None, bytes=None, **kwargs):
        self.clean_kwargs()
        msg = text
        player = self.get_player()
        group = self.get_group()
        # Some ideas:
        # Each seller in the beginning has slots (like a deposit cells) filled with goods from his repo.
        # Each buyer also has empty slots (deposit cells) to fill in.
        # Each seller slot is associated with a certain cost of production.
        # Each buyer slot is associated with a certain value of owning the item in it (sounds strange)
        # buyer costs are associated with increasing cost of production (?)
        # seller values with diminishing marginal value
        # when two persons make a contract, an item is moved from  seller's cell to buyer's cell.

        if msg['action'] == 'new_statement':
            if player.role() == 'buyer':
                try:
                    bid = player.bids.create(price=msg['price'], quantity=msg['quantity'])

                except NotEnoughFunds:
                    logger.warning('not enough funds')
            else:
                try:
                    ask = player.asks.create(price=msg['price'], quantity=msg['quantity'])

                except NotEnoughItemsToSell:
                    logger.warning('not enough items to sell')

        if msg['action'] == 'retract_statement':
            to_del = player.get_last_statement()
            if to_del:
                to_del.delete()

        spread = group.get_spread_html()
        for p in group.get_players():
            self.group_send(p.get_personal_channel_name(), {'asks': p.get_asks_html(),
                                                            'bids': p.get_bids_html()})

        self.group_send(group.get_channel_group_name(), {
            'spread': spread,
        })
        msg = dict()
        last_statement = player.get_last_statement()

        if last_statement:
            msg['last_statement'] = last_statement.as_dict()
        msg['form'] = player.get_form_html()
        self.send(msg)
