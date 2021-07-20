from datetime import datetime
import json
from json.decoder import JSONDecodeError
import math

# from sympy.solvers import solve
# from sympy import Symbol, N, integrate, expand


from model import TaskModel
# from reposition import Reposition
from helpers import getDateDelta
from filter import Filter

D0 = datetime(2000, 1, 1)


def dummy_start():
    n = new_id()
    task_cumulation = {}
    name = input(f'Task No. {n} Name (blank to cancel): ')

    while name != "":
        d = getDateDelta(input('Due date (yyyy-mm-dd):'))
        w = int(input('Hrs of work: '))
        g = input('Gradient (+/-/0): ')

        # assumed no work can be done on the day of creation
        task = TaskModel(id=n, due=d, work=w,
                         week_day_work=6, days=0, gradient=g, today=getDateDelta(datetime.now()) + 1)
        task_cumulation[(n, name, d)] = task

        n = n+1
        name = input(f'Task No. {n} Name (blank to cancel): ')

    # a = Reposition(task_cumulation, 6, 10)
    a = Filter(task_cumulation)


def new_id():
    with open('tasks.json') as tasks_json:
        try:
            tasks = json.load(tasks_json)
            nos = sorted([int(id.strip('t'))
                          for id in tasks.keys()], reverse=True)
            if float(nos[0]).is_integer():
                # print(int(nos[0]) + 1, nos)
                return int(nos[0]) + 1
            else:
                # print(math.ceil(float(nos[0])))
                return math.ceil(float(nos[0]))
        except JSONDecodeError:
            # print(1)
            return 1


if __name__ == "__main__":
    # d = int(input('Days to due: '))
    # w = int(input('Hrs of work: '))
    # task = TaskModel(due=d, work=w, week_day_work=6, days=0, gradient='0')
    # print(task.generate_list())
    dummy_start()
    # new_id()
    # TaskGenerator()
