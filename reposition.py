from datetime import datetime, date as d_
import json
from json.decoder import JSONDecodeError
import math
import pprint
from .helpers import getDateDelta, getDatefromDelta, isWeekend
import operator
import copy

RESCHEDULE_LIMIT = 0


class Reposition:
    def __init__(self, newtasks, oldschedule, oldtasks, normal_work, max_work, extra_hours, localdate):
        self.tasks = newtasks
        self.week_day_work = float(normal_work[0])
        self.week_end_work = float(normal_work[1])

        self.max_week_day_work = float(max_work[0])
        self.max_week_end_work = float(max_work[1])

        self.extra_hours = dict(extra_hours)
        self.task_range = {}
        self.task_total = {}

        self.task_obj = oldtasks
        # print('hi: ', self.task_obj)

        self.today = localdate

        self.schedule = self.schedule_cumulation()
        self.oldschedule = oldschedule
        print(1)
        pprint.pprint(self.schedule)
        # pprint.pprint(to_reschedule)

        print(self.week_day_work, self.week_end_work)
        print(self.max_week_day_work, self.max_week_end_work)

        self.process_data()
        print('Processed Schedule')
        pprint.pprint(self.schedule)
        # pprint.pprint(to_reschedule)
        print()

        print('Task Range before BASIC reschedule')
        pprint.pprint(self.task_range)

        self.to_reschedule = self.basic_reschedule()
        print('Basic Rescheduled Schedule')
        pprint.pprint(self.schedule)
        print()
        print('Initial to_reschedule')
        # pprint.pprint(to_reschedule)
        print()
        print('Initial Sum')
        pprint.pprint(self.get_task_sums())

        print('Task Range before reschedule')
        pprint.pprint(self.task_range)
        self.rescheduling()
        # print(4)
        # pprint.pprint(self.schedule)
        # pprint.pprint(to_reschedule)

    def set_old_schedule(self):
        # oldschedule = self.oldschedule
        # _o_schedule = dict(oldschedule)

        # for day, data in _o_schedule.items():
        #     dayDelta = getDateDelta(day)
        #     oldschedule[dayDelta] = oldschedule.pop(day)

        #     sum_of_tasks = sum(data['quots'].values())
        #     # difference = 0
        #     if isWeekend(day):
        #         difference = self.week_end_work - \
        #             sum_of_tasks if self.week_end_work - sum_of_tasks > 0 else 0
        #     else:
        #         difference = self.week_day_work - \
        #             sum_of_tasks if self.week_day_work - sum_of_tasks > 0 else 0
        #     oldschedule[dayDelta]['data'] = {
        #         'difference': difference, 'sum': sum_of_tasks}
        print('\033[91m')
        pprint.pprint(self.schedule)
        print('oldschedule')
        pprint.pprint(self.oldschedule)

        self.oldschedule.update(self.schedule)
        self.schedule = self.oldschedule

        print('updated schedule; normal = old update normal')
        pprint.pprint(self.schedule)
        print('\033[0m')
        # self.schedule = schedule

    # getting the initial schedule from the tasks

    def schedule_cumulation(self):
        schedule_cumulation = {}

        for task_info, task_object in self.tasks.items():
            days = task_object.generate_list()
            # print(days)

            task_id = f't{task_info[0]}'
            due_date = task_object.due_date
            self.task_total[task_id] = task_object.work

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

        # print('schedule_cu', schedule_cumulation)
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
            if isWeekend(getDatefromDelta(day)):
                info['data']['difference'] = self.week_end_work - sum_of_area
            else:
                info['data']['difference'] = self.week_day_work - sum_of_area
            # info['data']['percent_of_work'] = percent_of_work

    # filling days with tasks according to their proximity to the deadline
    def day_filling(self, tasks, surface=False, precedence_available=True):
        true_surface = surface

        # initial day filler items for resetting
        init_day_filler_items = copy.deepcopy(tasks)

        # day filler items for a single iteration
        day_filler_items = copy.deepcopy(tasks)

        # to prevent infinite loop
        n = 1
        while n < 50:
            print('LOOP NUMBER ', n)

            pprint.pprint(day_filler_items)
            print()
            pprint.pprint(init_day_filler_items)

            # For every task that has to be rescheduled
            for task in list(self.to_reschedule.keys()):

                # list of days with this task
                filtered = list(
                    filter(lambda x: task in x[1], day_filler_items))

                # divided into groups of five. First five high priority is filled before others
                segmented_filterd = list([filtered[x:x+5]
                                          for x in range(0, len(filtered), 5)])

                if surface:
                    print("\033[92m", "Surfacing Loop ",
                          task, "\033[0m")

                # print('task dayfilling: ', task)
                # pprint.pprint(self.to_reschedule)
                # __to_reschedule = dict(self.to_reschedule)
                # n = 1
                # for each group of 5 days in the segmented filtered list
                # print("segmented_filterd")
                # pprint.pprint(segmented_filterd)

                # FOR EACH GROUP of 5 in the filtered list of lists
                # this is so that extra space is divided among groups instead of days
                for group_index, group in enumerate(segmented_filterd):
                    # print("GROUP")
                    # pprint.pprint(group)
                    # print(n)

                    while len(group):
                        # forming ratio formula
                        no_content = len(group)         # no of content
                        eq_gradient = 1/no_content      # gradient of ratio formula
                        denominator = sum(
                            [n*eq_gradient for n in range(1, no_content+1)])

                        # true surface
                        surface = true_surface
                        print('SURFACE', surface)

                        # area which are really small that has to be skipped
                        group_excluded_area = 0

                        # initial group difference - cummulated free space in the group
                        group_diff = math.nan

                        # unchanging reschedule copy, values from which are used for the areas in this group
                        # has to be in here as the following rounds would need update
                        _to_reschedule = dict(self.to_reschedule)
                        # print(_to_reschedule, to_reschedule)

                        # EACH DAY in this group, enumerated and duplicated as items need to be deleted
                        for i, day in enumerate(list(group)):
                            print('TASK: ', task)
                            print('Day:', getDatefromDelta(day[3]))
                            print('to_reschedule BEFORE:')
                            pprint.pprint(self.to_reschedule)

                            # gonna be there in the list
                            list_i = day_filler_items.index(day)
                            task_index = day[1].index(task)
                            day_updated = False                     # boolean to see if the day gets updated

                            days_final = False                      # if day has reached its MAX limit
                            priority_index = no_content - i         # priority for the ratio formula

                            # calculating required area off this day.
                            # to_reschedule data from the static group copy is used
                            # so that the real total to_reschedule hours can be filled in this group
                            # and the real to_reschedule can be edited as we go
                            required_area = _to_reschedule[task] * \
                                priority_index * eq_gradient / denominator

                            print("GROUP LENGTH:", len(group))
                            print("REQUIRED AREA: ", required_area)

                            # TODO exchange this with helper method and remove item from list
                            isWeekend = day[2]

                            # figuring the free space for this day
                            # if day is defined in the schedule
                            if day[3] in self.schedule:
                                # difference from the schedule
                                diff = self.schedule[day[3]
                                                     ]['data']['difference']
                                print('schedule diff', diff)

                                # if there is no difference or if it is really small
                                if diff <= 0.001 and surface:

                                    # if there are extra hours allocated
                                    extra_hours = 0
                                    if day[3] in self.extra_hours:
                                        extra_hours = float(
                                            self.extra_hours.pop(day[3]))

                                    # using maximum hours with any extra hours as difference
                                    if isWeekend:
                                        diff = self.max_week_end_work - \
                                            self.schedule[day[3]
                                                          ]['data']['sum'] + extra_hours
                                        days_final = True
                                    else:
                                        diff = self.max_week_day_work - \
                                            self.schedule[day[3]
                                                          ]['data']['sum'] + extra_hours
                                        days_final = True
                                    print('surface diff', diff)

                            # day is not in the schedule, should be a new precedence day, gets defaults
                            # will be added to the schedule at the end
                            else:
                                if isWeekend:
                                    diff = self.week_end_work
                                else:
                                    diff = self.week_day_work

                            # STILL no space in this day; day is removed and skipped
                            # TODO check possibility for this, make sure no filled days are sent
                            if diff < 0.001:
                                print('DAY SKIPPED and REMOVED', getDatefromDelta(
                                    day[3]), 'This day has no free space, diff < 0.001 after figuring;')
                                print('---- end of day ----')
                                pprint.pprint(self.schedule.get(
                                    day[3], {}))
                                # not surfacing and big task to be rescheduled OR if it has reached its max, day is removed

                                # if days_final or not surface:
                                # TODO do days_final check for unneccesary loop

                                # remove day from continuing in this iteration
                                # day_filler_items.remove(day)

                                # and in the iterations to come
                                # init_day_filler_items.remove(
                                #     list(filter(lambda x: x[3] == day[3], init_day_filler_items))[0])
                                # day_updated = True

                                # else:
                                #     day_filler_items[list_i][0] -= 1
                                #     day_filler_items[list_i][1].pop(task_index)
                                #     day_filler_items[list_i][5].pop(task_index)
                                #     day_updated = True
                                # day is removed from this instantanious group as it can't hold any more hours with the limit
                                # group.remove(day)
                                continue
                            # print(diff)

                            # calculating available area, using `Proximity` Percentage
                            days_to_dues = day[5]
                            due = days_to_dues[day[1].index(task)]

                            # amount of area that can be added with this given diff and other tasks in this day
                            available_area = 1/due / \
                                sum([1/n for n in days_to_dues]) * diff
                            print('diff: ', diff)
                            print("AVAILABLE AREA:", available_area)

                            # assigning portion that is going to be used according to the free and requierd area
                            if required_area < available_area:
                                portion_used = required_area

                            elif required_area >= available_area:
                                print('DAY REMOVED',
                                      'required_area >= available_area')
                                portion_used = available_area
                                # day is removed from the group as it is filled
                                # if day in group:
                                # removal wouldn't affect other day calculations as constants outside loop
                                group.remove(day)

                            print('Portion Used', portion_used)

                            # if the portion to be used has less than 20 mins of work
                            if portion_used + self.schedule.get(day[3], {}).get('quots', {}).get(task, 0) < float(20/60):
                                # adds to a variable the hours
                                # group_excluded_area += portion_used

                                print(
                                    'DAY SKIPPED', 'this day has less than 20mins of this task')

                                # if groups alloted reschedule hours is greater than 1 hour, and day is not removed
                                # if _to_reschedule[task] > 1 and day in group:
                                print(
                                    'DAY REMOVED & SKIPPED', 'this task has less than 1 hour of to_reschedule')

                                # day is removed from group as this would
                                if day in group:
                                    if group[-1] == day:
                                        group.remove(day)
                                        if len(segmented_filterd) > group_index + 2:
                                            segmented_filterd[group_index +
                                                              1].insert(0, day)
                                        # if not day_updated:
                                        #     day_filler_items[list_i][0] -= 1
                                        #     day_filler_items[list_i][1].pop(
                                        #         task_index)
                                        #     day_filler_items[list_i][5].pop(
                                        #         task_index)
                                        #     day_updated = True
                                # print(task, day[3])
                                print('---- end of day ----')
                                continue

                            # print("segmented_filterd 3")
                            # pprint.pprint(segmented_filterd)

                            self.to_reschedule[task] = round(self.to_reschedule.get(
                                task) - portion_used, 5)
                            # print(
                            #     'to_reschedule updated', self.to_reschedule[task], task, ' : ', self.to_reschedule[task], ' hrs')
                            # print(day[3], task, required_area)

                            if day[3] not in self.schedule.keys():
                                # print(
                                #     'day not in schedule; should be precedence, added empty data to schedule')
                                self.schedule[day[3]] = {
                                    'data': {'days_to_due': {}}, 'quots': {}}

                            self.schedule[day[3]]['data']['sum'] = self.schedule[day[3]]['data'].get(
                                'sum', 0) + portion_used
                            # print(day[3], diff, portion_used)
                            self.schedule[day[3]
                                          ]['data']['difference'] = diff - portion_used

                            # print(group)
                            if day in group:
                                group.remove(day)

                            if diff - portion_used <= 0.001:
                                # if (day in day_filler_items and not surface and self.to_reschedule[task] > self.task_total[task]/3) \
                                # if (day in day_filler_items) and (days_final or not surface) and not day_updated:
                                print(
                                    f'{day[3]} in day filler items, removed')
                                day_filler_items.remove(day)
                                day_updated = True
                                # else:
                                #     pprint.pprint(day_filler_items)
                                #     print(day)

                                # if (days_final or not surface):
                                # init_day_filler_items.remove(day)
                                day_item = list(
                                    filter(lambda x: x[3] == day[3], init_day_filler_items))

                                if day_item:
                                    init_day_filler_items.remove(
                                        list(filter(lambda x: x[3] == day[3], init_day_filler_items))[0])
                                    print(
                                        f'{day[3]} in init day filler items, removed')
                                    day_updated = True

                            # print("segmented_filterd 4")
                            # pprint.pprint(segmented_filterd)

                            if task in self.schedule[day[3]]['quots'].keys():
                                self.schedule[day[3]]['quots'][task] = self.schedule[day[3]
                                                                                     ]['quots'][task] + portion_used
                            else:
                                self.schedule[day[3]
                                              ]['quots'][task] = portion_used
                                # print(dues)
                                if 'days_to_due' in self.schedule[day[3]]['data']:
                                    self.schedule[day[3]
                                                  ]['data']['days_to_due'][task] = due
                                else:
                                    self.schedule[day[3]]['data']['days_to_due'] = {
                                        task: due}

                            # if day in group:
                            #     day[0] -= 1
                            #     day[1].pop(task_index)
                            #     day[5].pop(task_index)

                            print('init_day BEFORE')
                            # print(init_day_filler_items)

                            if not day_updated:
                                day_filler_items[list_i][0] -= 1
                                day_filler_items[list_i][1].pop(task_index)
                                day_filler_items[list_i][5].pop(task_index)

                            # print('day_filler')
                            # print(day_filler_items)
                            # print('init_day AFTER')
                            # print(init_day_filler_items)

                            print('schedule updated for',
                                  getDatefromDelta(day[3]))
                            pprint.pprint(self.schedule[day[3]])
                            print('to_reschedule AFTER:')
                            pprint.pprint(self.to_reschedule)
                            print('sum AFTER')
                            print(self.get_task_sums()[task])
                            print(self.get_task_sums())
                            print('---- end of day ----')
                            print()
                            # day[4] += portion_used

                            # if len(day[1]) == 0:
                            #     group.remove(day)

                        # print('after', _to_reschedule, self.to_reschedule)
                        # if no free space in the group, then break
                        group_diff = sum([self.schedule.get(day[3], {}).get('data', {}).get('difference', 0)
                                          for day in group])

                        # segment_diff += group_diff

                        # print(group_diff, [getDatefromDelta(day[3])
                        #    for day in group])

                        # if group_diff - group_excluded_area < 0.001:
                        #     break

                        # surface = False

                    # does not need to proceed if this task no longer needs to be rescheduled
                        if self.to_reschedule[task] <= 0.001:
                            break

                print('n is ', n)

                # if very less hours remain to be rescheduled.
                if self.to_reschedule[task] <= 0.001:
                    # removes day from to_reschedule
                    self.to_reschedule.pop(task)

                    # removes day from day_filler_items and init_day_filler_items
                    # this will prevent reiteration of this task

                    # from init_day_filler_items
                    for day in init_day_filler_items:
                        if task in day[1]:
                            # TODO check this out
                            # if day filler item has only one day, removes the item
                            if day[0] == 1:
                                print('DELETING DAYS')
                                init_day_filler_items.remove(day)
                                # if day in day_filler_items:
                                #     day_filler_items.remove(day)
                            else:
                                # else edits the day filler items
                                print('EDITTING GROUPED DAYS')
                                # print(task, day[1])
                                in_item_i = init_day_filler_items.index(day)
                                init_day_filler_items[in_item_i][0] -= 1
                                index = init_day_filler_items[in_item_i][1].index(
                                    task)
                                init_day_filler_items[in_item_i][1].pop(index)
                                init_day_filler_items[in_item_i][5].pop(index)

                    # from day_filler_items, similar to above
                    for day in day_filler_items:
                        if task in day[1]:
                            if day[0] == 1:
                                # if day in day_filler_items:
                                day_filler_items.remove(day)
                            else:
                                item_i = day_filler_items.index(day)
                                day_filler_items[item_i][0] -= 1
                                index = day_filler_items[item_i][1].index(
                                    task)
                                day_filler_items[item_i][1].pop(index)
                                day_filler_items[item_i][5].pop(index)

            n += 1
            print('\033[94m', self.to_reschedule, "\033[0m")

            if not len(self.to_reschedule) or not len(day_filler_items):
                break

            pprint.pprint(day_filler_items)
            pprint.pprint(init_day_filler_items)

            day_filler_items = list(
                filter(lambda x: any(k in self.to_reschedule.keys() for k in x[1]), copy.deepcopy(init_day_filler_items)))
            # day_filler_items = copy.deepcopy(init_day_filler_items)
            # if not surface and len(day_filler_items):

        print("\033[96m")
        pprint.pprint(day_filler_items)
        print("\033[0m")
        # print('NEW')
        # pprint(schedule)
        # pprint(self.to_reschedule)

    # produce day filler items for filling in days that are already in the schedule

    def reschedulable_days(self, surface=False):
        # TODO fix this to disinclude empty items
        # array of days that contain details of tasks that can be resceduled into those days
        weekend_days, weekday_days = [], []

        # iterate through date and respective information of schedule tasks
        for day, info in self.schedule.items():

            area = info['data']['sum']      # total time of these tasks
            date = getDatefromDelta(day)        # get string text
            is_weekend = isWeekend(date)

            if not surface:
                if info['data']['difference'] <= 0.001:
                    continue
            else:
                if is_weekend:
                    if self.max_week_end_work + float(self.extra_hours.get(day, 0)) - area <= 0.001:
                        continue
                    else:
                        info['data']['difference'] = self.max_week_end_work + \
                            float(self.extra_hours.get(day, 0)) - area
                else:
                    if self.max_week_day_work + float(self.extra_hours.get(day, 0)) - area <= 0.001:
                        continue
                    else:
                        info['data']['difference'] = self.max_week_day_work + \
                            float(self.extra_hours.get(day, 0)) - area

            # 0, 1, 2 => weekday, sat, sun. For easy ordering

            no_tasks = 0
            tasks = []          # tasks that can be resceduled into this day
            task_dues = []      # days to due of these tasks

            # iterate through all the tasks in the task_range property
            for task, day_range in self.task_range.items():
                # see if this day is in the range of any tasks and if those task needs to be reschedulable
                if int(day) in range(int(day_range[0]), int(day_range[1])+1) and task in self.to_reschedule.keys():
                    # if task has value of 0 in to_reschedule
                    # TODO make sure that to_reschedule becomes 0
                    if self.to_reschedule[task] == 0:
                        continue

                    # add to the lists about tasks defined before
                    no_tasks = no_tasks + 1
                    tasks.append(task)
                    task_dues.append(int(day_range[1])-day+1)

            if not len(tasks):
                continue

            # adding to the lists of days defined before
            if is_weekend:
                weekend_days.append(
                    [no_tasks, tasks, is_weekend, day, area, task_dues])
            else:
                weekday_days.append([no_tasks, tasks, 0, day, area, task_dues])

        return weekday_days, weekend_days

    # Produces day filler items for the purpose of precedence.
    def precedence(self):
        precede_days = []

        # dict with days and the tasks that can be done on these days
        precede_days_dict = {}

        # print(self.to_reschedule, self.task_range)

        # iterate through the tasks that have hours to be rescheduled
        for task, hours in self.to_reschedule.items():
            # if no hours to be rescheduled, continue
            if hours == 0:
                continue

            # if start date of the task is tomorrow, continue
            # TODO TIME ZONES!!
            if self.task_range[task][0] == getDateDelta(self.today) + 1:
                continue
            # if 5 less than start date of task is still more than tomorrow
            elif self.task_range[task][0] - 5 >= getDateDelta(self.today) + 1:
                lower_date = self.task_range[task][0] - 5
            # 5 less than start date of task is less than tomorrow, keep tommorow
            else:
                lower_date = getDateDelta(self.today) + 1

            # add the days from this lower date till the day before start date to precede_days_dict with tasks
            for n in range(lower_date, self.task_range[task][0]):
                precede_days_dict[n] = precede_days_dict.get(n, []) + [task]

            # update this task in the task_range property with lower date
            self.task_range[task][0] = lower_date

        # add to precede_days according to day_filling format
        for date, tasks in precede_days_dict.items():

            if self.schedule.get(date, {}).get('data', {}).get('difference', 1) <= 0.001:
                continue

            precede_days.append([len(tasks), tasks, isWeekend(getDatefromDelta(date)), date, 0, [
                                self.task_range[t][1] + 1 - date for t in tasks]])

        print('precede days')
        pprint.pprint(precede_days)

        return precede_days

    # free days that are before the due date of a task from other tasks
    def free_final_days(self):
        for task, range in self.task_range.items():
            last_date = range[1]

            for t in dict(self.schedule[last_date]['quots']):
                if t != task and last_date != self.task_range[t][1]:
                    area_rm = self.schedule[last_date]['quots'][t]
                    self.schedule[last_date]['data']['sum'] = self.schedule[last_date]['data']['sum'] - area_rm
                    self.schedule[last_date]['data']['difference'] = self.schedule[last_date]['data']['difference'] + area_rm
                    self.schedule[last_date]['quots'].pop(t)
                    # pprint.pprint(self.schedule)
                    self.schedule[last_date]['data']['days_to_due'].pop(t)

                    self.to_reschedule[t] = self.to_reschedule.get(
                        t, 0) + area_rm

                    if last_date == self.task_range[t][0]:
                        self.task_range[t][0] = last_date + 1
                    # print(t, self.task_range[t])

    def rescheduling(self):
        self.free_final_days()
        # self.update_schedule()

        # difference between weekend and weekday works
        work_difference = self.week_end_work - \
            self.week_day_work       # no of extra hours for weekends
        print("work difference", work_difference,
              self.week_end_work, self.week_day_work)

        # this will collect the days that can be rescheduled into
        weekday_days, weekend_days = self.reschedulable_days()

        # priority is given to sort the weekend days,
        # so that more data is added first to the ones with less pressure
        # Priority no 1: No of tasks done during that weekend day. Lesser would be above
        # Priority no 2: Total number of hours worked during the weekend day. Lesser would be above
        # Priority no 3: Saturday or Sunday. Saturday is favored over sunday
        # weekend_days.sort(key=operator.itemgetter(3), reverse=True)
        weekend_days.sort(key=operator.itemgetter(0, 4, 2))
        # weekday_days.sort(key=operator.itemgetter(3), reverse=True)
        weekday_days.sort(key=operator.itemgetter(0, 4))

        # for day in self.schedule.keys():
        #     if isWeekend(getDatefromDelta(day)):
        #         self.schedule[day
        #                       ]['data']['difference'] += abs(work_difference)

        # combined = list(weekend_days + weekday_days)
        # schedule_ = self.schedule
        # to_resch_ = self.to_reschedule
        # print(self.to_reschedule)
        self.day_filling(list(weekend_days + weekday_days))
        # print("OLD")
        # pprint.pprint(self.schedule)
        # pprint.pprint(self.to_reschedule)

        # print('before')
        # pprint.pprint(self.schedule)

        # if check == self.schedule:
        #     # pprint.pprint(check)
        #     print(True)
        # if more work can be done during weekends than weekdays,
        # then excess tasks can be rescheduled into those days
        # if work_difference > 0:
        #     # self.day_filling(weekend_days)
        #     pass

        # else tasks have to be removed from them and added to to_reschedule dict
        # elif work_difference < 0:
        #     self.to_reschedule = {k: self.basic_reschedule().get(
        #         k, 0) + self.to_reschedule.get(k, 0) for k in set(self.to_reschedule)}
        # TODO whats this

        # self.day_filling(weekday_days)          # rescheduling into weekdays

        # print('afters')
        # pprint.pprint(self.schedule)

        for task, hours in dict(self.to_reschedule).items():
            if hours < 0.001:
                self.to_reschedule.pop(task)

        pprint.pprint(self.to_reschedule)

        self.set_old_schedule()

        # print('to_reschedule before precedence', self.to_reschedule)
        precedence_available = True

        # if there are tasks that still needs to be rescheduled
        while len(self.to_reschedule):
            # getting 5 days prior to the start date of the tasks
            if precedence_available:
                extra_days = self.precedence()
            # if reached today, can't get more room from earlier days
                if len(extra_days):
                    # sorting the extra days preceeding the start date, filling the last first
                    extra_days.sort(key=operator.itemgetter(3), reverse=True)
                    self.day_filling(extra_days)
                else:
                    precedence_available = False

            # _to_reschedule = dict(self.to_reschedule)
            # get ALL week days and weekend days that have the tasks
            weekday_days, weekend_days = self.reschedulable_days(True)

            # sort these days such that earlier comes first
            # TODO see if there is a better option
            # weekend_days.sort(key=operator.itemgetter(3), reverse=True)
            weekend_days.sort(key=operator.itemgetter(0, 4, 2))
            # weekday_days.sort(key=operator.itemgetter(3), reverse=True)
            weekday_days.sort(key=operator.itemgetter(0, 4))

            self.day_filling(list(weekend_days + weekday_days),
                             True, precedence_available)

            if not precedence_available:
                print('end of process')
                break

            # print(1)
            # pprint.pprint(_to_reschedule)
            # print(2)
            # pprint.pprint(self.to_reschedule)

        self.finalise_schedule()
        self.finalise_to_reschedule()
        print('Sums: ', self.get_task_sums())
        # self.output_tasks()
        # self.output_schedule()
        # print('final schedule')
        # pprint.pprint(self.schedule)

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
            # self.schedule[day]['data'].pop('days_to_due')

        sorted(self.schedule, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))
        # self.schedule[day]['data'].pop('difference')

    def finalise_to_reschedule(self):
        for task, hours in dict(self.to_reschedule).items():
            self.to_reschedule[int(task.strip('t'))
                               ] = self.to_reschedule.pop(task)

    def get_task_sums(self):
        total_areas = {}
        for info in self.schedule.values():
            for task, area in info['quots'].items():
                total_areas[task] = total_areas.get(task, 0) + area
        return total_areas

    def worked_tasks(self):
        # with open('tasks.json') as json_file:
        #     data = json.load(json_file)
        taskInfo = {}
        # for task, info in self.task_obj.items():
        for task, range in self.task_range.items():      # TODO why this
            taskInfo[int(f"{task.strip('t')}")] = [
                range[0], self.to_reschedule.get(task, 0)]
            # _info = info
            # _info[2] = self.task_range[task]
            # # _info[3] = getDateDelta(datetime.now()) + 1
            # _info[4] = self.to_reschedule.get(task, 0)
            # # print('final', task, info[2], _info[2])
            # taskInfo[task] = _info
        return taskInfo
        # self.task_obj.update(taskInfo)

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
        # dict with the tasks and how much hours there needs to be rescheduled
        to_reschedule = {}

        # iterating through the schedule
        for day, info in self.schedule.items():
            # getting the difference property,
            # +ve would mean free space and -ve would mean overflow
            # difference is perfect at 0
            diff = info['data']['difference']

            # day is skipped if there is no difference
            if diff >= 0:
                continue

            # five attempts to remove excess task hours
            i = 0               # to allow for small task hours which might not be able to provide

            while i < 5:
                # loop is done if the difference is made perfect
                if info['data']['difference'] >= 0:
                    break

                # `Priority` Percentage is calculated using the ratio of the due dates
                sum_of_dues = 0

                for task_id, days_to_due in info['data']['days_to_due'].items():
                    sum_of_dues = sum_of_dues + days_to_due

                # this percentage is used to calculate how much of the difference is contributed by which task
                # the program would `try` to remove these much amount from each task item that day
                portion_needed = {task: d/sum_of_dues * abs(info['data']['difference']) for task,
                                  d in info['data']['days_to_due'].items()}

                # gets the tasks in this day,
                # the list method is used to duplicate the quots obj as its size would be changed
                for task_id in list(info['quots']):
                    quote = info["quots"][task_id]      # quote of this task

                    # if there is enough hours to fullfill the requirement
                    if quote > portion_needed[task_id]:
                        # take out that much amount
                        info['quots'][task_id] = quote - \
                            portion_needed[task_id]

                        # add to to_reschedule dict
                        to_reschedule[task_id] = to_reschedule.get(task_id, 0) + \
                            portion_needed[task_id]

                        # difference and sum properties are updated
                        info['data']['difference'] = info['data']['difference'] + \
                            portion_needed[task_id]
                        info['data']['sum'] = info['data']['sum'] - \
                            portion_needed[task_id]

                    # if the required amount is perfectly equal to whats available
                    elif quote == portion_needed[task_id]:

                        # add to to_reschedule dict
                        to_reschedule[task_id] = to_reschedule.get(task_id, 0) + \
                            portion_needed[task_id]

                        # remove the task item from the day
                        info['quots'].pop(task_id)
                        info['data']['days_to_due'].pop(task_id)

                        # update difference and sum properties
                        info['data']['difference'] = info['data']['difference'] + \
                            portion_needed[task_id]
                        info['data']['sum'] = info['data']['sum'] - \
                            portion_needed[task_id]

                        # if the day happens to be the first day of a task
                        if day == self.task_range[task_id][0]:
                            self.task_range[task_id][0] += 1
                        # TODO whats this all about? also down
                        if day == self.task_range[task_id][1]:
                            self.task_range[task_id][1] -= 1

                    # if the available hours are less than what is requied
                    elif quote < portion_needed[task_id]:
                        # add the whole quote to_reschedule dict
                        to_reschedule[task_id] = to_reschedule.get(task_id, 0) + \
                            quote

                        # remove the task item from the day
                        info['quots'].pop(task_id)
                        info['data']['days_to_due'].pop(task_id)

                        # update the difference and sum properties
                        info['data']['difference'] += quote
                        info['data']['sum'] -= quote

                        # if the day happens to be the first day of a task
                        if day == self.task_range[task_id][0]:
                            self.task_range[task_id][0] += 1
                        if day == self.task_range[task_id][1]:
                            self.task_range[task_id][1] -= 1

                # the difference neednt be made perfect
                # because of the possibility of the requirement not fullfilling
                i += 1      # increment of the loop variable
                # the loop would happen 4 more times after which the residual is ignored

        return to_reschedule
