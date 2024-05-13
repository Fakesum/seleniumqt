from loguru import logger

# create formating
FORMAT = "<green>{time:YYYY-MM-DD-HH:mm:ss.SSS}</green>-|-<u><level>{level:-^8}</level></u>-|-<white>{thread.name:-^10}</white>---<white>{process.name:-^30}</white>-|-<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>---<b><level>{message}</level></b>"

# remove existing sink.
logger.remove()
# create logs folder if it doesn't already exsit.
from datetime import datetime
import os
import sys

if not os.path.exists("./logs/"):
    os.mkdir("logs")

# add sinks, backtrace and diagnose + Enqueue all.

# colorize to the terminal
logger.add(
    sys.stdout,
    format=FORMAT,
    colorize=True,
    backtrace=True,
    diagnose=True,
    enqueue=True
)

# no-colorize to log file.
logger.add(
    open(datetime.now().strftime("logs/%d_%m_%Y_%H_%M_%S.log"), "w"),
    colorize=False,
    enqueue=True,
    backtrace=True,
    diagnose=True
)