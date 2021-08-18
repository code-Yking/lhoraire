from datetime import datetime, timedelta, date as _d
import json
from json.decoder import JSONDecodeError
import math

D0 = _d(2000, 1, 1)   # this is the defualt reference point


def getDateDelta(date):

    if not isinstance(date, datetime) and not isinstance(date, _d):
        date = _d.fromisoformat(date)

    delta = date - D0
    return delta.days - 1               # - 1 to fix the final date as the date before due


def getDatefromDelta(delta):
    date = D0 + timedelta(days=(delta + 1))
    return date.strftime("%Y-%m-%d")


def isWeekend(date):
    date = datetime.fromisoformat(date)

    weekno = date.weekday()
    if weekno == 5:
        return 1
    elif weekno == 6:
        return 2
    else:
        return 0


def save(newtasks):
    to_save = {}
    for name, model in newtasks.items():
        to_save[model.id] = [model.k, model.gradient, [
            math.ceil(model.start_day), model.due_date-1], model.today, 0, name[1]]

    with open('tasks.json') as json_file:
        try:
            data = json.load(json_file)
            to_save.update(data)
        except JSONDecodeError:
            pass

    with open('tasks.json', 'w') as outfile:
        json.dump(to_save, outfile)
