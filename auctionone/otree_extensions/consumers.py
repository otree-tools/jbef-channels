from channels.generic.websockets import JsonWebsocketConsumer

# we need to import our Player model to get and put some data there
from auctionone.models import Player, Group, JobContract, Constants
import ast

class AuctionTracker(JsonWebsocketConsumer):

    url_pattern = r'^/auction_channel/(?P<player_pk>[0-9]+)/(?P<group_pk>[0-9]+)$'

    def clean_kwargs(self):
        self.player_pk = self.kwargs['player_pk']
        self.group_pk = self.kwargs['group_pk']

    def connect(self, message, **kwargs):
        print('someone connected')

    def disconnect(self, message, **kwargs):
        print('someone disconnected')

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

    def get_contracts(self, group):
        contracts = {}
        active_contracts = list(
            JobContract.objects.filter(accepted=False, employer__group=group).values('pk', 'amount'))
        closed_contracts = list(
            JobContract.objects.filter(accepted=True, employer__group=group).values('id', 'employer_id', 'worker_id',
                                                                                    'amount', 'accepted',
                                                                                    'amount_updated', 'tasks_corr',
                                                                                    'tasks_att'))
        contracts['active_contracts'] = active_contracts
        contracts['closed_contracts'] = closed_contracts
        group.contracts_dump = str(contracts)
        group.save()
        return contracts

    def receive(self, text=None, bytes=None, **kwargs):
        self.clean_kwargs()
        msg = text
        group = self.get_group()
        role = msg['role']
        print(msg)
        if role == "employer":
            employer = Player.objects.get(pk=msg['player_pk'])
            wage_offer = msg['wage_offer']
            employer.offers.create(amount=wage_offer)
            contract, created = employer.contract.get_or_create(defaults={'amount': wage_offer, 'accepted': False, })
            if created:
                print("offer created")
                group.last_message = str("Nuova offerta salariale di " + str(wage_offer) + ".")
            if not created:
                group.last_message = str(
                    "Un'offerta precedentemente di " + str(contract.amount) + " è ora di " + str(wage_offer) + ".")
            group.save()
            contract.amount = wage_offer
            contract.save()
        else:
            print('worker accepting')
            response = {}
            worker = Player.objects.get(pk=msg['player_pk'])
            # check no offers accepted
            accepted_contracts = JobContract.objects.filter(accepted=True, employer__group=group, worker=worker).count()
            if accepted_contracts == 0:
                contract = JobContract.objects.get(pk=msg['contract_to_accept'])
                wage_accepted = msg['wage_accepted']
                # check the offer is valid
                if contract.accepted:
                    # if not, check if there are alternative contracts with the identical wage offer
                    alternative_contracts = list(
                        JobContract.objects.filter(accepted=False, employer__group=group, amount=wage_accepted).values(
                            'pk', 'amount'))
                    if len(alternative_contracts) == 0:
                        # if no alternatives, send info that the offer is taken
                        response['already_taken'] = True
                        response['last_message'] = False
                        group.last_message = False
                        group.save()
                    else:
                        # accept the first alternative contract
                        contract_key = alternative_contracts[0]['pk']
                        contract = JobContract.objects.get(pk=contract_key)
                        contract.worker = worker
                        contract.accepted = True
                        contract.save()
                        response['already_taken'] = False
                        group.last_message = str("È stata accettata un offerta di " + wage_accepted + ".")
                        group.save()
                        worker.matched = 1
                        worker.save()
                        employer = Player.objects.get(pk=contract.employer_id)
                        employer.matched = 1
                        employer.wage_offer = contract.amount
                        employer.save()

                elif int(wage_accepted) != contract.amount:
                    # the contract has been updated to a different amount
                    response['already_taken'] = True
                    response['last_message'] = False
                else:
                    # the initial contract is to be accepted
                    contract.worker = worker
                    contract.accepted = True
                    contract.save()
                    group.last_message = str("È stata accettata un offerta di " + wage_accepted + ".")
                    group.save()
                    worker.matched = 1
                    worker.save()
                    employer = Player.objects.get(pk=contract.employer_id)
                    employer.matched = 1
                    employer.wage_offer = contract.amount
                    employer.save()
                    response['already_taken'] = False
                self.send({'text': response})
        textforgroup = self.get_contracts(group)
        print("textforgroup", textforgroup)
        closed_contracts_num = JobContract.objects.filter(accepted=True, employer__group=group).count()
        group.num_contracts_closed = closed_contracts_num
        group.save()
        print("number of closed contracts", closed_contracts_num)
        if closed_contracts_num >= Constants.num_employers:
            group.day_over = True
            group.save()
        self.group_send(group.get_channel_group_name(), {'active_contracts': textforgroup['active_contracts'],
                                                         'closed_contracts': textforgroup['closed_contracts'],
                                                         'day_over': group.day_over,
                                                         'last_message': group.last_message,
                                                         'contracts_closed': group.num_contracts_closed,})


class MatrixTracker(JsonWebsocketConsumer):
    # For the real effort task
    url_pattern = r'^/matrixtracker/(?P<player_id>[0-9]+)$'

    def clean_kwargs(self):
        self.player_pk = self.kwargs['player_pk']

    def connect(self, message, **kwargs):
        print('someone connected')
        # when player (re)connects, send the (old) task
        p = Player.objects.get(id=self.kwargs['player_id'])
        if p.tasks_attempted < Constants.max_task_amount:
            mat1 = ast.literal_eval(p.mat1)
            mat2 = ast.literal_eval(p.mat2)
            self.send({'mat1': mat1,
                       'mat2': mat2,
                       'tasks_correct': p.tasks_correct,
                       'tasks_attempted': p.tasks_attempted,
                       })

    def disconnect(self, message, **kwargs):
        print('someone disconnected')

    def receive(self, text=None, bytes=None, **kwargs):
        p = Player.objects.get(id=self.kwargs['player_id'])
        answer = text.get('answer')
        if answer:
            p.tasks_attempted += 1
            if int(answer) == p.last_correct_answer:
                p.tasks_correct += 1
                feedback = "La precedente risposta era corretta."
            else:
                feedback = "La precedente risposta " + str(answer) + " era sbagliata, la risposta corretta era " + str(
                    p.last_correct_answer) + "."
            new_task = p.get_task()
            p.save()
            print(new_task)
            if p.role() == 'worker':
                if p.tasks_attempted < Constants.max_task_amount:
                    self.send({'mat1': new_task['mat1'],
                               'mat2': new_task['mat2'],
                               'tasks_correct': p.tasks_correct,
                               'tasks_attempted': p.tasks_attempted,
                               'feedback': feedback
                               })
                else:
                    new_task['task_over'] = True
                    self.send({'task_over': new_task['task_over']})
            else:
                self.send({'mat1': new_task['mat1'],
                           'mat2': new_task['mat2'],
                           'tasks_correct': p.tasks_correct,
                           'tasks_attempted': p.tasks_attempted,
                           'feedback': feedback
                           })