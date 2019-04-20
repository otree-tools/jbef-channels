from channels.generic.websockets import JsonWebsocketConsumer
from realefforttask.models import Player
from otree.models import Participant
from otree.models_concrete import ParticipantToPlayerLookup
import logging

logger = logging.getLogger(__name__)


class TaskTracker(JsonWebsocketConsumer):
    url_pattern = r'^/RETtasktracker/(?P<participant_code>.+)$'

    def clean_kwargs(self):
        participant = Participant.objects.get(code__exact=self.kwargs['participant_code'])
        cur_page_index = participant._index_in_pages
        lookup = ParticipantToPlayerLookup.objects.get(participant=participant, page_index=cur_page_index)
        self.player_pk = lookup.player_pk

    def get_player(self):
        self.clean_kwargs()
        return Player.objects.get(id=self.player_pk)

    def receive(self, text=None, bytes=None, **kwargs):
        player = self.get_player()
        answer = text.get('answer')
        if answer:
            old_task = player.get_or_create_task()
            old_task.answer = answer
            old_task.save()
            new_task = player.get_or_create_task()
            self.send({'task_body': new_task.html_body,
                       'num_tasks_correct': player.num_tasks_correct,
                       'num_tasks_total': player.num_tasks_total,
                       })

    def connect(self, message, **kwargs):
        logger.info(f'Connected: {self.kwargs["participant_code"]}')
