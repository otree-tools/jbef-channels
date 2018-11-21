from channels.generic.websockets import JsonWebsocketConsumer
from realefforttask.models import Player, Task
import json


class TaskTracker(JsonWebsocketConsumer):
    url_pattern = (
        r'^/RETtasktracker/(?P<player_id>[0-9]+)$')

    def get_player(self):
        self.player_id = self.kwargs['player_id']
        return Player.objects.get(id=self.player_id)

    def receive(self, text=None, bytes=None, **kwargs):
        player = self.get_player()
        answer = text.get('answer')
        print('AAAAA', answer)
        if answer:
            old_task = player.get_or_create_task()
            old_task.answer = answer
            old_task.save()
            new_task = player.get_or_create_task()
            self.send({'task_body': new_task.html_body,
                       'num_tasks_correct': player.num_tasks_correct,
                       'num_tasks_total': player.num_tasks_total,
                       })
