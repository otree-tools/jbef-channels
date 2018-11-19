from channels.generic.websockets import JsonWebsocketConsumer
import random
from negotiations.models import Constants, Player, Group
import json


class OfferTracker(JsonWebsocketConsumer):
    url_pattern = (r'^/offer_channel/(?P<player_pk>[0-9]+)/(?P<group_pk>[0-9]+)$')

    def clean_kwargs(self):
        self.player_pk = self.kwargs['player_pk']
        self.group_pk = self.kwargs['group_pk']

    def connection_groups(self, **kwargs):
        group_name = self.get_group().get_channel_group_name()
        return [group_name]

    def connect(self, message, **kwargs):
        print('someone connected')

    def disconnect(self, message, **kwargs):
        print('someone disconnected')

    def get_player(self):
        self.clean_kwargs()
        return Player.objects.get(pk=self.player_pk)

    def get_group(self):
        self.clean_kwargs()
        return Group.objects.get(pk=self.group_pk)

    def receive(self, text=None, bytes=None, **kwargs):
        self.clean_kwargs()
        msg = text
        sender = self.get_player()
        group = self.get_group()
        receiver = sender.get_another()

        if msg['type'] == 'offer':
            offer = int(msg['amount'])
            offer = group.offers.create(sender=sender, receiver=receiver, amount=offer, accept=False)
            self.group_send(group.get_channel_group_name(), offer.as_dict())
            return
        if msg['type'] == 'accept':
            accepted_offer = group.offers.filter(sender=receiver, receiver=sender).latest('created_at')
            accepted_offer.accept = True
            accepted_offer.save()

            self.group_send(group.get_channel_group_name(), {'accept': True})


class TaskTracker(JsonWebsocketConsumer):
    url_pattern = (r'^/tasktracker/(?P<player_pk>[0-9]+)/(?P<task_type>[0-9]+)$')

    def clean_kwargs(self):
        self.player_pk = self.kwargs['player_pk']
        self.task_type = int(self.kwargs['task_type'])

    def get_player(self):
        self.clean_kwargs()
        return Player.objects.get(pk=self.player_pk)

    def prepare_task(self, player, task):
        return {'task': task.as_dict(),
                'num_correct': player.num_correct,
                'num_incorrect': player.num_incorrect,
                }

    def connect(self, message, **kwargs):
        player = self.get_player()
        unanswered_tasks = player.tasks.filter(answer__isnull=True)
        if unanswered_tasks.exists():
            task = unanswered_tasks.first()
        else:
            task = player.tasks.create(task_type=self.task_type)
        response = self.prepare_task(player, task)
        self.send(response)

    def receive(self, text=None, bytes=None, **kwargs):
        player = self.get_player()
        oldtask = player.tasks.filter(answer__isnull=True).first()
        oldtask.answer = text
        oldtask.save()
        player.num_answered += 1
        if text == oldtask.correct_answer:
            player.num_correct += 1
        else:
            player.num_incorrect += 1
        newtask = player.tasks.create(task_type=self.task_type)
        response = self.prepare_task(player, newtask)
        player.save()
        self.send(response)
