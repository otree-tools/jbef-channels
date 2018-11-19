from channels.generic.websockets import JsonWebsocketConsumer
from decoding_app.models import Constants, Player


class TaskTracker(JsonWebsocketConsumer):
    url_pattern = (r'^/tasktracker/(?P<player_pk>[0-9]+)$')

    def clean_kwargs(self):
        self.player_pk = self.kwargs['player_pk']


    def get_player(self):
        self.clean_kwargs()
        return Player.objects.get(pk=self.player_pk)

    def prepare_task(self, player, task):
        return {'task': task.as_dict(),
                'num_correct': player.num_correct,
                }

    def connect(self, message, **kwargs):
        player = self.get_player()
        unanswered_tasks = player.get_unfinished_tasks()
        if unanswered_tasks.exists():
            task = unanswered_tasks.first()
        else:
            task = player.tasks.create()
        response = self.prepare_task(player, task)
        self.send(response)

    def receive(self, text=None, bytes=None, **kwargs):
        player = self.get_player()
        oldtask = player.get_unfinished_tasks().first()
        oldtask.answer = text
        oldtask.is_correct = text == ''.join(oldtask.correct_answer)
        oldtask.save()
        newtask = task = player.tasks.create()
        response = self.prepare_task(player, newtask)
        player.save()
        self.send(response)
