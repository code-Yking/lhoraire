from datetime import datetime
import json

# from sympy.solvers import solve
# from sympy import Symbol, N, integrate, expand


from model import TaskModel
from reposition import Reposition
from helpers import getDateDelta

D0 = datetime(2000, 1, 1)


class TaskGenerator():
    def __init__(self):

        d_today = datetime.now()        # today's date

        self.delta = getDateDelta(d_today)
        print("Now: ", self.delta)

        self.addition()

    def addition(self):
        self.task_list = []

        n = 1
        task = input(f'Task {n} (blank to cancel): ')

        while task != '':
            task_info = {
                'id': n,
                'details': task,
                'due': str(input('Due: ')),
                'hours_needed': int(input('Hours Needed: ')),
                'gradient': input('Gradient (+/-/0): ')
            }
            self.task_list.append(task_info)
            n = n+1
            print(task_info)

            task = input(f'Task {n} (blank to cancel): ')

        self.save()
        self.work_to_do()

    def save(self):
        if self.task_list != []:
            # with open('data.json', 'r') as json_file:
            #     data = json.load(json_file)
            with open('data.json', 'w') as outfile:
                json.dump(self.task_list, outfile)

    def work_to_do(self):
        self.dates = {}

        with open('data.json') as json_file:
            data = json.load(json_file)

        for n in data:
            due_date = getDateDelta(n['due'])
            # if (due_date - datetime.now()).days > 0 and (due_date - datetime.now()).days <= n['hours_needed']:
            #     work_start_delta = (due_date - D0).days - n['hours_needed']
            print(due_date)

            # TaskModel(due=12, work=10, week_day_work=6)


def dummy_start():
    n = 1
    task_cumulation = {}
    name = input(f'Task No. {n} Name (blank to cancel): ')

    while name != "":
        d = getDateDelta(input('Due date: '))
        w = int(input('Hrs of work: '))
        g = input('Gradient (+/-/0): ')

        # assumed no work can be done on the day of creation
        task = TaskModel(id=n, due=d, work=w,
                         week_day_work=6, days=0, gradient=g, today=getDateDelta(datetime.now()) + 1)
        task_cumulation[(n, name, d)] = task

        n = n+1
        name = input(f'Task No. {n} Name (blank to cancel): ')

    a = Reposition(task_cumulation, 6, 10)


if __name__ == "__main__":
    # d = int(input('Days to due: '))
    # w = int(input('Hrs of work: '))
    # task = TaskModel(due=d, work=w, week_day_work=6, days=0, gradient='0')
    # print(task.generate_list())
    dummy_start()
    # TaskGenerator()
