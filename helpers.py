from datetime import datetime


def getDateDelta(date):
    D0 = datetime(2000, 1, 1)   # this is the defualt reference point

    if not isinstance(date, datetime):
        date = datetime.fromisoformat(date)

    delta = date - D0
    return delta.days
