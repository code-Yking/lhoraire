from datetime import datetime
import json
import math
from model import TaskModel
import pprint
from helpers import getDateDelta, getDatefromDelta, isWeekend
import operator


class Reposition:
    def __init__(self, tasks, normal_work, max_work):
        self.tasks = tasks
        self.week_day_work = normal_work[0]
        self.week_end_work = normal_work[1]

        self.max_week_day_work = max_work[0]
        self.max_week_end_work = max_work[1]

        self.day_scale = [[], [], [], []]
        self.to_reschedule = {}
        self.task_range = {}
        self.schedule = self.schedule_cumulation()

        self.process_data()
        # processed, day_freedom = self.process_data(self.schedule)
        # pprint.pprint(processed)
        # print(day_freedom)
        self.fix_difference()

    def schedule_cumulation(self):
        schedule_cumulation = {}

        for task_info, task_object in self.tasks.items():
            days = task_object.generate_list()

            task_id = f't{task_info[0]}'
            due_date = task_object.due_date

            for day in days:

                date_delta = day[0]
                date = day[0]
                # date = getDatefromDelta(date_delta)
                task_area = day[1]

                if date in schedule_cumulation:
                    schedule_cumulation[date]['quots'][task_id] = task_area
                    schedule_cumulation[date]['data']['days_to_due'][task_id] = due_date - date + 1
                else:
                    schedule_cumulation[date] = {
                        'quots': {
                            task_id: task_area
                        },
                        'data': {
                            'days_to_due': {
                                task_id: due_date - date_delta + 1
                            }
                        }
                    }

            start_date = math.ceil(task_object.start_day)
            self.task_range[task_id] = [start_date, due_date]
        return schedule_cumulation

    def process_data(self):
        # schedule_cumulation = cumulation

        yellow_days, orange_days, red_days = [], [], []

        for day, info in self.schedule.items():
            sum_of_area = 0

            for task_id, quote in info['quots'].items():
                sum_of_area = sum_of_area + quote

            # percent_of_work = {task_id: quote /
            #                    sum_of_area for task_id, quote in info['quots'].items()}

            info['data']['sum'] = sum_of_area
            info['data']['difference'] = self.week_day_work - sum_of_area
            # info['data']['percent_of_work'] = percent_of_work

            self.day_scale_append(day, sum_of_area, self.week_day_work)

    def day_scale_append(self, day, work_sum, total_hrs):
        day_scale = [[_day for _day in group if _day != day]
                     for group in self.day_scale]

        work_scale = work_sum/total_hrs
        if work_scale > 0.5 and work_scale < 0.75:
            day_scale[0].append(day)
        elif work_scale >= 0.75 and work_scale < 0.9:
            day_scale[1].append(day)
        elif work_scale > 0.9 and work_scale < 1:
            day_scale[2].append(day)
        elif work_scale >= 1:
            day_scale[3].append(day)

        # print(day)
        self.day_scale = day_scale

    def day_filling(self, tasks, surface=False):
        tasks_list = tasks

        for i, day_info in enumerate(tasks_list):          # for each weekend
            # the day delta number
            day = day_info[3]

            if day_info[2]:
                work_difference = self.week_end_work - self.week_day_work
                diff = self.week_end_work
            else:
                work_difference = 0
                diff = self.week_day_work

            # extra amount of hours that can be filled
            if day in self.schedule and not surface:
                diff = self.schedule[day]['data']['difference'] + \
                    work_difference
            elif day in self.schedule and surface:
                if day_info[2]:
                    diff = 1
                else:
                    diff = 0.5

            # task ids array
            tasks = day_info[1]

            # loop to put in the rescheduled tasks
            while diff > 0.1 and sum({k: self.to_reschedule[k] for k in self.to_reschedule.keys() & tasks}.values()) > 0.1:
                # days to due array
                dues = day_info[5]

                _diff = diff

                # Calculating the reciprocal `Proximity` Percentage
                # to decide how much hours (of the free) can be allocated to each reschedule task
                sum_reciprocals = 0

                for index, n in enumerate(dues):
                    # making sure the task needs to rescheduled
                    if tasks[index] not in self.to_reschedule.keys():
                        continue
                    sum_reciprocals = sum_reciprocals + 1/n

                for index, task in enumerate(tasks):
                    # making sure the task needs to rescheduled
                    if task not in self.to_reschedule.keys():
                        continue
                    days_to_due = dues[index]
                    # using `Proximity` Percentage to calculate the max available portion for that task
                    portion_available = (
                        (1 / days_to_due) / sum_reciprocals) * _diff

                    # print('due: ', dues[index], 'portion: ', portion_available)

                    reschedulable_portion = self.to_reschedule[task]

                    portion_used = 0

                    # more hours that are to be rescheduled than available in the weekend for that task
                    if portion_available < reschedulable_portion:
                        portion_used = portion_available
                        # to_reschedule property updated
                        self.to_reschedule[task] = reschedulable_portion - \
                            portion_available
                        diff = diff - portion_available

                        # weekend_tasks[i][0] = weekend_tasks[i][0] - 1
                        # weekend_tasks[i][1].remove(task)
                        # weekend_tasks[i][5].remove(dues)

                    elif portion_available >= reschedulable_portion:
                        portion_used = reschedulable_portion
                        diff = diff - reschedulable_portion
                        self.to_reschedule.pop(task)

                        tasks_list[i][0] = tasks_list[i][0] - 1
                        tasks_list[i][1].remove(task)
                        tasks_list[i][5].remove(days_to_due)

                    if day not in self.schedule.keys():
                        self.schedule[day] = {
                            'data': {'days_to_due': {}}, 'quots': {}}

                    self.schedule[day]['data']['sum'] = self.schedule[day]['data'].get(
                        'sum', 0) + portion_used
                    self.schedule[day]['data']['difference'] = diff

                    if task in self.schedule[day]['quots'].keys():
                        self.schedule[day]['quots'][task] = self.schedule[day]['quots'][task] + portion_used
                    else:
                        self.schedule[day]['quots'][task] = portion_used
                        print(dues)
                        self.schedule[day]['data']['days_to_due'][task] = days_to_due

                    self.day_scale_append(
                        day, self.schedule[day]['data']['sum'], self.week_end_work)

                print(diff)
                print('final', diff)
                print()
                print(day_info)
                print()
                pprint.pprint(self.schedule[day])
                print()
                pprint.pprint(self.to_reschedule)
                print()

    # PLAN:
    # cream off from week days, before or after according to gradient
    # not a problem if no of days get reduced as this is max days needed.

    def reschedulable_days(self):
        weekend_days, weekday_days = [], []

        for day, info in self.schedule.items():
            date = getDatefromDelta(day)
            is_weekend = isWeekend(date)

            no_tasks = 0
            tasks = []
            task_dues = []
            area = info['data']['sum']

            for task, day_range in self.task_range.items():
                # see if it is a weekend and the task needs to be reschedulable
                if int(day) in range(int(day_range[0]), int(day_range[1])+1) and task in self.to_reschedule.keys():
                    no_tasks = no_tasks + 1
                    tasks.append(task)
                    task_dues.append(int(day_range[1])-day+1)

            if is_weekend:
                weekend_days.append(
                    [no_tasks, tasks, is_weekend, day, area, task_dues])
            else:
                weekday_days.append([no_tasks, tasks, 0, day, area, task_dues])

        return weekday_days, weekend_days

    def precedence(self):
        precede_days = []
        precede_days_dict = {}

        for task, hours in self.to_reschedule.items():
            if self.task_range[task][0] == getDateDelta(datetime.now()) + 1:
                return []
            elif self.task_range[task][0] - 5 >= getDateDelta(datetime.now()) + 1:
                lower_date = self.task_range[task][0] - 5
            else:
                lower_date = getDateDelta(datetime.now()) + 1

            for n in range(lower_date, self.task_range[task][0]+1):
                precede_days_dict[n] = precede_days_dict.get(n, []) + [task]

        for date, tasks in precede_days_dict.items():
            precede_days.append([len(tasks), tasks, isWeekend(getDatefromDelta(date)), date, 0, [
                                self.task_range[t][1] - date for t in tasks]])

        for task in self.to_reschedule.keys():
            self.task_range[task][0] = lower_date

        # print(precede_days)
        return precede_days

    def fix_weekends(self):
        work_difference = self.week_end_work - self.week_day_work
        weekday_days, weekend_days = self.reschedulable_days()

        # priority is given to sort the weekend days,
        # so that more data is added first to the ones with less pressure
        # Priority no 1: No of tasks done during that weekend day. Lesser would be above
        # Priority no 2: Total number of hours worked during the weekend day. Lesser would be above
        # Priority no 3: Saturday or Sunday. Saturday is favored over sunday
        weekend_days.sort(key=operator.itemgetter(0, 4, 2))
        weekday_days.sort(key=operator.itemgetter(0, 4))

        # print('day scale', self.day_scale)

        # if more work can be done during weekends than weekdays
        if work_difference > 0:
            self.day_filling(weekend_days)
            self.day_filling(weekday_days)

        if work_difference < 0:

            for weekend in weekend_days:
                self.schedule[weekend[3]]['data']['difference'] = self.schedule[weekend[3]
                                                                                ]['data']['difference'] - abs(work_difference)
            self.to_reschedule = {k: self.basic_reschedule().get(
                k, 0) + self.to_reschedule.get(k, 0) for k in set(self.to_reschedule)}

        # print('day scale', self.day_scale)
        # print(weekday_days)

        while len(self.to_reschedule):
            # self.tail_tasks()
            extra_days = self.precedence()

            if not len(extra_days):

                while len(self.to_reschedule):
                    weekday_days, weekend_days = self.reschedulable_days()
                    # print(weekday_days)
                    weekend_days.sort(key=operator.itemgetter(3))
                    weekday_days.sort(key=operator.itemgetter(3))
                    self.day_filling(weekend_days, True)
                    self.day_filling(weekday_days, True)

                break
            extra_days.sort(key=operator.itemgetter(3), reverse=True)
            print(extra_days)
            self.day_filling(extra_days)

        pprint.pprint(self.schedule)
        pprint.pprint(self.to_reschedule)

    def tail_tasks(self):
        input()
        task_cumulation = {}
        for task, hours in self.to_reschedule.items():
            id = float(task.strip('t')) + 0.001
            d = self.task_range[task][0]
            task = TaskModel(id, due=d, work=hours,
                             week_day_work=6, days=0, today=getDateDelta(datetime.now()) + 1)
            task_cumulation[(id, f'tail for {task}', d)] = task

        # print(task_cumulation)
        from filter import Filter
        a = Filter(task_cumulation)

    def update_tasks(self, task, diff):
        with open('tasks.json') as json_file:
            data = json.load(json_file)

        info = data[task]
        info[0] = info[0] - diff

        with open('tasks.json', 'w') as outfile:
            json.dump(data, outfile)

    # PLAN:
    # Find difference where -ve,
    # use percent_of_dues and find which proportion of which to move out
    # use differences to find close days to relocate

    def fix_difference(self):
        self.to_reschedule = self.basic_reschedule()
        print(self.to_reschedule)
        self.fix_weekends()

    def basic_reschedule(self):
        to_reschedule = {}

        for day, info in self.schedule.items():
            diff = info['data']['difference']

            if diff >= 0:               # day is skipped if there is no difference
                pass
            else:
                i = 0               # to allow for small task hours which might not be able to provide
                while i < 2:
                    if info['data']['difference'] >= 0:
                        break
                    sum_of_dues = 0

                    for task_id, days_to_due in info['data']['days_to_due'].items():
                        sum_of_dues = sum_of_dues + days_to_due

                    portion_needed = {task: d/sum_of_dues * abs(info['data']['difference']) for task,
                                      d in info['data']['days_to_due'].items()}
                    # print(portion_needed)
                    for task_id in list(info['quots']):
                        quote = info["quots"][task_id]

                        if quote > portion_needed[task_id]:
                            info['quots'][task_id] = quote - \
                                portion_needed[task_id]

                            if task_id in to_reschedule.keys():
                                to_reschedule[task_id] = to_reschedule[task_id] + \
                                    portion_needed[task_id]
                            else:
                                to_reschedule[task_id] = portion_needed[task_id]

                            info['data']['difference'] = info['data']['difference'] + \
                                portion_needed[task_id]
                            info['data']['sum'] = info['data']['sum'] - \
                                portion_needed[task_id]

                        elif quote == portion_needed[task_id]:

                            if task_id in to_reschedule.keys():
                                to_reschedule[task_id] = to_reschedule[task_id] + \
                                    portion_needed[task_id]
                            else:
                                to_reschedule[task_id] = portion_needed[task_id]

                            info['quots'].pop(task_id)
                            info['data']['days_to_due'].pop(task_id)
                            info['data']['difference'] = info['data']['difference'] + \
                                portion_needed[task_id]
                            info['data']['sum'] = info['data']['sum'] - \
                                portion_needed[task_id]

                        elif quote < portion_needed[task_id]:

                            if task_id in to_reschedule.keys():
                                to_reschedule[task_id] = to_reschedule[task_id] + quote
                            else:
                                to_reschedule[task_id] = quote

                            info['data']['difference'] = info['data']['difference'] + quote
                            info['quots'].pop(task_id)
                            info['data']['days_to_due'].pop(task_id)
                            info['data']['sum'] = info['data']['sum'] - quote
                    i = i+1
                self.day_scale_append(
                    day, info['data']['sum'], self.week_day_work)

        # pprint.pprint(self.schedule)
        # print('to_reschedule: ', to_reschedule)
        return to_reschedule

        reschedule_table = {'G': {}, 'Y': {}, 'O': {}, 'R': {}}

        for task_id, reschedulable in to_reschedule.items():
            reschedule_table['G'][task_id] = reschedulable * 1/2
            reschedule_table['Y'][task_id] = reschedulable * 1/3
            reschedule_table['O'][task_id] = reschedulable * 1/6

        print(reschedule_table)

    def get_overlaps(self, schedule_cumulation):
        for day, info in schedule_cumulation.items():
            no_of_tasks = len(info['quots'].keys())
