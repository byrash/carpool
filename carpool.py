from datetime import date, datetime, timedelta
import icalendar
from icalendar import vDDDTypes


class Queue:
    def __init__(self):
        self.items = []

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        if self.is_empty():
            return None
        return self.items.pop(0)

    def is_empty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)

    def clean(self):
        sequence = []
        for key, value in days_to_drivers.items():
            if key not in ["Friday", "Saturday", "Sunday"]:
                sequence.append(value)
        i = 0
        while i < len(self.items):
            if self.items[i:i+len(sequence)] == sequence:
                del self.items[i:i+len(sequence)]
            else:
                i += 1


days_to_drivers = {
    "Monday": "Bh",
    "Tuesday": "Sh",
    "Wednesday": "Ya",
    "Thursday": "Sa",
    "Friday": "TODO",
    "Saturday": "~~~~~~~~~~",
    "Sunday": "~~~~~~~~~~~"
}


class CarpoolSchedule:
    def __init__(self, ical_file_path):
        self.missed_roaster = Queue()
        self.regular_friday_roaster = Queue()
        self.holidays = self.read_holidays_from_ical(ical_file_path)
        self.assign_regular_friday()

    def get_value_by_slice(self, slice_key):
        for key in days_to_drivers:
            if slice_key == key:
                return days_to_drivers[key]
        return None

    def assign_roaster(self):
        today = datetime.today()
        for i in range(100):
            self.missed_roaster.clean()
            current_date = today + timedelta(days=i)
            day = self.get_weekday(current_date.strftime("%Y-%m-%d"))
            if current_date.strftime("%Y-%m-%d") > self.last_day_of_school:
                continue
            if current_date.strftime("%Y-%m-%d") in self.holidays:
                if day == "Friday":
                    self.missed_roaster.enqueue(
                        self.regular_friday_roaster.dequeue())
                else:
                    self.missed_roaster.enqueue(
                        self.get_value_by_slice(day))
                continue

            if day == "Sunday" or day == "Saturday":
                print()
                continue

            if day == "Friday":
                if self.missed_roaster.size() > 0:
                    print(current_date, day, '-->  ',
                          self.missed_roaster.dequeue())
                else:
                    print(current_date, day, '-->  ',
                          self.regular_friday_roaster.dequeue())
            else:
                print(current_date, day, '-->  ', self.get_value_by_slice(day))

    def get_weekday(self, calendar_date):
        # Parse the calendar date string into a datetime object
        date_obj = datetime.strptime(calendar_date, '%Y-%m-%d')
        # Get the weekday index (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)
        weekday_index = date_obj.weekday()
        # Return the name of the weekday
        weekdays = ["Monday", "Tuesday", "Wednesday",
                    "Thursday", "Friday", "Saturday", "Sunday"]
        return weekdays[weekday_index]

    def assign_regular_friday(self):
        for i in range(50):
            for key, value in days_to_drivers.items():
                if key not in ["Friday", "Saturday", "Sunday"]:
                    self.regular_friday_roaster.enqueue(value)

    def read_holidays_from_ical(self, ical_file_path):
        holidays = []

        with open(ical_file_path, 'rb') as f:
            cal_data = f.read()
        cal = icalendar.Calendar.from_ical(cal_data)

        for event in cal.walk('VEVENT'):
            # print(event.get('DTSTART').dt, '\n')
            summary = event.get('summary')
            if summary == "Teacher Workday" or summary == "Holiday- No School" or summary == "Spring Break":
                start_date = event.get('DTSTART').dt
                # holidays.append(start_date)
                if event.get('DTEND') is not None:
                    end_date = event.get('DTEND').dt
                    while start_date < end_date:
                        holidays.append(start_date.strftime("%Y-%m-%d"))
                        start_date += timedelta(days=1)
                elif event.get('DURATION') is not None:
                    duration = vDDDTypes.from_ical(event.get('DURATION'))
                    end_date = start_date + duration if duration else None
                    while start_date < end_date:
                        holidays.append(start_date.strftime("%Y-%m-%d"))
                        start_date += timedelta(days=1)
            elif summary == "Last Day of School for Students":
                self.last_day_of_school = start_date = event.get(
                    'DTSTART').dt.strftime("%Y-%m-%d")

        return holidays


if __name__ == "__main__":
    # Replace with the path to your .ics file
    ical_file_path = 'icalfeed.ics'
    carpool = CarpoolSchedule(ical_file_path)
    carpool.assign_roaster()
