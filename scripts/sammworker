#!/usr/bin/python3

import sys, getopt, os
from sammcheck import SAMMWorker
import time
import logging
import signal
from threading import Timer

w = None
keep_running = True
stats_time = 5
pid_file='/run/sammworker_process.pid'
runas='nagios'
log_file="/usr/local/nagios/var/sammworker.log"
qh_file='/usr/local/nagios/var/rw/nagios.qh'
job_wait=5
retry_delay=5

def sig(signum, frame):
    global w, keep_running, pid_file

    w.close()
    if signum == signal.SIGINT:
        logging.warning('Interrupt received. Closing connections')
        keep_running = False
        os.remove(pid_file)
        logging.shutdown()
    elif signum == signal.SIGHUP:
        logging.warning('Restarting the conneciton')
        w.connect()
        w.register()
    else:
        logging.warning('Signal handler called with signal %s' % str(signum))

def help(msg=""):
    print("%s\n" \
        "USAGE: %s [ options ]\n" \
        "-F Run in the foreground\n" \
        "-r <seconds>  Delay between attempts of connection to worker pipe in seconds (def: 5 seconds)\n" \
        "-j <seconds>  Time to wait for jobs in seconds (def: 5 seconds)\n" \
        "-p <pid file> Path to the PID file (def: /run/sammworker_process.pid)\n" \
        "-u <username> Username to run this process (def: nagios)\n" \
        "-d <level>    Debug level\n" \
        "-h            Print this screen" % \
        (msg, sys.argv[0]))
    return -1

def main(argv):
    t = None
    global keep_running, pid_file, w, log_file, qh_file

    try:
        opts, args = getopt.getopt(argv, "Fr:j:p:u:d:")
    except getopt.GetoptError:
        return help()

    foreground=False
    logging.basicConfig(level=logging.INFO, filename=log_file)
    for opt, arg in opts:
        if opt == '-h':
            return help()
        elif opt == '-F':
            foreground = True
        elif opt == '-r':
            retry_delay = int(arg)
        elif opt == '-j':
            wait = int(arg)
        elif opt == '-p':
            pid_file = arg
        elif opt == '-u':
            runas = arg
        elif opt == '-d':
            logging.basicConfig(level=logging.DEBUG, filename=log_file)
        else:
            return help("Invalid parameter %s" % arg)

    if foreground == False:
        n = os.fork()
        if n > 0:
            return 0

    with open(pid_file, "w") as f:
        pid = os.getpid()
        f.write(str(pid))

    signal.signal(signal.SIGHUP, sig)
    signal.signal(signal.SIGINT, sig)

    while keep_running:
        w = SAMMWorker(wait=job_wait, address=qh_file)
        while w.connected == False:
            try:
                w.connect()
                logging.info("Connected to Nagios. Starting to process requests")
            except Exception as e:
                logging.warning("Nagios not running. Retrying in 5 seconds. %s" % str(e))
                time.sleep(retry_delay)
        w.register()
        if w.registered:
            logging.info("Registered")
        else:
            logging.critical("Unable to register. Aborting")
            w.close()
        while keep_running and w.registered and w.connected:
            if t is None or time.time() - t > stats_time:
                logging.info(w.stats())
                t = time.time()
            try:
                if w.recv():
                    logging.debug("Received data.")
                else:
                    logging.debug("No data received. Check jobs.")
            except Exception as e:
                logging.warning("Unable to receive data. Exiting loop. %s" % str(e))
                continue
            for j in w.jobs:
                if w.run(j):
                    logging.debug("Ran job %s" % j)
            for j in w.jobs:
                if w.done(j):
                    logging.debug("Finished job %s" % j)
        logging.warning("Disconnected from Nagios.")
        w.close()
    os.remove(pid_file)
    return 0

if __name__ == "__main__":
    exit(main(sys.argv[1:]))
