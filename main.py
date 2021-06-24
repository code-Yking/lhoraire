from datetime import datetime
import json

# from sympy.solvers import solve
# from sympy import Symbol, N, integrate, expand

import scipy.integrate
from scipy import optimize

import math

D0 = datetime(2000, 1, 1)


class start():
    def __init__(self):

        d_today = datetime.now()

        deltaTime = d_today - D0
        self.delta = deltaTime.days
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
                'due': str(datetime.fromisoformat(input('Due: '))),
                'hours_needed': int(input('Hours Needed: '))
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
            due_date = datetime.fromisoformat((n['due']))
            work_start_delta = (due_date - D0).days
            # if (due_date - datetime.now()).days > 0 and (due_date - datetime.now()).days <= n['hours_needed']:
            #     work_start_delta = (due_date - D0).days - n['hours_needed']
            print(work_start_delta)

            TaskModel(due=12, work=10, week_day_work=6)


class TaskModel():
    def __init__(self, due, work, week_day_work, week_end_work=0, days=0):
        self.due = due
        self.k = work
        self.h = week_day_work

        if self.k > 10:
            # get c value with least final day area
            self.c = optimize.root_scalar(                  # c is the flexibility variable
                self.for_c, bracket=[0, 3], method='brentq').root       # todo fix the bracket

        # todo work on c which can be customized according to users no of day

        # duration
        self.n = 3*self.k/(self.h+2*self.c)

        # the start date of the task
        # d0 = D-n
        self.start_day = self.due-self.n
        print('n: ', self.n)
        # if the initial date is less than 0
        if self.start_day < 0:           # todo make this today
            # c gets re-evaluate according to condition
            self.c = (3*self.k/self.due - self.h)/2
            self.start_day = 0                               # start date is made 0
        elif days != 0:
            self.c = (3*self.k/days - self.h)/2
            self.start_day = self.due-days

        # total area, for checking
        total_area = scipy.integrate.quad(
            self.model, self.start_day, self.due)[0]

        print('c: ', self.c)
        print('area: ', round(total_area, 4))

        self.generate_list()

    def for_c(self, x):                     # used to find min area for final day. Used only for default
        return (-8*x**3 - 4*self.h*x**2 + 16*self.k*x**2 + 2*self.h**2*x - 6*self.k **
                2*x + 4*self.h*self.k*x + self.h**3 - 3*self.h*self.k**2 - 2*self.h**2*self.k)/(3*self.k**2*(2*x+self.h))+1

    def model(self, x):
        return (self.h - self.c)/(3*self.k/(self.h+2*self.c))**2 * (x-self.due + 3*self.k/(self.h+2*self.c))**2 + self.c

    def generate_list(self):
        self.task_days = []

        def area(start, end): return scipy.integrate.quad(
            self.model, start, end)[0]

        if not float(self.start_day).is_integer():
            self.task_days.append(((math.ceil(self.start_day)),
                                   area(self.start_day, math.ceil(self.start_day))))

        for n in range(math.ceil(self.start_day), self.due):
            # print(f'Day {n+1}: ', area(n, n+1))
            self.task_days.append((n+1, area(n, n+1)))


if __name__ == "__main__":
    d = int(input('Days to due: '))
    w = int(input('Hrs of work: '))
    task = TaskModel(due=d, work=w, week_day_work=6, days=0)
    print(task.task_days)
