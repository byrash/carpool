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

holiday_event_summary = ["Teacher Workday",
                         "Holiday- No School", "Spring Break", "Winter Break", "Vacation Day- No School"]

weekdays = ["Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"]

ignored_weekdays = ["Friday", "Saturday", "Sunday"]


class CarpoolSchedule:
    def __init__(self, ical_file_path):
        self.missed_roaster = Queue()
        self.regular_friday_roaster = Queue()
        # self.holidays = self.read_holidays_from_ical(ical_file_path)
        self.holidays = self.read_holidays_from_api()
        self.assign_regular_friday()
        self.schedule = {}
        self.start_from_date = datetime(2023, 12, 11)
        self.last_day_of_school = datetime(2024, 7, 1)
        self.generate_roaster_for_365_days = 365

    def assign_roaster(self):
        for i in range(self.generate_roaster_for_365_days):
            self.missed_roaster.clean()
            current_date = self.start_from_date + timedelta(days=i)
            day = self.get_weekday(current_date)

            if current_date > self.last_day_of_school:
                # self.schedule[current_date] = "Beyond Last Day Of School"
                continue

            if current_date in self.holidays:
                # self.schedule[current_date] = "Holiday"
                if day not in ignored_weekdays:
                    #     regular_friday_roaster_driver = self.regular_friday_roaster.dequeue()
                    #     print(current_date, 'Friday --> Missed by ',
                    #           regular_friday_roaster_driver)
                    #     self.missed_roaster.enqueue(regular_friday_roaster_driver)
                    # else:
                    # print(current_date, day, ' --> Missed by ',
                    #   days_to_drivers[day])
                    self.missed_roaster.enqueue(days_to_drivers[day])

                continue
            # else:
                # print(current_date, "Not in Holidays")

            if day == "Sunday" or day == "Saturday":
                # self.schedule[current_date] = "~~~~~~~~~~~~"
                continue
            if day == "Friday":
                if self.missed_roaster.size() > 0:
                    self.schedule[current_date] = self.missed_roaster.dequeue()
                    # print(current_date, day, '-->  ',
                    #       self.missed_roaster.dequeue())
                else:
                    self.schedule[current_date] = self.regular_friday_roaster.dequeue(
                    )
                    # print(current_date, day, '-->  ',
                    #       self.regular_friday_roaster.dequeue())
            else:
                self.schedule[current_date] = days_to_drivers[day]
                # print(current_date, day, '-->  ', self.get_value_by_slice(day))

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
        dt_format = "%Y-%m-%dT%H:%M:%S"
        for event in events:
            title = event['Title']
            if title == "Last Day of School for Students":
                self.last_day_of_school = datetime.strptime(
                    event['Start'], dt_format)
            if title in holiday_event_summary or "Holiday" in title:
                start = datetime.strptime(event['Start'], dt_format)
                end = datetime.strptime(event['End'], dt_format)
                # diff = end-start
                # print(title, start, end, diff.days)
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
            summary = event.get('summary')
            # print(event.get('DTSTART').dt, summary)
            if summary in holiday_event_summary:
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
    # carpool.read_holidays_from_api()
    carpool.assign_roaster()
    # print()
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
        # event.add('dtstart', datetime(
        #     2022, 1, 25, 8, 0, 0, tzinfo=eastern.zone))
        # event.add('dtend', datetime(
        #     2022, 1, 25, 10, 0, 0, tzinfo=eastern.zone))
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

        # event.name = f"Carpool: {driver}"
        # event.begin = datetime.combine(start_time, start_time.min.time())
        # event.end = datetime.combine(end_time, end_time.max.time())
        # event.alarms = [DisplayAlarm(trigger=timedelta(minutes=-10))]
        # cal.events.add(event)
        # print(driver)
    # with open("carpool_schedule.ics", "w") as f:
        # f.write(cal.to_ical())
    f = open('carpool_schedule.ics', 'wb')
    f.write(cal.to_ical())
    f.close()
