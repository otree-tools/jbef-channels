from channels.generic.websocket import JsonWebsocketConsumer
from realefforttask.models import Player
from otree.models import Participant
from otree.models_concrete import ParticipantToPlayerLookup
import logging

logger = logging.getLogger(__name__)


class TaskTracker(JsonWebsocketConsumer):
    url_pattern = r'^RETtasktracker/(?P<participant_code>.+)$'

    def set_vars(self):
        participant = Participant.objects.get(code__exact=self.participant_id)
        cur_page_index = participant._index_in_pages
        lookup = ParticipantToPlayerLookup.objects.get(participant=participant, page_index=cur_page_index)
        player_pk = lookup.player_pk
        self.player = Player.objects.get(id=player_pk)

    def receive_json(self, content, **kwargs):
        answer = content.get('answer')
        if answer:
            old_task = self.player.get_or_create_task()
            old_task.answer = answer
            old_task.save()
            new_task = self.player.get_or_create_task()
            self.send_json({'task_body': new_task.html_body,
                            'num_tasks_correct': self.player.num_tasks_correct,
                            'num_tasks_total': self.player.num_tasks_total,
                            })

    def connect(self):
        self.participant_id = self.scope['url_route']['kwargs']['participant_code']
        self.set_vars()
        self.accept()
        logger.info(f'Connected: {self.participant_id}')
