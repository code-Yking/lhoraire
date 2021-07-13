from datetime import datetime, timedelta

D0 = datetime(2000, 1, 1)   # this is the defualt reference point


def getDateDelta(date):

    if not isinstance(date, datetime):
        date = datetime.fromisoformat(date)

    delta = date - D0
    return delta.days - 1               # - 1 to fix the final date as the date before due


def getDatefromDelta(delta):
    date = D0 + timedelta(days=delta)
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
