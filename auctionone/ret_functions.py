# this is the module responsible for generation functions for different rets
# if you need new rets you need to define generating functions here and attach them to corresponding tasks

from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
import random
import json
from random import randint
from string import digits, ascii_lowercase


# function slices a list with n elements in each sublist (if possible)
def slicelist(l, n):
    return [l[i:i + n] for i in range(0, len(l), n)]


# slices a list into n parts  of an equal size (if possible)
def chunkify(lst, n):
    return [lst[i::n] for i in range(n)]


def get_random_list(max_len):
    low_upper_bound = 50
    high_upper_bound = 99
    return [randint(10, randint(low_upper_bound, high_upper_bound)) for i in range(max_len)]


class TaskGenerator:
    path_to_render = None

    def __init__(self, **kwargs):
        self.body = self.get_body(**kwargs)
        self.correct_answer = self.get_correct_answer()
        self.html_body = self.get_html_body()
        print('DEBUG - CORRECT ANSWER', self.correct_answer)

    def get_context_for_body(self):
        return {}

    def get_html_body(self):
        return mark_safe(render_to_string(self.path_to_render, self.get_context_for_body()))

    def get_body(self, **kwargs):
        pass

    def get_correct_answer(self):
        pass


class TwoMatrices(TaskGenerator):
    path_to_render = 'auctionone/components/twomatrices.html'

    def get_correct_answer(self):
        return max(self.listx) + max(self.listy)

    def get_body(self, **kwargs):
        diff = kwargs.get('difficulty', 10)
        self.listx = get_random_list(diff ** 2)
        self.listy = get_random_list(diff ** 2)

        _listx = slicelist(self.listx, diff)
        _listy = slicelist(self.listy, diff)
        return {'listx': _listx, 'listy': _listy}

    def get_context_for_body(self):
        return {
            "mat1": self.body['listx'],
            "mat2": self.body['listy'],
            "correct_answer": self.correct_answer,
        }

