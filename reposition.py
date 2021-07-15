import pprint
from helpers import getDatefromDelta, isWeekend
import operator


class Reposition:
    def __init__(self, tasks, week_day_work, week_end_work):
        self.tasks = tasks
        self.week_day_work = week_day_work
        self.week_end_work = week_end_work

        self.day_scale = []
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

            work_scale = sum_of_area/self.week_day_work

            if work_scale > 0.5 and work_scale < 0.75:
                yellow_days.append(day)
            elif work_scale >= 0.75 and work_scale < 0.9:
                orange_days.append(day)
            elif work_scale > 0.9:
                red_days.append(day)

        self.day_scale = [yellow_days, orange_days, red_days]

    # PLAN:
    # cream off from week days, before or after according to gradient
    # not a problem if no of days get reduced as this is max days needed.

    def fix_weekends(self):
        work_difference = self.week_end_work - self.week_day_work
        weekend_tasks = []

        for day, info in self.schedule.items():
            date = getDatefromDelta(day)
            is_weekend = isWeekend(date)

            if is_weekend:
                no_tasks = 0
                tasks = []
                area = info['data']['sum']
                # print(day, date)
                for task, day_range in self.task_range.items():

                    # see if it is a weekend
                    if int(day) in range(int(day_range[0]), int(day_range[1])+1):
                        no_tasks = no_tasks + 1
                        tasks.append(task)
                weekend_tasks.append([no_tasks, tasks, is_weekend, day, area])

        weekend_tasks.sort(key=operator.itemgetter(0, 4, 2))

        # for weekend in weekend_tasks:
        #     difference =

        print(weekend_tasks)

        if work_difference > 0:
            pass
        if work_difference < 0:
            pass

    # PLAN:
    # Find difference where -ve,
    # use percent_of_dues and find which proportion of which to move out
    # use differences to find close days to relocate

    def fix_difference(self):
        self.to_reschedule = self.basic_reschedule()
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

        pprint.pprint(self.schedule)
        return to_reschedule
        # print('to_reschedule: ', to_reschedule)

        reschedule_table = {'G': {}, 'Y': {}, 'O': {}, 'R': {}}

        for task_id, reschedulable in to_reschedule.items():
            reschedule_table['G'][task_id] = reschedulable * 1/2
            reschedule_table['Y'][task_id] = reschedulable * 1/3
            reschedule_table['O'][task_id] = reschedulable * 1/6

        print(reschedule_table)

    def get_overlaps(self, schedule_cumulation):
        for day, info in schedule_cumulation.items():
            no_of_tasks = len(info['quots'].keys())
