import random
import time

MAX_RETRIES = 3

def process_settlement(trade):

    retry_count = trade.get("retry_count", 0)

    outcome = random.choices(
        ["COMPLETED", "DELAYED", "FAILED"],
        weights=[70, 20, 10]
    )[0]

    if outcome == "DELAYED":

        if retry_count < MAX_RETRIES:

            trade["retry_count"] = retry_count + 1

            time.sleep(3)

            return process_settlement(trade)

        else:
            return "FAILED"

    return outcome