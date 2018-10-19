import schedule
import logging

from ebola_data import get_and_predict

import time

schedule.every().hour.do(get_and_predict)

logging.info("Starting data preparation loop")
while True:
    schedule.run_pending()
    time.sleep(1)
