from datetime import timedelta




class TimeDelta_Calculation:
    def __init__(self):
        string_test = self.string_to_td("40:54:23")
        print("DateTime =", string_test)
        hour_test = self.td_to_hour(string_test)
        print("Hours =", hour_test)
        return_td_test = self.hour_to_td_val(hour_test)
        print("back to td = ", return_td_test)

    def string_to_td(self, string):
        h, m, s = string.split(':')
        return timedelta(hours=int(h), minutes=int(m), seconds=int(s))

    def list_to_td(self, td_list):
        td_sum = sum(td_list, timedelta(0))
        return td_sum

    def td_to_hour(self, td_val):

        total_seconds = td_val.total_seconds()
        seconds_in_hour = 60 * 60
        total_hours = round((total_seconds / seconds_in_hour), 2)
        return total_hours

    def hour_to_td_val(self, total_hours):
        td_val = timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=total_hours, weeks=0)
        return td_val

run = TimeDelta_Calculation()
run.__init__()