from channels.generic.websockets import JsonWebsocketConsumer
# we need to import our models to get and put some data there
from auctionone.models import Player, Group, JobOffer, Constants


class AuctionTracker(JsonWebsocketConsumer):
    url_pattern = r'^/auction_channel/(?P<player_pk>[0-9]+)/(?P<group_pk>[0-9]+)$'

    def clean_kwargs(self):
        self.player_pk = self.kwargs['player_pk']
        self.group_pk = self.kwargs['group_pk']

    def connection_groups(self, **kwargs):
        group_name = self.get_group().get_channel_group_name()
        personal_channel = self.get_player().get_personal_channel_name()
        return [group_name, personal_channel]

    def get_group(self):
        self.clean_kwargs()
        return Group.objects.get(pk=self.group_pk)

    def get_player(self):
        self.clean_kwargs()
        return Player.objects.get(pk=self.player_pk)

    def receive(self, text=None, bytes=None, **kwargs):
        self.clean_kwargs()
        player = self.get_player()
        if text.get('offer_made') and player.role() == 'employer':
            wage_offer = text['wage_offer']
            open_offers = player.offer_made.filter(worker__isnull=True)
            if open_offers.exists():
                recent_offer = open_offers.first()
                recent_offer.amount = wage_offer
                recent_offer.save()
            else:
                player.offer_made.create(amount=wage_offer, group=player.group)

        if text.get('offer_accepted') and player.role() == 'worker':
            offer_id = text['offer_id']
            try:
                offer = JobOffer.objects.get(id=offer_id, worker__isnull=True)
                offer.worker = player
                offer.save()
            except JobOffer.DoesNotExist:
                return



class TaskTracker(JsonWebsocketConsumer):
    url_pattern = (
        r'^/auction_one_tasktracker/(?P<player_id>[0-9]+)$')

    def get_player(self):
        self.player_id = self.kwargs['player_id']
        return Player.objects.get(id=self.player_id)

    def receive(self, text=None, bytes=None, **kwargs):
        player = self.get_player()
        answer = text.get('answer')
        if answer:
            old_task = player.get_or_create_task()
            old_task.answer = answer
            old_task.save()
            if old_task.answer == old_task.correct_answer:
                feedback = "Your answer was correct."
            else:
                feedback = "Your previous answer " + old_task.answer + " was wrong, the correct answer was " + \
                           old_task.correct_answer + "."
            new_task = player.get_or_create_task()
            self.send({'task_body': new_task.html_body,
                       'num_tasks_correct': player.num_tasks_correct,
                       'num_tasks_total': player.num_tasks_total,
                       'feedback': feedback,
                       })
