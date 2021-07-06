from datetime import datetime, timedelta

D0 = datetime(2000, 1, 1)   # this is the defualt reference point


def getDateDelta(date):

    if not isinstance(date, datetime):
        date = datetime.fromisoformat(date)

    delta = date - D0
    return delta.days


def getDatefromDelta(delta):
    date = D0 + timedelta(days=delta)
    return date.strftime("%Y/%m/%d")
