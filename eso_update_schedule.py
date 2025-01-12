import time
import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from eso import construct_query, get_eso, group_data, store_dfs
from ServerFiles import setup_logging
from pytz import timezone

logger = setup_logging("eso_updater.log")

# Time interval in minutes for fetching data
API_interval_time_in_seconds = 60
process_interval_in_seconds = 15
catch_up_max_day_increment = 10

# Log file for last update time
import os

# Define an absolute path for the log file
base_dir = os.path.dirname(
    os.path.abspath(__file__)
)  # Directory where the script is located
last_update_log = os.path.join(base_dir, "eso_last_update_time.txt")

# set timezone
tz = timezone("America/Chicago")


# ==========  Account periods of downtime  =============================


def get_last_update():
    try:
        with open(last_update_log, "r") as f:
            content = f.read().strip()
            if content:
                last_update_time = datetime.fromisoformat(content)
                logger.info(f"Read last update time: {last_update_time}")
            else:
                raise ValueError("No data found in the update time file")
    except FileNotFoundError:
        last_update_time = datetime.now() - timedelta(days=10)
        logger.warning("Update time file not found, assuming start time 10 days ago")
    except Exception as e:
        last_update_time = datetime.now() - timedelta(days=10)
        logger.error(f"Error reading last update time, defaulting to 10 days ago: {e}")
    return last_update_time


def set_last_update(update_time):
    try:
        with open(last_update_log, "w") as f:
            f.write(update_time.isoformat())
        logger.info(f"Successfully updated last update time to {update_time}")
    except Exception as e:
        logger.error(f"Failed to update last update time: {e}")


def catch_up_data():
    last_update_time = get_last_update()
    current_time = datetime.now()
    if last_update_time + timedelta(minutes=1) < current_time:
        logger.info(f"Last Updated : {last_update_time} - Initializing Catchup Script")
    while last_update_time < current_time:
        start_time = last_update_time
        end_time = min(
            start_time + timedelta(days=catch_up_max_day_increment), current_time
        )
        logger.info(f"  processing: {start_time} - {end_time}")
        query = construct_query(start_time, end_time)
        data = get_eso(query)
        if data:
            group_dfs = group_data(data)
            store_dfs(group_dfs)
            last_update_time = end_time
            set_last_update(last_update_time)
        else:
            break
        time.sleep(1)  # Pause to mitigate API rate limit concerns


# ==========  Main Logic  ==============================================


def fetch_and_process_data():
    # This function now only handles data updates at regular intervals, assuming no large backlogs
    end_time = datetime.now()
    start_time = end_time - timedelta(seconds=API_interval_time_in_seconds)
    query = construct_query(start_time, end_time)
    data = get_eso(query)
    if data:
        set_last_update(end_time)
        group_dfs = group_data(data)
        store_dfs(group_dfs)


def main(stop_event):
    logger.info("Starting Main")
    catch_up_data()  # Perform catch-up first

    logger.info("Completed catch up")
    try:
        scheduler = BackgroundScheduler(
            timezone="UTC"
        )  # Ensure you define 'tz' or replace with a literal
        scheduler.add_job(
            fetch_and_process_data, "interval", seconds=process_interval_in_seconds
        )
        scheduler.start()

        # Wait indefinitely until the event is set.
        stop_event.wait()
        scheduler.shutdown()
        logger.info("Scheduler shutdown completed")

    except Exception as e:
        logger.error(f"Failed to add to scheduler: {e}")
        raise


if __name__ == "__main__":
    stop_event = threading.Event()

    def run_scheduler():
        main(stop_event)

    # Run the main function in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
        logger.info("Stopping scheduler...")

    # Wait for the scheduler thread to finish
    scheduler_thread.join()
    logger.info("Scheduler stopped.")
