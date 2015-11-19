import collections
import datetime


class InvalidBusynessChart(ValueError):
    pass


class ContinousWeek(collections.UserDict):

    @staticmethod
    def normalise(day, hour, quarter):
        while day < 0:
            day += 7
        while day > 6:
            day -= 7
        while hour < 0:
            hour += 24
        while hour > 23:
            hour -= 24
        while quarter < 0:
            quarter += 4
        while quarter > 3:
            quarter -= 4
        return day, hour, quarter

    @staticmethod
    def _key_for(day, hour, quarter):
        day, hour, quarter = ContinousWeek.normalise(day, hour, quarter)
        return (day, hour, quarter)

    def set(self, day, hour, quarter, value):
        key = self._key_for(day, hour, quarter)
        self.data[key] = value

    def get(self, day, hour, quarter):
        key = self._key_for(day, hour, quarter)
        return self.data.get(key)

    def next(self, day, hour, quarter, direction=None):
        if direction == -1:
            return self.previous(day, hour, quarter)

        quarter += 1
        if quarter > 3:
            quarter = 0

            hour += 1
            if hour > 23:
                hour = 0
                day += 1

        return day, hour, quarter

    def previous(self, day, hour, quarter):
        quarter -= 1
        if quarter < 0:
            quarter = 3

            hour -= 1
            if hour < 0:
                hour = 23
                day -= 1

        return day, hour, quarter


class BusynessChart:
    def __init__(self, raw_results):
        self.week = ContinousWeek()

        self.raw_week = ContinousWeek()
        for row in raw_results:
            self.raw_week.set(int(row[0]) - 1, int(row[1]), int(row[2]),
                              row[3])

        if not self.raw_week.data:
            raise InvalidBusynessChart('There are no results so a chart '
                                       'cannot be formed.')

        self.raw_week2 = ContinousWeek()

        # first fill from previous day
        for day in range(7):
            for hour in range(24):
                for quarter in range(4):
                    busyness = self.raw_week.get(day, hour, quarter)

                    if busyness is None:
                        for i in range(7):
                            busyness_before = self.raw_week.get(day - i, hour,
                                                                quarter)
                            if busyness_before is not None:
                                busyness = busyness_before
                                break

                    self.raw_week2.set(day, hour, quarter, busyness)

        self.raw_week = self.raw_week2

        # next interpolate
        for day in range(7):
            for hour in range(24):
                for quarter in range(4):
                    busyness = self.raw_week.get(day, hour, quarter)
                    if busyness is None:
                        busyness = round(self.interpolate(day, hour, quarter),
                                         1)

                    self.week.set(day, hour, quarter, busyness)

    def interpolate(self, day, hour, quarter):
        def find_value(day, hour, quarter, direction):
            distance = 0
            while True:
                distance += 1
                day, hour, quarter = self.raw_week.next(day, hour, quarter,
                                                        direction)
                value = self.raw_week.get(day, hour, quarter)
                if value is not None:
                    return float(value), distance

        left_value, left_distance = find_value(day, hour, quarter, -1)
        right_value, right_distance = find_value(day, hour, quarter, +1)

        a = left_distance / (left_distance + right_distance)
        return left_value * (1 - a) + right_value * a

    @property
    def now(self):
        d = datetime.datetime.now()
        quarter = int(d.minute / 15)
        return round(self.week.get(d.weekday(), d.hour, quarter))

    @property
    def rows(self):
        now = datetime.datetime.now()
        quarter_now = int(now.minute / 15)

        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

        for day, day_name in enumerate(days):
            for hour in range(24):
                for quarter in range(4):
                    is_now = day == now.weekday() and hour == now.hour \
                        and quarter == quarter_now
                    yield (day_name, hour, quarter), \
                        self.week.get(day, hour, quarter), is_now
