from channels.generic.websockets import JsonWebsocketConsumer
from realefforttask.models import Player, Task
import json


# TODO: delete fol lines

# from realefforttask.forms import ChooseTaskForm
# from django.template.loader import render_to_string


class TaskTracker(JsonWebsocketConsumer):
    url_pattern = (
        r'^/tasktracker' +
        '/participant/(?P<participant_code>[a-zA-Z0-9_-]+)' +
        '/player/(?P<player_id>[0-9]+)' +
        '$')

    def clean_kwargs(self, kwargs):
        self.player_id = self.kwargs['player_id']
        self.participant_code = self.kwargs['participant_code']
        self.player = self.get_player()

    def get_player(self):
        return Player.objects.get(participant__code__exact=self.participant_code, pk=self.player_id)

    def receive(self, text=None, bytes=None, **kwargs):
        player = Player.objects.get(pk=self.kwargs['player'])
        if text.get('answer'):
            player.num_tasks_total += 1
            if text.get('answer') == player.get_correct_answer():
                player.num_tasks_correct += 1
            player.task_body = player.create_task()
            player.save()
            self.send({'task_body': player.task_body,
                       'num_tasks_correct': player.num_tasks_correct,
                       'num_tasks_total': player.num_tasks_total, })

    def connect(self, message, **kwargs):
        self.clean_kwargs(kwargs)
