from channels.generic.websockets import JsonWebsocketConsumer
# we need to import our Player model to get and put some data there
from minimum.models import Player


class TaskTracker(JsonWebsocketConsumer):
    # this is the path that should correspond to the one we use in our javascript file
    # the 'player_id' keyword helps us to retrieve the corresponding player data from the database
    url_pattern = (r'^/tasktracker/(?P<player_id>[0-9]+)$')

    # the following 'receive' method is executed automatically by Channels when a message is received from a client
    def receive(self, text=None, bytes=None, **kwargs):
        # using the keyword we get the player
        p = Player.objects.get(id=self.kwargs['player_id'])
        # we receive the answer
        answer = text.get('answer')
        # if the answer is not empty....
        if answer:
            # ... then we increase the counter of total tasks attempted by 1
            p.num_tasks_total += 1
            # if the answer is correct...
            if int(answer) == p.last_correct_answer:
                # ... we increase the counter of correctly submitted tasks by 1
                p.num_tasks_correct += 1
            #  we create a new task
            p.create_task()
            # IMPORTANT: save the changes in the database
            p.save()
            # and send a new task with updated counters back to a user
            self.send({'task_body': p.task_body,
                       'num_tasks_correct': p.num_tasks_correct,
                       'num_tasks_total': p.num_tasks_total, })
