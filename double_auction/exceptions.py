class NotEnoughFunds(Exception):
    def __init__(self):
        super().__init__('Not enough money to create a new bid of this amount')

class NotEnoughItemsToSell(Exception):
    def __init__(self):
        super().__init__('Not enough items to sell')
