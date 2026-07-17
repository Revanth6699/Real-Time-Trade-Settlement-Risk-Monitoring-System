import random

class MarketState:

    STATES = {
        "LOW": (5, 10),        # 1 trade every 5-10 sec
        "NORMAL": (0.5, 1.0),  # 1-2 trades/sec
        "BUSY": (0.2, 0.5),    # 2-5 trades/sec
        "PEAK": (0.05, 0.15)   # 7-20 trades/sec
    }

    PROBABILITIES = [
        ("LOW", 0.25),
        ("NORMAL", 0.45),
        ("BUSY", 0.20),
        ("PEAK", 0.10)
    ]

    @classmethod
    def get_state(cls):
        r = random.random()
        total = 0

        for state, prob in cls.PROBABILITIES:
            total += prob
            if r <= total:
                return state

        return "NORMAL"

    @classmethod
    def get_delay(cls, state):
        low, high = cls.STATES[state]
        return random.uniform(low, high)