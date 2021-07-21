import pandas
import matplotlib.pyplot as plt
import json
from json.decoder import JSONDecodeError

while True:
    with open('schedule.json') as schedule_json:
        try:
            schedule_dict = json.load(schedule_json)
        except JSONDecodeError:
            schedule_dict = {}

    with open('tasks.json') as tasks_json:
        try:
            tasks_dict = json.load(tasks_json)
            tasks = list(tasks_dict.keys())
        except JSONDecodeError:
            tasks_dict = {}

    all_areas = []
    index = []
    for day, info in schedule_dict.items():
        index.append(day)
        daily_areas = []
        for task in tasks:
            daily_areas.append(info['quots'].get(task, 0))
        all_areas.append(daily_areas)

    print(tasks)
    print(all_areas)
    print('Kill the terminal to cancel')

    df = pandas.DataFrame(all_areas, columns=tasks, index=index)
    df.plot.bar(stacked=True)
    plt.show()
