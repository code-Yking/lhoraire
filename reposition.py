from datetime import datetime, date as d_
import json
from json.decoder import JSONDecodeError
import math
import pprint
from .helpers import getDateDelta, getDatefromDelta, isWeekend
import operator


class Reposition:
    def __init__(self, newtasks, oldschedule, oldtasks, normal_work, max_work, to_reschedule={}):
        self.tasks = newtasks
        self.week_day_work = float(normal_work[0])
        self.week_end_work = float(normal_work[1])

        self.max_week_day_work = float(max_work[0])
        self.max_week_end_work = float(max_work[1])

        self.to_reschedule = to_reschedule
        self.task_range = {}

        self.task_obj = oldtasks
        # print('hi: ', self.task_obj)

        self.schedule = self.schedule_cumulation()
        self.oldschedule = oldschedule
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

    def set_old_schedule(self):
        oldschedule = self.oldschedule
        _o_schedule = dict(oldschedule)
        for day, data in _o_schedule.items():
            dayDelta = getDateDelta(day)
            oldschedule[dayDelta] = oldschedule.pop(day)
            sum_of_tasks = sum(data['quots'].values())
            # difference = 0
            if isWeekend(day):
                difference = self.week_end_work - \
                    sum_of_tasks if self.week_end_work - sum_of_tasks > 0 else 0
            else:
                difference = self.week_day_work - \
                    sum_of_tasks if self.week_day_work - sum_of_tasks > 0 else 0
            oldschedule[dayDelta]['data'] = {
                'difference': difference, 'sum': sum_of_tasks}
        # print('schedule')
        # pprint.pprint(self.schedule)
        # print('oldschedule')
        # pprint.pprint(oldschedule)
        oldschedule.update(self.schedule)
        self.schedule = oldschedule
        # print('updated schedule')
        # pprint.pprint(self.schedule)
        # self.schedule = schedule

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
            info['data']['difference'] = self.week_day_work - sum_of_area
            # info['data']['percent_of_work'] = percent_of_work

    # filling days with tasks according to their proximity to the deadline
    def day_filling(self, tasks, surface=False):
        day_filler_items = tasks
        # print('hello')
        # print(to_reschedule)
        for task in self.to_reschedule.keys():
            # list of days with this task
            filtered = list(filter(lambda x: task in x[1], day_filler_items))

            # divided into groups of five. First five high priority is filled before others
            segmented_filterd = [filtered[x:x+100]
                                 for x in range(0, len(filtered), 100)]
            # print(segmented_filterd)

            n = 1
            # for each group of 5 days in the segmented filtered list
            for group in segmented_filterd:

                # print(n)
                no_content = len(group)
                eq_gradient = 1/no_content
                denominator = sum(
                    [n*eq_gradient for n in range(1, no_content+1)])

                n += 1
                surface = surface
                # while there are free space in the group and while this task requires rescheduling
                while self.to_reschedule[task] > 0.001:

                    # has to be in here as the following rounds would need update
                    _to_reschedule = dict(self.to_reschedule)
                    # print(_to_reschedule, to_reschedule)

                    # for days in the group
                    for i, day in enumerate(group):
                        priority_index = no_content - i

                        required_area = _to_reschedule[task] * \
                            priority_index * eq_gradient / denominator

                        isWeekend = day[2]
                        # figuring the free space for this day
                        # if day is defined in the schedule
                        if day[3] in self.schedule:
                            # if it should NOT contribute towards excess hours
                            if not surface:
                                diff = self.schedule[day[3]
                                                     ]['data']['difference']
                            else:
                                # prioritizing weekends
                                if isWeekend:
                                    diff = 1 if self.schedule[day[3]]['data']['sum'] + \
                                        1 <= self.max_week_end_work else self.max_week_end_work - self.schedule[day]['data']['sum']
                                else:
                                    diff = 0.5 if self.schedule[day[3]]['data']['sum'] + \
                                        0.5 <= self.max_week_day_work else self.max_week_day_work - self.schedule[day]['data']['sum']
                        else:
                            if isWeekend:
                                diff = self.week_end_work
                            else:
                                diff = self.week_day_work

                        # no space in this day
                        # TODO check possibility for this, make sure no filled days are sent
                        if diff == 0:
                            break

                        # calculating available area, using `Proximity` Percentage
                        days_to_dues = day[5]
                        due = days_to_dues[day[1].index(task)]

                        available_area = 1/due / \
                            sum([1/n for n in days_to_dues]) * diff

                        if required_area <= available_area:
                            portion_used = required_area

                        elif required_area > available_area:
                            portion_used = available_area
                            # print('used', 2)

                        self.to_reschedule[task] = self.to_reschedule.get(
                            task) - portion_used
                        # print(day[3], task, required_area)
                        if day[3] not in self.schedule.keys():
                            self.schedule[day[3]] = {
                                'data': {'days_to_due': {}}, 'quots': {}}

                        self.schedule[day[3]]['data']['sum'] = self.schedule[day[3]]['data'].get(
                            'sum', 0) + portion_used
                        self.schedule[day[3]]['data']['difference'] = diff

                        if task in self.schedule[day[3]]['quots'].keys():
                            self.schedule[day[3]]['quots'][task] = self.schedule[day[3]
                                                                                 ]['quots'][task] + portion_used
                        else:
                            self.schedule[day[3]]['quots'][task] = portion_used
                            # print(dues)
                            if 'days_to_due' in self.schedule[day[3]]['data']:
                                self.schedule[day[3]
                                              ]['data']['days_to_due'][task] = due
                            else:
                                self.schedule[day[3]]['data']['days_to_due'] = {
                                    task: due}

                        if len(day[1]) == 0:
                            group.remove(day)

                    # print('after', _to_reschedule, self.to_reschedule)
                    # if no free space in the group, then break
                    group_diff = sum([self.schedule[day[3]]['data']
                                      ['difference'] for day in group])

                    if group_diff < 0.001:
                        break

                    surface = False

                # does not need to proceed if this task no longer needs to be rescheduled
                if self.to_reschedule[task] < 0.001:
                    break

                # pprint(schedule)
        # print('NEW')
        # pprint(schedule)
        # pprint(self.to_reschedule)

    # PLAN:
    # cream off from week days, before or after according to gradient
    # not a problem if no of days get reduced as this is max days needed.

    def reschedulable_days(self):
        # TODO fix this to disinclude empty items
        # array of days that contain details of tasks that can be resceduled into those days
        weekend_days, weekday_days = [], []

        # iterate through date and respective information of schedule tasks
        for day, info in self.schedule.items():
            date = getDatefromDelta(day)        # get string text
            # 0, 1, 2 => weekday, sat, sun. For easy ordering
            is_weekend = isWeekend(date)

            no_tasks = 0
            tasks = []          # tasks that can be resceduled into this day
            task_dues = []      # days to due of these tasks
            area = info['data']['sum']      # total time of these tasks

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

            # adding to the lists of days defined before
            if is_weekend:
                weekend_days.append(
                    [no_tasks, tasks, is_weekend, day, area, task_dues])
            else:
                weekday_days.append([no_tasks, tasks, 0, day, area, task_dues])

        return weekday_days, weekend_days

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
            if self.task_range[task][0] == getDateDelta(d_.today()) + 1:
                continue
            # if 5 less than start date of task is still more than tomorrow
            elif self.task_range[task][0] - 5 >= getDateDelta(d_.today()) + 1:
                lower_date = self.task_range[task][0] - 5
            # 5 less than start date of task is less than tomorrow, keep tommorow
            else:
                lower_date = getDateDelta(d_.today()) + 1

            # add the days from this lower date till the day before start date to precede_days_dict with tasks
            for n in range(lower_date, self.task_range[task][0]):
                precede_days_dict[n] = precede_days_dict.get(n, []) + [task]

            # update this task in the task_range property with lower date
            self.task_range[task][0] = lower_date

        # add to precede_days according to day_filling format
        for date, tasks in precede_days_dict.items():
            precede_days.append([len(tasks), tasks, isWeekend(getDatefromDelta(date)), date, 0, [
                                self.task_range[t][1] + 1 - date for t in tasks]])

        # print(precede_days)

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
                    pprint.pprint(self.schedule)
                    self.schedule[last_date]['data']['days_to_due'].pop(t)

                    self.to_reschedule[t] = self.to_reschedule.get(
                        t, 0) + area_rm

                    if last_date == self.task_range[t][0]:
                        self.task_range[t][0] = last_date + 1
                    # print(t, self.task_range[t])

    def rescheduling(self):
        self.free_final_days()
        # self.update_schedule()
        print('taskrange before reschedulable_days()', self.task_range)

        # difference between weekend and weekday works
        work_difference = self.week_end_work - \
            self.week_day_work       # no of extra hours for weekends

        # this will collect the days that can be rescheduled into
        weekday_days, weekend_days = self.reschedulable_days()

        print('taskrange after reschedulable_days()', self.task_range)

        # priority is given to sort the weekend days,
        # so that more data is added first to the ones with less pressure
        # Priority no 1: No of tasks done during that weekend day. Lesser would be above
        # Priority no 2: Total number of hours worked during the weekend day. Lesser would be above
        # Priority no 3: Saturday or Sunday. Saturday is favored over sunday
        weekend_days.sort(key=operator.itemgetter(0, 4, 2))
        weekday_days.sort(key=operator.itemgetter(0, 4))

        for weekend in weekend_days:
            self.schedule[weekend[3]]['data']['difference'] = self.schedule[weekend[3]
                                                                            ]['data']['difference'] + abs(work_difference)
        from .task_spread import day_filling_v2

        # combined = list(weekend_days + weekday_days)
        # schedule_ = self.schedule
        # to_resch_ = self.to_reschedule
        # print(self.to_reschedule)
        day_filling_v2(list(weekend_days + weekday_days), self.schedule, self.to_reschedule,
                       self.week_day_work, self.max_week_day_work, self.week_end_work, self.max_week_end_work)
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
        if work_difference > 0:
            # self.day_filling(weekend_days)
            pass

        # else tasks have to be removed from them and added to to_reschedule dict
        elif work_difference < 0:
            self.to_reschedule = {k: self.basic_reschedule().get(
                k, 0) + self.to_reschedule.get(k, 0) for k in set(self.to_reschedule)}
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

        # if there are tasks that still needs to be rescheduled
        while len(self.to_reschedule):
            # getting 5 days prior to the start date of the tasks
            extra_days = self.precedence()
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
                    # self.day_filling(weekend_days, True)
                    # self.day_filling(weekday_days, True)

                    day_filling_v2(list(weekend_days + weekday_days), self.schedule, self.to_reschedule,
                                   self.week_day_work, self.max_week_day_work, self.week_end_work, self.max_week_end_work, True)
                    # print('final')
                    # pprint.pprint(self.to_reschedule)
                    # pprint.pprint(self.schedule)

                    if _to_reschedule == self.to_reschedule:
                        break
                break

            # sorting the extra days preceeding the start date, filling the last first
            extra_days.sort(key=operator.itemgetter(3), reverse=True)
            day_filling_v2(extra_days, self.schedule, self.to_reschedule,
                           self.week_day_work, self.max_week_day_work, self.week_end_work, self.max_week_end_work, True)
            # self.day_filling(extra_days)

        self.finalise_schedule()
        print('Sums: ', self.get_task_sums())
        # self.output_tasks()
        # self.output_schedule()
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
                            self.task_range[task_id][0] = self.task_range[task_id][0] + 1
                        # TODO whats this all about? also down
                        elif day == self.task_range[task_id][1]:
                            self.task_range[task_id][1] = self.task_range[task_id][1] - 1

                    # if the available hours are less than what is requied
                    elif quote < portion_needed[task_id]:
                        # add the whole quote to_reschedule dict
                        to_reschedule[task_id] = to_reschedule.get(task_id, 0) + \
                            quote

                        # remove the task item from the day
                        info['quots'].pop(task_id)
                        info['data']['days_to_due'].pop(task_id)

                        # update the difference and sum properties
                        info['data']['difference'] = info['data']['difference'] + quote
                        info['data']['sum'] = info['data']['sum'] - quote

                        # if the day happens to be the first day of a task
                        if day == self.task_range[task_id][0]:
                            self.task_range[task_id][0] = self.task_range[task_id][0] + 1
                        elif day == self.task_range[task_id][1]:
                            self.task_range[task_id][1] = self.task_range[task_id][1] - 1

                # the difference neednt be made perfect
                # because of the possibility of the requirement not fullfilling
                i += 1      # increment of the loop variable
                # the loop would happen 4 more times after which the residual is ignored

        return to_reschedule
