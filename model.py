import scipy.integrate
from scipy import optimize

import math
import json


class TaskModel():
    def __init__(self, id, today, due, work, week_day_work, week_end_work=0, days=0, gradient='+'):
        self.id = f't{id}'
        self.due_date = due
        self.k = work
        self.h = week_day_work
        self.gradient = gradient
        self.today = today

        # if the task is big, more than 10 hours of work
        if self.k > 10:
            # get c value with least final day area
            self.c = optimize.root_scalar(                  # c is the flexibility variable
                self.c_for_huge, bracket=[0, 3], method='brentq').root       # TODO fix the bracket

        # if the task is small, less than or equal 10 hours of work
        elif self.k <= 10:
            # no of days needed is estimated to H / H**(1/3)
            # this will make sure that the final gradient is around 1
            self.c = (3*self.k**(1/3)-1)/3
            self.h = self.c + 1         # TODO when this h is more than min threshold
        # TODO work on c which can be customized according to users no of day

        # duration
        self.n = 3*self.k/(self.h+2*self.c)

        # the start date of the task
        # d0 = D-n
        self.start_day = self.due_date-self.n

        # if the initial date is less than 0
        if self.start_day < today:           # TODO make this today by getting a relative time for due date
            # c gets re-evaluate according to condition
            self.h = week_day_work
            self.c = (3*self.k/(self.due_date-today) - self.h)/2
            # set duration as days to due
            self.n = self.due_date - today
            # start date is made 0, current date
            self.start_day = today
        # if user requires a no of days and its NOT less than min
        elif days != 0 and self.due_date - today + days > 0:
            # TODO make sure this works
            self.c = (3*self.k/(days + today) - self.h)/2
            self.start_day = self.due_date - (days + today)

        # TODO flip according to limitation
        if (gradient == '-' and self.k/(self.due_date - today) < self.h) or (gradient == '+' and self.k/(self.due_date - today) > self.h):
            self.h = self.c
            self.c = (3*self.k/self.n - self.h)/2

        if gradient == '0':
            self.n = days if days != 0 else self.k / \
                self.k**(1/3) if self.k/self.k**(1/3) < self.due_date - \
                today else self.due_date - today
            self.c = self.k/self.n
            self.h = self.c
            self.start_day = self.due_date-self.n

        # total area, for checking
        total_area = scipy.integrate.quad(
            self.model, self.start_day, self.due_date)[0]

        print('n: ', self.n)
        print('c: ', self.c, 'h: ', self.h)
        print('total area: ', round(total_area, 4))

        # self.generate_list()

    # used to find min area for final day. Used only for default (large) tasks
    def c_for_huge(self, x):
        return (-8*x**3 - 4*self.h*x**2 + 16*self.k*x**2 + 2*self.h**2*x - 6*self.k **
                2*x + 4*self.h*self.k*x + self.h**3 - 3*self.h*self.k**2 - 2*self.h**2*self.k)/(3*self.k**2*(2*x+self.h))+1

    def model(self, x):
        return (self.h - self.c)/(3*self.k/(self.h+2*self.c))**2 * (x-self.due_date + 3*self.k/(self.h+2*self.c))**2 + self.c

    def generate_list(self):
        task_days = []

        def area(start, end): return scipy.integrate.quad(
            self.model, start, end)[0]

        task_days.append(((math.floor(self.start_day)),
                          area(self.start_day, math.ceil(self.start_day))))

        for n in range(math.floor(self.start_day)+1, self.due_date):
            task_days.append((n, area(n, n+1)))

        return task_days
