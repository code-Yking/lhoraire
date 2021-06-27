

class reposition:
    def __init__(self, cumulated, week_end_hours):
        self.cumulated = cumulated
        self.week_end_hours = week_end_hours

    # PLAN:
    # cream off from week days, before or after according to gradient
    # not a problem if no of days get reduced as this is max days needed.

    def fix_weekends(self):
        pass

    # PLAN:
    # Find difference where -ve,
    # use percent_of_dues and find which proportion of which to move out
    # use differences to find close days to relocate

    def fix_difference(self):
        pass
