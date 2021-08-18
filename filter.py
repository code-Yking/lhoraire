from .helpers import save
import json
from json.decoder import JSONDecodeError
import math
from .model import TaskModel
from .reposition import Reposition


def Filter(newtasks, oldtasks):

    newtasks = newtasks
    oldtasks = oldtasks

    to_reschedule = {}
    newtask_range = {}

    # produce the limits of the range of new tasks, according to the model
    # limits ie, first and last date that has this task as a tuple
    for model in newtasks.values():
        newtask_range[model.id] = (
            math.floor(model.start_day), model.due_date - 1)

# with open('tasks.json') as tasks_json:          # accessing old recorded tasks
    # try:
        # oldtasks = json.load(tasks_json)

        # produce the limits of the range of old tasks, according to the record
    oldtask_range = {task_id: tuple(task_info[2])
                     for task_id, task_info in oldtasks.items()}

    to_reschedule = {task_id: task_info[4]
                     for task_id, task_info in oldtasks.items()}

    # combine the two dictionaries with limits
    task_range = dict(oldtask_range, **newtask_range)

    # invert this dictionary
    # to make the limits the key and the task(s) that have this limit the values in a list
    inverted_tasks = {}

    for task_id, range in task_range.items():
        inverted_tasks[range] = inverted_tasks.get(
            range, []) + [task_id]

    # unique ranges (limits) of the tasks
    unique_ranges = list(inverted_tasks.keys())

    # union of these limits have to be found to group tasks that overlap and that can affect each other
    union_ranges = []
    grouped_tasks = []
    # each list of tasks inside grouped_tasks would belong within the limits present in union_ranges under same index

    # getting the union of the limits from unique_ranges and getting the respective tasks into the above lists
    for begin, end in sorted(unique_ranges):
        if union_ranges and union_ranges[-1][1] >= begin:
            index = union_ranges.index(union_ranges[-1])

            grouped_tasks[index] = grouped_tasks[index] + inverted_tasks.get(
                (begin, end))

            union_ranges[-1][1] = max(union_ranges[-1][1], end)
        else:
            union_ranges.append([begin, end])
            grouped_tasks.append(inverted_tasks.get((begin, end)))

    # lists are converted to tuples so they are hashable
    union_ranges = [(k, w) for k, w in unique_ranges]

    # producing a dictionary from both the lists
    union_range_tasks = dict(zip(union_ranges, grouped_tasks))

    # save(newtasks)

    # adding old tasks under the union of the limits of the new tasks into the list that is considered for reposition
    for range, tasks in union_range_tasks.items():
        for t in tasks:
            # if the group contain a new task
            if t in newtask_range.keys():
                # add all the other tasks in that group to
                for n in tasks:
                    if n not in newtask_range.keys():
                        if n in to_reschedule.keys():
                            to_reschedule.pop(n)
                        d = oldtasks[n][2][1]
                        w = oldtasks[n][0]
                        g = oldtasks[n][1]
                        da = oldtasks[n][3]
                        n = int(n.strip('t'))
                        task = TaskModel(id=n, due=d, work=w,
                                         week_day_work=6, days=0, gradient=g, today=da)
                        newtasks[(n, "", d)] = task

#     except JSONDecodeError:
#         # save(newtasks)
#         print(1)
    return newtasks
    # return Reposition(newtasks, (6, 10), (8, 14), to_reschedule)

# Filter()
