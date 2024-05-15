"""define a custom logger for seleniumqt."""

from loguru import logger

# create formating
FORMAT = "<green>{time:YYYY-MM-DD-HH:mm:ss.SSS}</green>-|-<u><level>{level:-^8}</level></u>-|-<white>{thread.name:-^10}</white>---<white>{process.name:-^30}</white>-|-<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>---<b><level>{message}</level></b>"

# remove existing sink.
logger.remove()
# create logs folder if it doesn't already exsit.
from datetime import datetime
import os
import sys

# threading to get thread name
import threading

#processing to get process name
import multiprocessing

# re + slugify to convert any string to a valid filename
import re

def slugify(str_: str):
    slug = re.sub(r'[^A-z0-9-]', '_', str_)
    return slug

if not os.path.exists("./.log"):
    os.mkdir(".log")

# add sinks, backtrace and diagnose + Enqueue all.
# log level is set to trace for file, and DEBUG for stdout.

# colorize to the terminal
logger.add(
    sys.stdout,
    format=FORMAT,
    colorize=True,
    backtrace=True,
    diagnose=True,
    enqueue=True,
    level="DEBUG",
)

# no-colorize to log file.
logger.add(
    #                                                                      this will make it clearer which thread and process created each log.
    open(datetime.now().strftime(f"./.log/%d_%m_%Y_%H_%M_%S_{slugify(threading.current_thread().name)}_{slugify(multiprocessing.current_process().name)}.log"), "w"),
    format=FORMAT,
    colorize=False,
    enqueue=True,
    backtrace=True,
    diagnose=True,
    level="TRACE",
)

logger.trace("init done.")
