from helpers import save
import json
from json.decoder import JSONDecodeError
import math
from model import TaskModel
from reposition import Reposition


class Filter:
    def __init__(self, newtasks):
        newtasks = newtasks
        to_reschedule = {}
        newtask_range = {}

        for name, model in newtasks.items():
            newtask_range[model.id] = (
                math.ceil(model.start_day), model.due_date-1)

        with open('tasks.json') as tasks_json:
            try:
                oldtasks = json.load(tasks_json)

                oldtask_range = {task_id: tuple(task_info[2])
                                 for task_id, task_info in oldtasks.items()}

                to_reschedule = {task_id: task_info[4]
                                 for task_id, task_info in oldtasks.items()}
                # print(to_reschedule)
                # print('hello')
                # input()
                task_range = dict(oldtask_range, **newtask_range)
                # print(oldtask_range)
                inverted_tasks = {}

                for task_id, range in task_range.items():
                    inverted_tasks[range] = inverted_tasks.get(
                        range, []) + [task_id]

                a = list(inverted_tasks.keys())
                b = []

                c = []

                for begin, end in sorted(a):
                    if b and b[-1][1] >= begin:
                        # print(tuple(b[-1]), (begin, end))
                        index = b.index(b[-1])

                        c[index] = c[index] + inverted_tasks.get(
                            (begin, end))

                        b[-1][1] = max(b[-1][1], end)
                    else:
                        b.append([begin, end])
                        c.append(inverted_tasks.get((begin, end)))

                b = [(k, w) for k, w in a]

                b = dict(zip(b, c))

                save(newtasks)

                for range, tasks in b.items():
                    for t in tasks:
                        if t in newtask_range.keys():
                            # theres a new guy
                            for n in tasks:
                                if n not in newtask_range.keys():
                                    # print(tasks, to_reschedule)
                                    if n in to_reschedule.keys():
                                        to_reschedule.pop(n)
                                    d = oldtasks[n][2][1]+1
                                    w = oldtasks[n][0]
                                    g = oldtasks[n][1]
                                    da = oldtasks[n][3]
                                    n = n.strip('t')
                                    task = TaskModel(id=n, due=d, work=w,
                                                     week_day_work=6, days=0, gradient=g, today=da)
                                    newtasks[(n, "", d)] = task

            except JSONDecodeError:
                save(newtasks)
                print(1)

        Reposition(newtasks, (6, 10), (8, 14), to_reschedule)

# Filter()
