import json
from channels import Group as ChannelGroup


class NotEnoughFunds(Exception):
    def __init__(self, owner):
        channel = ChannelGroup(owner.get_personal_channel_name())
        channel.send({'text': json.dumps({'warning': 'You do not have enough funds to make this bid. Retract previous bids'
                                                     ' or change the amount.'})})
        super().__init__('Not enough money to create a new bid of this amount')


class NotEnoughItemsToSell(Exception):
    def __init__(self, owner):
        channel = ChannelGroup(owner.get_personal_channel_name())
        channel.send({'text': json.dumps({'warning': 'You do not have not enough items to make this ask. Retract previous asks'
                                                     })})
        super().__init__('Not enough items to sell')
