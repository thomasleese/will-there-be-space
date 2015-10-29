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


class BusynessChart:
    def __init__(self, raw_results):
        if not raw_results:
            raise ValueError('There are no results so a chart cannot be '
                             'formed.')

        self.week = ContinousWeek()

        raw_week = ContinousWeek()
        for row in raw_results:
            raw_week.set(int(row[0]), int(row[1]), row[2])

        average = sum(raw_week.data.values()) / len(raw_week.data)

        for day in range(7):
            for hour in range(24):
                busyness = raw_week.get(day, hour)

                if busyness is None:
                    # try the day before
                    for i in range(7):
                        busyness_before = raw_week.get(day - i, hour)
                        if busyness_before is not None:
                            busyness = busyness_before
                            break

                    if busyness is None:
                        # average
                        busyness = average

                self.week.set(day, hour, busyness)

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
