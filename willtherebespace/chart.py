import datetime


class BusynessChart:
    def __init__(self, raw_results):
        results = []
        dict_results = {}

        if raw_results:
            average = sum(x for x in raw_results.values()) / len(raw_results)

            results = []
            for day in range(7):
                for hour in range(24):
                    busyness = raw_results.get((day, hour))

                    if busyness is None:
                        # try the day before
                        day_before = day - 1
                        while day_before != day:
                            busyness_before = raw_results.get((day_before, hour))
                            if busyness_before is not None:
                                busyness = busyness_before
                                break

                            day_before -= 1
                            if day_before < 0:
                                day_before = 6

                        if busyness is None:
                            # average
                            busyness = average

                    dict_results[(day, hour)] = busyness
                    results.append((day, hour, busyness))

        now = datetime.datetime.now()
        now_results = dict_results.get((now.weekday(), now.hour))

        self.now_results = now_results
        self.results = results
