from datetime import datetime
import json
from json.decoder import JSONDecodeError
import math

from model import TaskModel
from helpers import getDateDelta
from filter import Filter

D0 = datetime(2000, 1, 1)


def dummy_start():
    n = new_id()
    task_cumulation = {}
    name = input(f'Task No. {n} Name (blank to cancel): ')

    while name != "":
        d = getDateDelta(input('Due date (yyyy-mm-dd): '))
        w = int(input('Hrs of work: '))
        g = input('Gradient (+/-/0): ')

        # assumed no work can be done on the day of creation
        task = TaskModel(id=n, due=d, work=w,
                         week_day_work=6, days=0, gradient=g, today=getDateDelta(datetime.now()) + 1)
        task_cumulation[(n, name, d)] = task

        n = n+1
        name = input(f'Task No. {n} Name (blank to cancel): ')

    Filter(task_cumulation)


def new_id():
    # produces new id after reading the used ids from file
    with open('tasks.json') as tasks_json:
        try:
            tasks = json.load(tasks_json)
            nos = sorted([int(id.strip('t'))
                          for id in tasks.keys()], reverse=True)
            if float(nos[0]).is_integer():
                return int(nos[0]) + 1
            else:
                return math.ceil(float(nos[0]))
        except JSONDecodeError:
            # print(1)
            return 1


if __name__ == "__main__":
    dummy_start()
