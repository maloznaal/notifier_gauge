from prometheus_client import Gauge, start_http_server
import threading, time, signal
from datetime import timedelta
import glob
import os

tag = os.environ['TAG']
# const path, iNotify watching for this path inside container bind to host machine
WATCH_DIR = '/watchdir/'
PERIOD_SECONDS = os.environ['PERIOD_SECONDS']
TYPE = os.environ['TYPE']

g = Gauge('ftp_failed_directory', tag)


# raise exception, do cleanup
class ProcessShutdown(Exception):
    pass


# count files inside bind mounted DIR - WATCH_DIR
# specify .format for file types
def count_files():
    files = [f for f in glob.glob(WATCH_DIR + "*", recursive=False)]
    return len(files)


def update_gauge():
    print(time.ctime())
    # increase counter by gauge value
    g.set(count_files())


# handle SIGKILL
def signal_handler(signum, frame):
    print(signum, frame)
    raise ProcessShutdown


class Job(threading.Thread):
    def __init__(self, interval, execute, *args, **kwargs):
        threading.Thread.__init__(self)
        self.interval = interval
        self.execute = execute
        self.stopped = threading.Event()
        self.daemon = False
        self.args = args
        self.kwargs = kwargs

    def run(self):
        while not self.stopped.wait(self.interval.total_seconds()):
            self.execute(*self.args, **self.kwargs)

    def stop(self):
        self.stopped.set()
        self.join()


if __name__ == "__main__":
    # expose metrics on port - port passed by env, async
    start_http_server(3000)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    job = Job(interval=timedelta(seconds=int(PERIOD_SECONDS)), execute=update_gauge)
    job.start()

    # interceipt SIGKILL signal, stop job gracefully, do cleanup
    while True:
        try:
            time.sleep(1)
        except ProcessShutdown:
            print("\nProcess shutdown gracefully: running cleanup")
            job.stop()
            break
