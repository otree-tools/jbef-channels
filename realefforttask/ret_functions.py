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


# Shared properties for the tasks collected under the TaskGenerator Class
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
    path_to_render = 'realefforttask/ret_modules/twomatrices.html'

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


class SumNumbers(TaskGenerator):
    path_to_render = 'realefforttask/ret_modules/sumnumbers.html'
    digits_range = (10, 99)

    def get_correct_answer(self):
        return sum(self.numbers)

    def get_body(self, **kwargs):
        num_digits = kwargs.get('num_digits', 2)
        self.digits_range = kwargs.get('digits_range', self.digits_range)
        self.numbers = [random.randint(*self.digits_range) for _ in range(num_digits)]
        return {'numbers': self.numbers}

    def get_context_for_body(self):
        return {"numbers": self.numbers, }


class CountZeroes(TaskGenerator):
    path_to_render = 'realefforttask/ret_modules/countzeroes.html'

    def get_correct_answer(self):
        return self.data.count(str(self.value_to_count))

    def get_body(self, **kwargs):
        num_rows = kwargs.get('num_rows', 10)
        num_columns = kwargs.get('num_columns', 10)
        selection_set = kwargs.get('selection_set', [0, 1])
        self.value_to_count = kwargs.get('value_to_count', 0)
        nxm = num_rows * num_columns
        self.data = [str(random.choice(selection_set)) for _ in range(nxm)]
        self.mat = chunkify(self.data, num_rows)
        return {'mat': self.mat}

    def get_context_for_body(self):
        return {
            "mat": self.mat,
            "value_to_count": self.value_to_count,
        }


class Decoding(TaskGenerator):
    path_to_render = 'realefforttask/ret_modules/decoding.html'

    def get_correct_answer(self):
        correct_answer = ''.join([self.task_dict[i] for i in self.question])
        return correct_answer

    def get_body(self, **kwargs):
        dict_length = kwargs.get('dict_length', 5)
        task_len = kwargs.get('task_len', 5)
        digs = list(digits)
        random.shuffle(digs)
        lts = random.sample(ascii_lowercase, k=dict_length)
        self.task_dict = dict(zip(digs, lts))
        self.question = random.choices(digits, k=task_len)

        return {
            'question': self.question,
            'task_dict': self.task_dict,
        }

    def get_context_for_body(self):
        return {
            'question': self.question,
            'task_dict': self.task_dict,
        }
