import collections
import datetime


class ContinousWeek(collections.UserDict):
    def normalise(self, day, hour):
        while day < 0:
            day += 7
        while day > 6:
            day -= 7
        while hour < 0:
            hour += 24
        while hour > 23:
            hour -= 24
        return day, hour

    def set(self, day, hour, value):
        day, hour = self.normalise(day, hour)
        self.data[(day, hour)] = value

    def get(self, day, hour):
        day, hour = self.normalise(day, hour)
        return self.data.get((day, hour))

    def next(self, day, hour, direction=None):
        if direction == -1:
            return self.previous(day, hour)

        hour += 1
        if hour > 23:
            hour = 0
            day += 1
        return day, hour

    def previous(self, day, hour):
        hour -= 1
        if hour < 0:
            hour = 23
            day -= 1
        return day, hour


class BusynessChart:
    def __init__(self, raw_results):
        if not raw_results:
            raise ValueError('There are no results so a chart cannot be '
                             'formed.')

        self.week = ContinousWeek()

        self.raw_week = ContinousWeek()
        for row in raw_results:
            self.raw_week.set(int(row[0]), int(row[1]), row[2])

        average = sum(self.raw_week.data.values()) / len(self.raw_week.data)

        self.raw_week2 = ContinousWeek()

        # first fill from previous day
        for day in range(7):
            for hour in range(24):
                busyness = self.raw_week.get(day, hour)

                if busyness is None:
                    for i in range(7):
                        busyness_before = self.raw_week.get(day - i, hour)
                        if busyness_before is not None:
                            busyness = busyness_before
                            break

                self.raw_week2.set(day, hour, busyness)

        self.raw_week = self.raw_week2

        # next interpolate
        for day in range(7):
            for hour in range(24):
                busyness = self.raw_week.get(day, hour)
                if busyness is None:
                    busyness = self.interpolate(day, hour)

                self.week.set(day, hour, busyness)

    def interpolate(self, day, hour):
        def find_value(day, hour, direction):
            distance = 0
            while True:
                distance += 1
                day, hour = self.raw_week.next(day, hour, direction)
                value = self.raw_week.get(day, hour)
                if value is not None:
                    return float(value), distance

        left_value, left_distance = find_value(day, hour, -1)
        right_value, right_distance = find_value(day, hour, +1)

        a = left_distance / (left_distance + right_distance + 1)
        return left_value * (1 - a) + right_value * a

    def as_list(self):
        results = []
        for day in range(7):
            for hour in range(24):
                results.append((day, hour, self.week.get(day, hour)))
        return results

    @property
    def now(self):
        d = datetime.datetime.now()
        return self.week.get(d.weekday(), d.hour)
