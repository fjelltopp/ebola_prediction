import schedule
import logging

from ebola_data import get_and_predict

import time



schedule.every(1).hour().do(get_and_predict)


while True:
    schedule.run_pending()
    time.sleep(1)
