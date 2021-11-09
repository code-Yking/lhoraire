from datetime import datetime, date as d_
import json
from json.decoder import JSONDecodeError
import math

from .helpers import getDateDelta, getDatefromDelta, isWeekend
import operator
import copy

RESCHEDULE_LIMIT = 0


class Reposition:
    def __init__(
        self,
        newtasks,
        oldschedule,
        oldtasks,
        normal_work,
        max_work,
        extra_hours,
        localdate,
    ):
        self.tasks = newtasks
        self.week_day_work = float(normal_work[0])
        self.week_end_work = float(normal_work[1])

        self.max_week_day_work = float(max_work[0])
        self.max_week_end_work = float(max_work[1])

        self.extra_hours = dict(extra_hours)
        self.task_range = {}
        self.task_total = {}

        self.task_obj = oldtasks

        self.today = localdate
        self.to_reschedule = {}

        self.schedule = self.schedule_cumulation()
        self.oldschedule = oldschedule

        self.process_data()

        self.to_reschedule = {
            t: k + self.to_reschedule.get(t, 0)
            for t, k in self.basic_reschedule().items()
        }

        self.rescheduling()




    def set_old_schedule(self):

        self.oldschedule.update(self.schedule)
        self.schedule = self.oldschedule


    # getting the initial schedule from the tasks

    def schedule_cumulation(self):
        schedule_cumulation = {}

        for task_info, task_object in self.tasks.items():
            days = task_object.generate_list()

            task_id = f"t{task_info[0]}"
            due_date = task_object.due_date
            self.task_total[task_id] = task_object.work

            for day in days:
                date_delta = day[0]
                date = day[0]
                # date = getDatefromDelta(date_delta)
                task_area = day[1]
                # adding to the schedule only if the task that day is greater
                # than 20 mins
                if task_area >= 20 / 60:
                    if date in schedule_cumulation:
                        schedule_cumulation[date]["quots"][task_id] = task_area
                        schedule_cumulation[date]["data"]["days_to_due"][
                            task_id
                        ] = (due_date - date)
                    else:
                        schedule_cumulation[date] = {
                            "quots": {task_id: task_area},
                            "data": {
                                "days_to_due": {task_id: due_date - date_delta}
                            },
                        }
                else:
                    self.to_reschedule[task_id] = (
                        self.to_reschedule.get(task_id, 0) + task_area
                    )

            # setting the task ranges
            start_date = math.floor(task_object.start_day)
            self.task_range[task_id] = [start_date, due_date - 1]


        return schedule_cumulation

    def process_data(self):
        # schedule_cumulation = cumulation

        for day, info in self.schedule.items():
            sum_of_area = 0

            for task_id, quote in info["quots"].items():
                sum_of_area = sum_of_area + quote

            info["data"]["sum"] = sum_of_area
            if isWeekend(getDatefromDelta(day)):
                info["data"]["difference"] = self.week_end_work - sum_of_area
            else:
                info["data"]["difference"] = self.week_day_work - sum_of_area
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
        while n < 10:

            # For every task that has to be rescheduled
            for task in list(self.to_reschedule.keys()):

                # list of days with this task
                filtered = list(
                    filter(lambda x: task in x[1], day_filler_items)
                )

                # divided into groups of five. First five high priority is
                # filled before others
                segmented_filterd = list(
                    [filtered[x: x + 5] for x in range(0, len(filtered), 5)]
                )


                # FOR EACH GROUP of 5 in the filtered list of lists
                # this is so that extra space is divided among groups
                # instead of days
                for group_index, group in enumerate(segmented_filterd):

                    while len(group):
                        # forming ratio formula
                        no_content = len(group)  # no of content
                        eq_gradient = (
                            1 / no_content
                        )  # gradient of ratio formula
                        denominator = sum(
                            [n * eq_gradient for n in range(1, no_content + 1)]
                        )

                        # true surface
                        surface = true_surface


                        # area which are really small that has to be skipped
                        group_excluded_area = 0

                        # initial group difference - cummulated free
                        # space in the group
                        group_diff = math.nan

                        # unchanging reschedule copy, values from which are
                        # used for the areas in this group has to be
                        # in here as the following rounds would need update
                        _to_reschedule = dict(self.to_reschedule)


                        # EACH DAY in this group, enumerated and duplicated
                        # as items need to be deleted
                        for i, day in enumerate(list(group)):

                            # gonna be there in the list
                            list_i = day_filler_items.index(day)
                            task_index = day[1].index(task)
                            day_updated = (
                                False  # boolean to see if the day gets updated
                            )

                            days_final = (
                                False  # if day has reached its MAX limit
                            )
                            priority_index = (
                                no_content - i
                            )  # priority for the ratio formula

                            # calculating required area off this day.
                            # to_reschedule data from the static group copy
                            # is used so that the real total to_reschedule
                            # hours can be filled in this group
                            # and the real to_reschedule can be edited as we go
                            required_area = (
                                _to_reschedule[task]
                                * priority_index
                                * eq_gradient
                                / denominator
                            )

                            # and remove item from list
                            isWeekend = day[2]

                            # figuring the free space for this day
                            # if day is defined in the schedule
                            if day[3] in self.schedule:
                                # difference from the schedule
                                diff = self.schedule[day[3]]["data"][
                                    "difference"
                                ]

                                # if there is no difference or
                                # if it is really small
                                if diff <= 0.001 and surface:

                                    # if there are extra hours allocated
                                    extra_hours = 0
                                    if day[3] in self.extra_hours:
                                        extra_hours = float(
                                            self.extra_hours.pop(day[3])
                                        )

                                    # using maximum hours with any extra hours
                                    # as difference
                                    if isWeekend:
                                        diff = (
                                            self.max_week_end_work
                                            - self.schedule[day[3]]["data"][
                                                "sum"
                                            ]
                                            + extra_hours
                                        )
                                        days_final = True
                                    else:
                                        diff = (
                                            self.max_week_day_work
                                            - self.schedule[day[3]]["data"][
                                                "sum"
                                            ]
                                            + extra_hours
                                        )
                                        days_final = True

                            # day is not in the schedule,
                            # should be a new precedence day, gets defaults
                            # will be added to the schedule at the end
                            else:
                                if isWeekend:
                                    diff = self.week_end_work
                                else:
                                    diff = self.week_day_work

                            # STILL no space in this day; day is removed and
                            # skipped
                            # make sure no filled days are sent
                            if diff < 0.001:
                                continue

                            # calculating available area,
                            # using `Proximity` Percentage
                            days_to_dues = day[5]
                            due = days_to_dues[day[1].index(task)]

                            # amount of area that can be added
                            # with this given diff and other tasks in this day
                            available_area = (
                                1
                                / due
                                / sum([1 / n for n in days_to_dues])
                                * diff
                            )


                            # assigning portion that is going to be used
                            # according to the free and requierd area
                            if required_area < available_area:
                                portion_used = required_area

                            elif required_area >= available_area:
                                portion_used = available_area
                                # day is removed from the group as it is filled
                                # if day in group:
                                # removal wouldn't affect other day
                                # calculations as constants outside loop
                                group.remove(day)


                            # if the portion to be used has less than
                            # 20 mins of work
                            if portion_used + self.schedule.get(
                                day[3], {}
                            ).get("quots", {}).get(task, 0) < float(20 / 60):

                                # day is removed from group as this would
                                if day in group:
                                    if group[-1] == day:
                                        group.remove(day)
                                        if (
                                            len(segmented_filterd)
                                            > group_index + 2
                                        ):
                                            segmented_filterd[
                                                group_index + 1
                                            ].insert(0, day)
                                continue

                            # update info
                            self.to_reschedule[task] = round(
                                self.to_reschedule.get(task) - portion_used, 5
                            )

                            if day[3] not in self.schedule.keys():
                                self.schedule[day[3]] = {
                                    "data": {"days_to_due": {}},
                                    "quots": {},
                                }

                            self.schedule[day[3]]["data"]["sum"] = (
                                self.schedule[day[3]]["data"].get("sum", 0)
                                + portion_used
                            )
                            self.schedule[day[3]]["data"]["difference"] = (
                                diff - portion_used
                            )

                            # remove day from group
                            if day in group:
                                group.remove(day)

                            # prevents day from being reiterated if no space
                            if diff - portion_used <= 0.001:

                                day_filler_items.remove(day)
                                day_updated = True

                                day_item = list(
                                    filter(
                                        lambda x: x[3] == day[3],
                                        init_day_filler_items,
                                    )
                                )

                                if day_item:
                                    init_day_filler_items.remove(
                                        list(
                                            filter(
                                                lambda x: x[3] == day[3],
                                                init_day_filler_items,
                                            )
                                        )[0]
                                    )

                                    day_updated = True

                            if task in self.schedule[day[3]]["quots"].keys():
                                self.schedule[day[3]]["quots"][task] = (
                                    self.schedule[day[3]]["quots"][task]
                                    + portion_used
                                )
                            else:
                                self.schedule[day[3]]["quots"][
                                    task
                                ] = portion_used

                                if (
                                    "days_to_due"
                                    in self.schedule[day[3]]["data"]
                                ):
                                    self.schedule[day[3]]["data"][
                                        "days_to_due"
                                    ][task] = due
                                else:
                                    self.schedule[day[3]]["data"][
                                        "days_to_due"
                                    ] = {task: due}

                            if not day_updated:
                                day_filler_items[list_i][0] -= 1
                                day_filler_items[list_i][1].pop(task_index)
                                day_filler_items[list_i][5].pop(task_index)


                        # if no free space in the group, then break
                        group_diff = sum(
                            [
                                self.schedule.get(day[3], {})
                                .get("data", {})
                                .get("difference", 0)
                                for day in group
                            ]
                        )

                        # does not need to proceed
                        # if this task no longer needs to be rescheduled
                        if self.to_reschedule[task] <= 0.001:
                            break

                    if self.to_reschedule[task] <= 0.001:
                        break

                # if very less hours remain to be rescheduled.
                if self.to_reschedule[task] <= 0.001:
                    # removes day from to_reschedule
                    self.to_reschedule.pop(task)

                    # removes day
                    # from day_filler_items and init_day_filler_items
                    # this will prevent reiteration of this task

                    # from init_day_filler_items
                    for day in init_day_filler_items:
                        if task in day[1]:
                            # if day filler item has only one day,
                            # removes the item
                            if day[0] == 1:

                                init_day_filler_items.remove(day)
                                # if day in day_filler_items:
                                #     day_filler_items.remove(day)
                            else:
                                # else edits the day filler items

                                in_item_i = init_day_filler_items.index(day)
                                init_day_filler_items[in_item_i][0] -= 1
                                index = init_day_filler_items[in_item_i][
                                    1
                                ].index(task)
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
                                index = day_filler_items[item_i][1].index(task)
                                day_filler_items[item_i][1].pop(index)
                                day_filler_items[item_i][5].pop(index)

            n += 1


            if not len(self.to_reschedule) or not len(day_filler_items):
                break

            day_filler_items = list(
                filter(
                    lambda x: any(
                        k in self.to_reschedule.keys() for k in x[1]
                    ),
                    copy.deepcopy(init_day_filler_items),
                )
            )
            # day_filler_items = copy.deepcopy(init_day_filler_items)

    # produce day filler items for filling in days that are
    # already in the schedule

    def reschedulable_days(self, surface=False):
        # array of days that contain details of tasks that can be
        # resceduled into those days
        weekend_days, weekday_days = [], []

        # iterate through date and respective information of schedule tasks
        for day, info in self.schedule.items():

            area = info["data"]["sum"]  # total time of these tasks
            date = getDatefromDelta(day)  # get string text
            is_weekend = isWeekend(date)

            if not surface:
                if info["data"]["difference"] <= 0.001:
                    continue
            else:
                if is_weekend:
                    if (
                        self.max_week_end_work
                        + float(self.extra_hours.get(day, 0))
                        - area
                        <= 0.001
                    ):
                        continue
                    else:
                        info["data"]["difference"] = (
                            self.max_week_end_work
                            + float(self.extra_hours.get(day, 0))
                            - area
                        )
                else:
                    if (
                        self.max_week_day_work
                        + float(self.extra_hours.get(day, 0))
                        - area
                        <= 0.001
                    ):
                        continue
                    else:
                        info["data"]["difference"] = (
                            self.max_week_day_work
                            + float(self.extra_hours.get(day, 0))
                            - area
                        )

            # 0, 1, 2 => weekday, sat, sun. For easy ordering

            no_tasks = 0
            tasks = []  # tasks that can be resceduled into this day
            task_dues = []  # days to due of these tasks

            # iterate through all the tasks in the task_range property
            for task, day_range in self.task_range.items():
                # see if this day is in the range of any tasks and
                # if those task needs to be reschedulable
                if (
                    int(day) in range(int(day_range[0]), int(day_range[1]) + 1)
                    and task in self.to_reschedule.keys()
                ):
                    # if task has value of 0 in to_reschedule
                    if self.to_reschedule[task] == 0:
                        continue

                    # add to the lists about tasks defined before
                    no_tasks = no_tasks + 1
                    tasks.append(task)
                    task_dues.append(int(day_range[1]) - day + 1)

            if not len(tasks):
                continue

            # adding to the lists of days defined before
            if is_weekend:
                weekend_days.append(
                    [no_tasks, tasks, is_weekend, day, area, task_dues]
                )
            else:
                weekday_days.append([no_tasks, tasks, 0, day, area, task_dues])

        return weekday_days, weekend_days

    # Produces day filler items for the purpose of precedence.
    def precedence(self):
        precede_days = []

        # dict with days and the tasks that can be done on these days
        precede_days_dict = {}



        # iterate through the tasks that have hours to be rescheduled
        for task, hours in self.to_reschedule.items():
            # if no hours to be rescheduled, continue
            if hours == 0:
                continue

            # if start date of the task is tomorrow, continue
            if self.task_range[task][0] == getDateDelta(self.today) + 1:
                continue
            # if 5 less than start date of task is still more than tomorrow
            elif self.task_range[task][0] - 5 >= getDateDelta(self.today) + 1:
                lower_date = self.task_range[task][0] - 5
            # 5 less than start date of task is less than tomorrow,
            # keep tommorow
            else:
                lower_date = getDateDelta(self.today) + 1

            # add the days from this lower date till the day before
            # start date to precede_days_dict with tasks
            for n in range(lower_date, self.task_range[task][0]):
                precede_days_dict[n] = precede_days_dict.get(n, []) + [task]

            # update this task in the task_range property with lower date
            self.task_range[task][0] = lower_date

        # add to precede_days according to day_filling format
        for date, tasks in precede_days_dict.items():

            if (
                self.schedule.get(date, {})
                .get("data", {})
                .get("difference", 1)
                <= 0.001
            ):
                continue

            precede_days.append(
                [
                    len(tasks),
                    tasks,
                    isWeekend(getDatefromDelta(date)),
                    date,
                    0,
                    [self.task_range[t][1] + 1 - date for t in tasks],
                ]
            )




        return precede_days

    # free days that are before the due date of a task from other tasks
    def free_final_days(self):
        for task, range in self.task_range.items():
            last_date = range[1]

            for t in dict(self.schedule[last_date]["quots"]):
                if t != task and last_date != self.task_range[t][1]:
                    area_rm = self.schedule[last_date]["quots"][t]
                    self.schedule[last_date]["data"]["sum"] = (
                        self.schedule[last_date]["data"]["sum"] - area_rm
                    )
                    self.schedule[last_date]["data"]["difference"] = (
                        self.schedule[last_date]["data"]["difference"]
                        + area_rm
                    )
                    self.schedule[last_date]["quots"].pop(t)

                    self.schedule[last_date]["data"]["days_to_due"].pop(t)

                    self.to_reschedule[t] = (
                        self.to_reschedule.get(t, 0) + area_rm
                    )

                    if last_date == self.task_range[t][0]:
                        self.task_range[t][0] = last_date + 1


    def rescheduling(self):
        self.free_final_days()
        # self.update_schedule()

        # difference between weekend and weekday works
        work_difference = (
            self.week_end_work - self.week_day_work
        )  # no of extra hours for weekends


        # this will collect the days that can be rescheduled into
        weekday_days, weekend_days = self.reschedulable_days()

        # priority is given to sort the weekend days,
        # so that more data is added first to the ones with less pressure
        # Priority no 1: No of tasks done during that weekend day.
        # Lesser would be above
        # Priority no 2: Total number of hours worked during the weekend day.
        # Lesser would be above
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

        self.day_filling(list(weekend_days + weekday_days))

        for task, hours in dict(self.to_reschedule).items():
            if hours < 0.001:
                self.to_reschedule.pop(task)



        self.set_old_schedule()


        precedence_available = True

        # if there are tasks that still needs to be rescheduled
        while len(self.to_reschedule):
            # getting 5 days prior to the start date of the tasks
            if precedence_available:
                extra_days = self.precedence()
                # if reached today, can't get more room from earlier days
                if len(extra_days):
                    # sorting the extra days preceeding the start date,
                    # filling the last first
                    extra_days.sort(key=operator.itemgetter(3), reverse=True)
                    self.day_filling(extra_days)
                else:
                    precedence_available = False

            # get ALL week days and weekend days that have the tasks
            weekday_days, weekend_days = self.reschedulable_days(True)

            # sort these days such that earlier comes first
            # weekend_days.sort(key=operator.itemgetter(3), reverse=True)
            weekend_days.sort(key=operator.itemgetter(0, 4, 2))
            # weekday_days.sort(key=operator.itemgetter(3), reverse=True)
            weekday_days.sort(key=operator.itemgetter(0, 4))

            self.day_filling(
                list(weekend_days + weekday_days), True, precedence_available
            )

            if not precedence_available:

                break

        self.finalise_schedule()
        self.finalise_to_reschedule()


    def finalise_schedule(self):
        _schedule = dict(self.schedule)
        for dayDelta, info in _schedule.items():
            day = getDatefromDelta(int(dayDelta))
            self.schedule[day] = self.schedule.pop(dayDelta)
            # self.schedule[day]['data'].pop('days_to_due')

        sorted(self.schedule, key=lambda x: datetime.strptime(x, "%Y-%m-%d"))
        # self.schedule[day]['data'].pop('difference')

    def finalise_to_reschedule(self):
        for task, hours in dict(self.to_reschedule).items():
            self.to_reschedule[int(task.strip("t"))] = self.to_reschedule.pop(
                task
            )

    def get_task_sums(self):
        total_areas = {}
        for info in self.schedule.values():
            for task, area in info["quots"].items():
                total_areas[task] = total_areas.get(task, 0) + area
        return total_areas

    def worked_tasks(self):
        taskInfo = {}
        for task, range in self.task_range.items(): 
            taskInfo[int(f"{task.strip('t')}")] = [
                range[0],
                self.to_reschedule.get(task, 0),
            ]
        return taskInfo


    # PLAN:
    # Find difference where -ve,
    # use percent_of_dues and find which proportion of which to move out
    # use differences to find close days to relocate

    def basic_reschedule(self):
        # dict with the tasks and how much hours there needs to be rescheduled
        to_reschedule = {}

        # iterating through the schedule
        for day, info in self.schedule.items():
            # getting the difference property,
            # +ve would mean free space and -ve would mean overflow
            # difference is perfect at 0
            diff = info["data"]["difference"]

            # day is skipped if there is no difference
            if diff >= 0:
                continue

            # five attempts to remove excess task hours
            i = 0
            # to allow for small task hours which might not be able to provide

            while i < 5:
                # loop is done if the difference is made perfect
                if info["data"]["difference"] >= 0:
                    break

                # `Priority` Percentage is calculated
                # using the ratio of the due dates
                sum_of_dues = 0

                for task_id, days_to_due in info["data"][
                    "days_to_due"
                ].items():
                    sum_of_dues = sum_of_dues + days_to_due

                # this percentage is used to calculate
                # how much of the difference is contributed by which task
                # the program would `try` to remove
                # these much amount from each task item that day
                portion_needed = {
                    task: d / sum_of_dues * abs(info["data"]["difference"])
                    for task, d in info["data"]["days_to_due"].items()
                }

                # gets the tasks in this day,
                # the list method is used to duplicate
                # the quots obj as its size would be changed
                for task_id in list(info["quots"]):
                    quote = info["quots"][task_id]  # quote of this task

                    # if there is enough hours to fullfill the requirement
                    if (
                        quote > portion_needed[task_id]
                        and quote - portion_needed[task_id] >= 20 / 60
                    ):
                        # take out that much amount
                        info["quots"][task_id] = (
                            quote - portion_needed[task_id]
                        )

                        # add to to_reschedule dict
                        to_reschedule[task_id] = (
                            to_reschedule.get(task_id, 0)
                            + portion_needed[task_id]
                        )

                        # difference and sum properties are updated
                        info["data"]["difference"] = (
                            info["data"]["difference"]
                            + portion_needed[task_id]
                        )
                        info["data"]["sum"] = (
                            info["data"]["sum"] - portion_needed[task_id]
                        )

                    # if the required amount is
                    # perfectly equal to whats available
                    elif (
                        quote == portion_needed[task_id]
                        or quote - portion_needed[task_id] < 20 / 60
                    ):

                        # add to to_reschedule dict
                        to_reschedule[task_id] = (
                            to_reschedule.get(task_id, 0)
                            + portion_needed[task_id]
                        )

                        # remove the task item from the day
                        info["quots"].pop(task_id)
                        info["data"]["days_to_due"].pop(task_id)

                        # update difference and sum properties
                        info["data"]["difference"] = (
                            info["data"]["difference"]
                            + portion_needed[task_id]
                        )
                        info["data"]["sum"] = (
                            info["data"]["sum"] - portion_needed[task_id]
                        )

                        # if the day happens to be the first day of a task
                        if day == self.task_range[task_id][0]:
                            self.task_range[task_id][0] += 1
                        if day == self.task_range[task_id][1]:
                            self.task_range[task_id][1] -= 1

                    # if the available hours are less than what is requied
                    elif quote < portion_needed[task_id]:
                        # add the whole quote to_reschedule dict
                        to_reschedule[task_id] = (
                            to_reschedule.get(task_id, 0) + quote
                        )

                        # remove the task item from the day
                        info["quots"].pop(task_id)
                        info["data"]["days_to_due"].pop(task_id)

                        # update the difference and sum properties
                        info["data"]["difference"] += quote
                        info["data"]["sum"] -= quote

                        # if the day happens to be the first day of a task
                        if day == self.task_range[task_id][0]:
                            self.task_range[task_id][0] += 1
                        if day == self.task_range[task_id][1]:
                            self.task_range[task_id][1] -= 1

                # the difference neednt be made perfect
                # because of the possibility of the requirement not fullfilling
                i += 1  # increment of the loop variable
                # the loop would happen 4 more times after
                # which the residual is ignored

        return to_reschedule

# these functions are never called
def update_schedule(self):
        with open("schedule.json") as schedule_json:
            try:
                schedule = json.load(schedule_json)
            except JSONDecodeError:
                schedule = {}
        _schedule = dict(schedule)
        for day in _schedule.keys():
            dayDelta = getDateDelta(day)
            schedule[dayDelta] = schedule.pop(day)

        schedule.update(self.schedule)
        self.schedule = schedule
        
def output_schedule(self):
    with open("schedule.json") as schedule_json:
        try:
            schedule = json.load(schedule_json)
        except JSONDecodeError:
            schedule = {}

    schedule.update(self.schedule)

    with open("schedule.json", "w") as outfile:
        json.dump(schedule, outfile, indent=4, sort_keys=True)