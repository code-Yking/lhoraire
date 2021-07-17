import pprint
from helpers import getDatefromDelta, isWeekend
import operator


class Reposition:
    def __init__(self, tasks, week_day_work, week_end_work):
        self.tasks = tasks
        self.week_day_work = week_day_work
        self.week_end_work = week_end_work

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

            start_date = task_object.start_day
            self.task_range[task_id] = (start_date, due_date)
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

    def day_filling(self, tasks, work_difference):
        tasks_list = tasks
        for i, day_info in enumerate(tasks_list):          # for each weekend
            # the day delta number
            day = day_info[3]

            # extra amount of hours that can be filled
            diff = self.schedule[day]['data']['difference'] + \
                work_difference

            # print('init', diff)
            # print()
            # print(day_info)
            # print()
            # pprint.pprint(self.schedule[day])
            # print()
            # pprint.pprint(self.to_reschedule)
            # print()
            # tasks (with the hours) that are present in to_reschedule dict and present in this weekend
            # reschedulable_tasks = {
            #     k: self.to_reschedule[k] for k in self.to_reschedule.keys() and tasks}

            # tasks id array
            tasks = day_info[1]

            # loop to put in the rescheduled tasks
            while diff > 0.1 and sum({k: self.to_reschedule[k] for k in self.to_reschedule.keys() & tasks}.values()) > 0.1:
                # days to due array
                dues = day_info[5]

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

                    # using `Proximity` Percentage to calculate the max available portion for that task
                    portion_available = 1 / \
                        dues[index] / sum_reciprocals * diff

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
                        tasks_list[i][5].remove(dues[index])

                    self.schedule[day]['data']['sum'] = self.schedule[day]['data']['sum'] + portion_used
                    self.schedule[day]['data']['difference'] = diff
                    if task in self.schedule[day]['quots'].keys():
                        self.schedule[day]['quots'][task] = self.schedule[day]['quots'][task] + portion_used
                    else:
                        self.schedule[day]['quots'][task] = portion_used
                        self.schedule[day]['data']['days_to_due'][task] = dues[index]

                    self.day_scale_append(
                        day, self.schedule[day]['data']['sum'], self.week_end_work)
                # print(diff)
                # print('final', diff)
                # print()
                # print(day_info)
                # print()
                # pprint.pprint(self.schedule[day])
                # print()
                # pprint.pprint(self.to_reschedule)
                # print()

    # PLAN:
    # cream off from week days, before or after according to gradient
    # not a problem if no of days get reduced as this is max days needed.

    def summarized_schedule(self):
        weekend_tasks, weekday_tasks = [], []

        for day, info in self.schedule.items():
            date = getDatefromDelta(day)
            is_weekend = isWeekend(date)

            if is_weekend:
                no_tasks = 0
                tasks = []
                task_dues = []
                area = info['data']['sum']
                # print(day, date)
                for task, day_range in self.task_range.items():

                    # see if it is a weekend and the task needs to be reschedulable
                    if int(day) in range(int(day_range[0]), int(day_range[1])+1) and task in self.to_reschedule.keys():
                        no_tasks = no_tasks + 1
                        tasks.append(task)
                        task_dues.append(int(day_range[1])-day+1)

                weekend_tasks.append(
                    [no_tasks, tasks, is_weekend, day, area, task_dues])

        return weekday_tasks, weekend_tasks

    def fix_weekends(self):
        work_difference = self.week_end_work - self.week_day_work
        weekday_tasks, weekend_tasks = self.summarized_schedule()

        # priority is given to sort the weekend days,
        # so that more data is added first to the ones with less pressure
        # Priority no 1: No of tasks done during that weekend day. Lesser would be above
        # Priority no 2: Total number of hours worked during the weekend day. Lesser would be above
        # Priority no 3: Saturday or Sunday. Saturday is favored over sunday
        weekend_tasks.sort(key=operator.itemgetter(0, 4, 2))

        print('day scale', self.day_scale)

        # if more work can be done during weekends than weekdays
        if work_difference > 0:
            self.day_filling(weekend_tasks, work_difference)

        if work_difference < 0:

            for weekend in weekend_tasks:
                self.schedule[weekend[3]]['data']['difference'] = self.schedule[weekend[3]
                                                                                ]['data']['difference'] - abs(work_difference)
            self.to_reschedule = {k: self.basic_reschedule().get(
                k, 0) + self.to_reschedule.get(k, 0) for k in set(self.to_reschedule)}

        print('day scale', self.day_scale)

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
