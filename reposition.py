import pprint


class Reposition:
    def __init__(self, tasks, week_day_work, week_end_work):
        self.tasks = tasks
        self.week_day_work = week_day_work
        self.week_end_work = week_end_work

        sched_cumul_data = self.schedule_cumulation()

        processed = self.process_data(sched_cumul_data)
        pprint.pprint(processed)

    def schedule_cumulation(self):
        schedule_cumulation = {}
        for task_info, task_object in self.tasks.items():
            days = task_object.generate_list()

            for day in days:
                date = day[0]
                task_area = day[1]

                task_id = f't{task_info[0]}'
                due_date = task_info[2]

                if date in schedule_cumulation:
                    schedule_cumulation[date]['quots'].append(
                        (task_area, task_id)
                    )
                    schedule_cumulation[date]['data']['days_to_due'][task_id] = due_date - date + 1
                else:
                    schedule_cumulation[date] = {
                        'quots': [(task_area, task_id)],
                        'data': {
                            'days_to_due': {
                                task_id: due_date - date + 1
                            }
                        }
                    }
        pprint.pprint(schedule_cumulation)
        return schedule_cumulation

    def process_data(self, cumulation):
        schedule_cumulation = cumulation
        for day, info in schedule_cumulation.items():
            sum_of_area = 0

            for task_info in info['quots']:
                sum_of_area = sum_of_area + task_info[0]

            sum_of_dues = 0
            percent_of_work = {task[1]: task[0] /
                               sum_of_area for task in info['quots']}

            for task_info, days_to_due in info['data']['days_to_due'].items():
                sum_of_dues = sum_of_dues + days_to_due

            percent_of_dues = {task: d/sum_of_dues for task,
                               d in info['data']['days_to_due'].items()}

            info['data']['sum'] = sum_of_area
            info['data']['difference'] = self.week_day_work - sum_of_area
            info['data']['percent_of_work'] = percent_of_work
            info['data']['percent_of_dues'] = percent_of_dues

        return schedule_cumulation

    # PLAN:
    # cream off from week days, before or after according to gradient
    # not a problem if no of days get reduced as this is max days needed.

    def fix_weekends(self):
        work_difference = self.week_end_work - self.week_day_work
        if work_difference > 0:
            pass

        if work_difference < 0:
            pass

    # PLAN:
    # Find difference where -ve,
    # use percent_of_dues and find which proportion of which to move out
    # use differences to find close days to relocate

    def fix_difference(self):
        pass
