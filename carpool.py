from datetime import date, datetime, timedelta
import json
import icalendar
from icalendar import Calendar, Event, vCalAddress, vText, vDDDTypes, Alarm
import requests
import pytz
from pytz import timezone


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
    "Monday": "Bhavani",
    "Tuesday": "Shivaji",
    "Wednesday": "Yaping",
    "Thursday": "Sandesh",
    "Friday": "TODO",
    "Saturday": "~~~~~~~~~~",
    "Sunday": "~~~~~~~~~~~"
}

holiday_event_summary = ["Trad - Teacher Workday", "Trad - Holiday"
                         "Trad - Thanksgiving Break", "Trad - Winter Break", "Trad - Spring Break"]

weekdays = ["Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"]

ignored_weekdays = ["Friday", "Saturday", "Sunday"]

last_day = "Trad - End of Nine Weeks and last day of classes"
dt_format = "%Y-%m-%dT%H:%M:%S"


class CarpoolSchedule:
    def __init__(self, ical_file_path):
        self.missed_roaster = Queue()
        self.regular_friday_roaster = Queue()
        self.holidays = self.read_holidays_from_ical(ical_file_path)
        # self.holidays = self.read_holidays_from_api()
        self.assign_regular_friday()
        self.schedule = {}
        self.start_from_date = datetime(2024, 8, 26)
        self.last_day_of_school = datetime(2025, 7, 1)
        self.generate_roaster_for_365_days = 365

    def assign_roaster(self):
        for i in range(self.generate_roaster_for_365_days):
            self.missed_roaster.clean()
            current_date = self.start_from_date + timedelta(days=i)
            day = self.get_weekday(current_date)

            if current_date > self.last_day_of_school:
                continue
            if current_date.strftime("%Y-%m-%d") in self.holidays:
                if day not in ignored_weekdays:
                    self.missed_roaster.enqueue(
                        days_to_drivers[day]+' for '+current_date.strftime("%Y-%m-%d"))
                continue

            if day == "Sunday" or day == "Saturday":
                continue
            if day == "Friday":
                if self.missed_roaster.size() > 0:
                    self.schedule[current_date] = self.missed_roaster.dequeue()
                else:
                    self.schedule[current_date] = self.regular_friday_roaster.dequeue(
                    )
            else:
                self.schedule[current_date] = days_to_drivers[day]

    def get_weekday(self, calendar_date):
        # Parse the calendar date string into a datetime object
        # date_obj = datetime.strptime(calendar_date, '%Y-%m-%d')
        # Get the weekday index (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)
        weekday_index = calendar_date.weekday()
        # Return the name of the weekday

        return weekdays[weekday_index]

    def assign_regular_friday(self):
        for i in range(400):
            for key, value in days_to_drivers.items():
                if key not in ignored_weekdays:
                    self.regular_friday_roaster.enqueue(value)

    def read_holidays_from_api(self):
        holidays = []
        url = "https://awsapieast1-prod23.schoolwires.com/REST/api/v4/CalendarEvents/GetEvents/19291?StartDate=2023-12-01&EndDate=2024-06-30&ModuleInstanceFilter=&CategoryFilter=&IsDBStreamAndShowAll=true"
        payload = {}
        headers = {
            'Authorization': 'Bearer <DING-DONG>'
        }
        # response = requests.request("GET", url, headers=headers, data=payload)
        # print(response.text)
        f = open('schedule.json', 'r')
        events = json.load(f)

        for event in events:
            title = event['Title']
            if title == "Last Day of School for Students":
                self.last_day_of_school = datetime.strptime(
                    event['Start'], dt_format)
            if title in holiday_event_summary or "Holiday" in title:
                start = datetime.strptime(event['Start'], dt_format)
                end = datetime.strptime(event['End'], dt_format)
                while start < end:
                    holidays.append(start)
                    start += timedelta(days=1)
        f.close()

        return holidays

    def read_holidays_from_ical(self, ical_file_path):
        holidays = []

        with open(ical_file_path, 'rb') as f:
            cal_data = f.read()
        cal = icalendar.Calendar.from_ical(cal_data)

        for event in cal.walk('VEVENT'):
            title = event['SUMMARY']
            if title == last_day:
                self.last_day_of_school = event.get(
                    'DTSTART').dt.strftime("%Y-%m-%d")
            if title in holiday_event_summary or "Holiday" in title:
                start = event.get('DTSTART').dt
                if start not in holidays:
                    holidays.append(start.strftime("%Y-%m-%d"))
                end = event.get('DTEND').dt
                if end not in holidays:
                    holidays.append(end.strftime("%Y-%m-%d"))

        return holidays


if __name__ == "__main__":
    # Replace with the path to your .ics file
    ical_file_path = 'basic.ics'
    carpool = CarpoolSchedule(ical_file_path)
    # carpool.read_holidays_from_api()
    carpool.assign_roaster()
    cal = Calendar()
    cal.add('prodid', '-//Shivaji Car Pool//byrapaneni.com//')
    cal.add('version', '2.0')
    eastern = timezone('US/Eastern')
    for date, driver in carpool.schedule.items():
        # print(date.strftime("%Y-%m-%d"), driver)
        start_time = date.replace(hour=6, minute=45)
        end_time = start_time + timedelta(minutes=5)

        event = Event()
        event.add('name', f"Carpool: {driver}")
        event.add('summary', f"Carpool: {driver}")
        event.add('description', 'Carnage MS Carpool Scheduled Driver')
        event.add('dtstart', start_time)
        event.add('dtend', end_time)

        organizer = vCalAddress('MAILTO:shivaji.byrapaneni@gmail.com')

        # Add parameters of the event
        organizer.params['name'] = vText('Shivaji Byrapaneni')
        event['organizer'] = organizer
        event['location'] = vText(
            '6903 Carpenter Fire Station Rd, Cary, NC 27519')
        event.add('priority', 1)

        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add("description", "Reminder")
        alarm.add("TRIGGER;RELATED=START", "-PT10M")
        event.add_component(alarm)
        cal.add_component(event)

    f = open('carpool_schedule.ics', 'wb')
    f.write(cal.to_ical())
    f.close()
