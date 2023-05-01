import socket, select
import os, signal, sys
import time
from .job import SAMMJob
from .utils import str2array
import logging

class SAMMWorkerStats:
    def __init__(self, w):
        if not isinstance(w, SAMMWorker):
            self.connected=False
            self.registered=False
            self.last_recv_job_id=-1
            self.last_run_job_id=-1
            self.last_done_jobe_id=-1
            self.received_jobs=-1
            self.processed_jobs=-1
            self.run_jobs=-1
            self.done_jobs=-1
            self.received_bytes=-1
            self.sent_bytes=-1
            return
        self.connected=w.connected
        self.registered=w.registered
        self.last_recv_job_id=w.last_recv_job_id
        self.last_run_job_id=w.last_run_job_id
        self.last_done_jobe_id=w.last_done_jobe_id
        self.received_jobs=w.received_jobs
        self.processed_jobs=w.processed_jobs
        self.run_jobs=w.run_jobs
        self.done_jobs=w.done_jobs
        self.received_bytes=w.received_bytes
        self.sent_bytes=w.sent_bytes
        self.running_jobs = len(w.running_jobs)

    def __str__(self):
        return "connected=%s " \
            "registered=%s " \
            "received_bytes=%d " \
            "sent_bytes=%d " \
            "processed_jobs=%d " \
            "run_jobs=%d " \
            "done_jobs=%d " \
            "received_jobs=%d " \
            "running_jobs=%d " \
            "last_recv_job_id=%s " \
            "last_run_job_id=%s " \
            "last_done_jobe_id=%s " % ( \
                self.connected,
                self.registered,
                self.received_bytes,
                self.sent_bytes,
                self.processed_jobs,
                self.run_jobs,
                self.done_jobs,
                self.received_jobs,
                self.running_jobs,
                self.last_recv_job_id,
                self.last_run_job_id,
                self.last_done_jobe_id)

class SAMMWorker:
    def __init__(self, plugin_name, sock=None, address=None, wait=5):
        if sock is None:
            self.sock = socket.socket(
                            socket.AF_UNIX, socket.SOCK_STREAM)
        else:
            self.sock = sock
        self.pid = os.getpid()
        self.registered = False
        self.connected = False
        self.max_jobs = 1
        self.running_jobs = {}
        self.raw_data = b""
        self.wait = wait
        self.last_recv_job_id=-1
        self.last_run_job_id=-1
        self.last_done_jobe_id=-1
        self.received_jobs=0
        self.processed_jobs=0
        self.run_jobs=0
        self.done_jobs=0
        self.received_bytes=0
        self.sent_bytes=0
        self.address=address
        self.logger = logging.getLogger("SAMMWorker")
        self.plugin_name = plugin_name
        #self.logger.setLevel(logging.DEBUG)
        #ch = logging.StreamHandler()
        #ch.setLevel(logging.DEBUG)
        #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        #ch.setFormatter(formatter)
        #self.logger.addHandler(ch)

        self.logger.debug("Instantiation of NagiosWorker with sock=%s and wait=%d", \
            self.sock, self.wait)

    def connect(self, address=None):
        if address is None:
            self.sock.connect(self.address)
        else:
            self.sock.connect(address)
        self.logger.debug("Connected to address \"%s\"", address)
        self.connected = True

    def stats(self):
        return SAMMWorkerStats(self)

    def register(self):
        self.register_message=b'@wproc register name=test%(pid)d;pid=%(pid)d;' \
            b'plugin=%(plugin_name)s\0\1\0\0\0' \
            % {b'pid': self.pid, b'plugin_name': self.plugin_name.encode('ascii') }
        self.logger.debug("Sending registration message: \"%s\"", self.register_message.decode('ascii'))
        self.sock.send(self.register_message)
        rec = self.sock.recv(3)
        self.logger.debug("Received data: %s", rec.decode('ascii'))
        if b"OK\0" != rec:
            raise Exception("Error Connecting. " + rec.decode('ascii'))
        self.registered=True

    def detach(self):
        self.sock = self.sock.detach()
        self.logger.debug("Detached sock %s", str(self.sock))

    def close(self):
        self.connected = False
        self.registered = False
        self.sock.close()
        self.logger.debug("Closed sock %s", str(self.sock))

    def recv(self):
        if self.connected == False:
            raise Exception("Not connected")
        readsock, writesock, exsock = select.select([self.sock], [], [], self.wait)
        self.logger.debug("Select releasing: readsock=%s", str(readsock))
        if len(readsock) > 0:
            temp=readsock[0].recv(2048)
            self.received_bytes+=len(temp)
            self.raw_data += temp
            self.logger.debug("Buffer is now: %s" % self.raw_data.decode('ascii'))
            if self.raw_data == b"":
                self.registered = False
                raise Exception("Got disconnected?")
            if not isinstance(self.raw_data, bytes):
                raise Exception("Invalid input from nagios")
            self.raw_data = self.process(self.raw_data)
            return True
        return False

    def process(self, s):
        while True:
            rec = s.split(b"\0\1\0\0\0", 1)
            if len(rec) == 1:
                return rec[0]
            s = rec[1]
            rec = rec[0]
            if rec == '':
                return s
            self.received_jobs += 1
            self.processed_jobs += 1
            self.logger.debug("starting SAMMJob with %s" % rec.decode('ascii'))
            job = SAMMJob(rec.decode('ascii'))
            self.last_run_job_id = job
            self.running_jobs[job.job_id] = job
        return s

    def run(self, job_id):
        job = self.running_jobs[job_id]
        check = job.check
        self.last_run_job_id=job_id
        if not check.running and not check.done:
            job.run()
            self.run_jobs += 1
            return True
            #logging.info(check)
        return False

    def done(self, job_id):
        if job_id not in self.running_jobs:
            raise Exception("Job %s not pending" % str(jdi))
        job = self.running_jobs[job_id]
        if job.still_running():
            return False
        message = str(job)
        self.sock.send(message.encode('ascii'))
        self.logger.debug("Sent data: %s" % message)
        self.running_jobs.pop(job_id)
        self.last_done_jobe_id=job_id
        self.done_jobs += 1
        self.sent_bytes += len(message)
        return True

    @property
    def jobs(self):
        return [k for k in self.running_jobs.keys()]

