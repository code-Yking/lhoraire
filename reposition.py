from datetime import datetime
import json
from json.decoder import JSONDecodeError
import math
from model import TaskModel
import pprint
from helpers import getDateDelta, getDatefromDelta, isWeekend
import operator


class Reposition:
    def __init__(self, tasks, normal_work, max_work, to_reschedule={}):
        self.tasks = tasks
        self.week_day_work = normal_work[0]
        self.week_end_work = normal_work[1]

        self.max_week_day_work = max_work[0]
        self.max_week_end_work = max_work[1]

        self.to_reschedule = to_reschedule
        self.task_range = {}

        self.schedule = self.schedule_cumulation()
        # print(1)
        # pprint.pprint(self.schedule)
        # pprint.pprint(to_reschedule)

        self.process_data()
        # print(2)
        # pprint.pprint(self.schedule)
        # pprint.pprint(to_reschedule)

        self.to_reschedule.update(self.basic_reschedule())
        # print(3)
        # pprint.pprint(self.schedule)
        # pprint.pprint(to_reschedule)

        self.rescheduling()
        # print(4)
        # pprint.pprint(self.schedule)
        # pprint.pprint(to_reschedule)

    # getting the initial schedule from the tasks
    def schedule_cumulation(self):
        schedule_cumulation = {}

        for task_info, task_object in self.tasks.items():
            days = task_object.generate_list()
            # print(days)

            task_id = f't{task_info[0]}'
            due_date = task_object.due_date

            for day in days:

                date_delta = day[0]
                date = day[0]
                # date = getDatefromDelta(date_delta)
                task_area = day[1]

                if date in schedule_cumulation:
                    schedule_cumulation[date]['quots'][task_id] = task_area
                    schedule_cumulation[date]['data']['days_to_due'][task_id] = due_date - date
                else:
                    schedule_cumulation[date] = {
                        'quots': {
                            task_id: task_area
                        },
                        'data': {
                            'days_to_due': {
                                task_id: due_date - date_delta
                            }
                        }
                    }

            # setting the task ranges
            start_date = math.floor(task_object.start_day)
            self.task_range[task_id] = [start_date, due_date - 1]

        return schedule_cumulation

    def process_data(self):
        # schedule_cumulation = cumulation

        for day, info in self.schedule.items():
            sum_of_area = 0

            for task_id, quote in info['quots'].items():
                sum_of_area = sum_of_area + quote

            # percent_of_work = {task_id: quote /
            #                    sum_of_area for task_id, quote in info['quots'].items()}

            info['data']['sum'] = sum_of_area
            info['data']['difference'] = self.week_day_work - sum_of_area
            # info['data']['percent_of_work'] = percent_of_work

    # filling days with tasks according to their proximity to the deadline
    def day_filling(self, tasks, surface=False):
        tasks_list = tasks

        # for each day with tasks that can be rescheduled into
        for i, day_info in enumerate(tasks_list):
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
                    diff = 1 if self.schedule[day]['data']['sum'] + \
                        1 <= self.max_week_end_work else self.max_week_end_work - self.schedule[day]['data']['sum']
                else:
                    diff = 0.5 if self.schedule[day]['data']['sum'] + \
                        0.5 <= self.max_week_day_work else self.max_week_day_work - self.schedule[day]['data']['sum']

            # task ids array
            tasks = day_info[1]

            # loop to put in the rescheduled tasks
            # TODO increase mins
            while diff > 0.001 and sum({k: self.to_reschedule[k] for k in self.to_reschedule.keys() & tasks}.values()) > 0.001:
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
                        # print(dues)
                        self.schedule[day]['data']['days_to_due'][task] = days_to_due

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

        # print(self.to_reschedule, self.task_range)

        for task, hours in self.to_reschedule.items():
            if hours == 0:
                continue

            if self.task_range[task][0] == getDateDelta(datetime.now()) + 1:
                continue

            elif self.task_range[task][0] - 5 >= getDateDelta(datetime.now()) + 1:
                lower_date = self.task_range[task][0] - 5
            else:
                lower_date = getDateDelta(datetime.now()) + 1

            for n in range(lower_date, self.task_range[task][0]):
                precede_days_dict[n] = precede_days_dict.get(n, []) + [task]
            self.task_range[task][0] = lower_date

        for date, tasks in precede_days_dict.items():
            precede_days.append([len(tasks), tasks, isWeekend(getDatefromDelta(date)), date, 0, [
                                self.task_range[t][1] + 1 - date for t in tasks]])

        return precede_days

    def free_days(self):
        for task, range in self.task_range.items():
            last_date = range[1]

            for t in dict(self.schedule[last_date]['quots']):
                if t != task and last_date != self.task_range[t][1]:
                    area_rm = self.schedule[last_date]['quots'][t]
                    self.schedule[last_date]['data']['sum'] = self.schedule[last_date]['data']['sum'] - area_rm
                    self.schedule[last_date]['data']['difference'] = self.schedule[last_date]['data']['difference'] + area_rm
                    self.schedule[last_date]['quots'].pop(t)
                    self.schedule[last_date]['data']['days_to_due'].pop(t)

                    self.to_reschedule[t] = self.to_reschedule.get(
                        t, 0) + area_rm

                    if last_date == self.task_range[t][0]:
                        self.task_range[t][0] = last_date + 1
                    # print(t, self.task_range[t])

    def rescheduling(self):
        # pprint.pprint(self.to_reschedule)
        self.free_days()
        # pprint.pprint(self.to_reschedule)
        self.update_schedule()
        # pprint.pprint(self.to_reschedule)

        work_difference = self.week_end_work - \
            self.week_day_work       # no of extra hours for weekends

        # this will collect the days that can be rescheduled into
        weekday_days, weekend_days = self.reschedulable_days()

        # priority is given to sort the weekend days,
        # so that more data is added first to the ones with less pressure
        # Priority no 1: No of tasks done during that weekend day. Lesser would be above
        # Priority no 2: Total number of hours worked during the weekend day. Lesser would be above
        # Priority no 3: Saturday or Sunday. Saturday is favored over sunday
        weekend_days.sort(key=operator.itemgetter(0, 4, 2))
        weekday_days.sort(key=operator.itemgetter(0, 4))

        # if more work can be done during weekends than weekdays,
        # then excess tasks can be rescheduled into those days
        if work_difference > 0:
            self.day_filling(weekend_days)
            # print(self.to_reschedule)

        # else tasks have to be removed from them and added to to_reschedule dict
        elif work_difference < 0:
            for weekend in weekend_days:
                self.schedule[weekend[3]]['data']['difference'] = self.schedule[weekend[3]
                                                                                ]['data']['difference'] - abs(work_difference)
            self.to_reschedule = {k: self.basic_reschedule().get(
                k, 0) + self.to_reschedule.get(k, 0) for k in set(self.to_reschedule)}

        self.day_filling(weekday_days)          # rescheduling into weekdays

        # if there are tasks that still needs to be rescheduled
        while len(self.to_reschedule):
            # getting 5 days prior to the start date of the tasks
            extra_days = self.precedence()
            # print('one to final')
            # pprint.pprint(self.to_reschedule)
            # if reached today, can't get more room from earlier days
            if not len(extra_days):
                # get ALL week days and weekend days that have the tasks
                weekday_days, weekend_days = self.reschedulable_days()

                # sort these days such that earlier comes first
                # TODO see if there is a better option
                weekend_days.sort(key=operator.itemgetter(3))
                weekday_days.sort(key=operator.itemgetter(3))

                # fill days untill it reaches maximum limit
                while len(self.to_reschedule):
                    _to_reschedule = dict(self.to_reschedule)
                    self.day_filling(weekend_days, True)
                    self.day_filling(weekday_days, True)
                    # print('final')
                    # pprint.pprint(self.to_reschedule)
                    # pprint.pprint(self.schedule)

                    if _to_reschedule == self.to_reschedule:
                        break
                break

            # sorting the extra days preceeding the start date, filling the last first
            extra_days.sort(key=operator.itemgetter(3), reverse=True)
            self.day_filling(extra_days)

        self.finalise_schedule()
        print('Sums: ', self.get_task_sums())
        self.output_tasks()
        self.output_schedule()

    def update_schedule(self):
        with open('schedule.json') as schedule_json:
            try:
                schedule = json.load(schedule_json)
            except JSONDecodeError:
                schedule = {}
        _schedule = dict(schedule)
        for day in _schedule.keys():
            dayDelta = getDateDelta(day)
            schedule[dayDelta] = schedule.pop(day)

        # print(schedule)
        schedule.update(self.schedule)
        self.schedule = schedule

    def finalise_schedule(self):
        _schedule = dict(self.schedule)
        for dayDelta, info in _schedule.items():
            day = getDatefromDelta(int(dayDelta))
            self.schedule[day] = self.schedule.pop(dayDelta)

        sorted(self.schedule, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))
        # self.schedule[day]['data'].pop('difference')
        # self.schedule[day]['data'].pop('days_to_due')

    def get_task_sums(self):
        total_areas = {}
        for info in self.schedule.values():
            for task, area in info['quots'].items():
                total_areas[task] = total_areas.get(task, 0) + area
        return total_areas

    def output_tasks(self):
        with open('tasks.json') as json_file:
            data = json.load(json_file)

        for task, info in data.items():
            if task in self.task_range.keys():
                _info = info
                _info[2] = self.task_range[task]
                # _info[3] = getDateDelta(datetime.now()) + 1
                _info[4] = self.to_reschedule.get(task, 0)
                # print('final', task, info[2], _info[2])
                data[task] = _info

        with open('tasks.json', 'w') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)

    def output_schedule(self):
        with open('schedule.json') as schedule_json:
            try:
                schedule = json.load(schedule_json)
            except JSONDecodeError:
                schedule = {}

        # pprint.pprint(schedule)
        schedule.update(self.schedule)

        with open('schedule.json', 'w') as outfile:
            json.dump(schedule, outfile, indent=4, sort_keys=True)

    # PLAN:
    # Find difference where -ve,
    # use percent_of_dues and find which proportion of which to move out
    # use differences to find close days to relocate

    def basic_reschedule(self):
        # print(self.task_range)
        to_reschedule = {}

        for day, info in self.schedule.items():
            diff = info['data']['difference']

            if diff >= 0:               # day is skipped if there is no difference
                pass
            else:
                i = 0               # to allow for small task hours which might not be able to provide
                while i < 5:
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

                            if day == self.task_range[task_id][0]:
                                self.task_range[task_id][0] = self.task_range[task_id][0] + 1
                            elif day == self.task_range[task_id][1]:
                                self.task_range[task_id][1] = self.task_range[task_id][1] - 1

                        elif quote < portion_needed[task_id]:
                            if task_id in to_reschedule.keys():
                                to_reschedule[task_id] = to_reschedule[task_id] + quote
                            else:
                                to_reschedule[task_id] = quote

                            info['data']['difference'] = info['data']['difference'] + quote
                            info['quots'].pop(task_id)
                            info['data']['days_to_due'].pop(task_id)
                            info['data']['sum'] = info['data']['sum'] - quote

                            if day == self.task_range[task_id][0]:
                                self.task_range[task_id][0] = self.task_range[task_id][0] + 1
                            elif day == self.task_range[task_id][1]:
                                self.task_range[task_id][1] = self.task_range[task_id][1] - 1
                    i = i+1

        # print('to_reschedule: ', to_reschedule)
        # print(self.task_range)
        return to_reschedule
