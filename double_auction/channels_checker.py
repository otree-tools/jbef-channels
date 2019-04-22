from otree.views.abstract import channels
from termcolor import colored

def cp(*x, color='red'):
    x = ' '.join([str(i) for i in x])
    return (colored(x, color, attrs=['bold']))


channel_ver = int(channels.__version__.split('.')[0])
if channel_ver > 0:
    raise Exception(cp('This code is not compatible with a new version of Django Channels.\n'
                       'Please update the code via https://github.com/otree-tools/jbef-channels/'))
