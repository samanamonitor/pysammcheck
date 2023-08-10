import time

class SAMMCheck:
    outmsg = "UNKNOWN - Plugin has not been initialized"
    outval = 3
    ready = False
    done = False
    running = False
    start = 0
    stop = 0
    _crit = None
    _host = ""
    _warn = None
    ready = False
    _argstring = ""
    _base_help = '''\
Check Samana %s v%s
This nagios plugin come with ABSOLUTELY NO WARRANTY and is property of
SAMANA GROUP LLC. If you want to use it, you should contact us before
to get a license.
Copyright (c) 2021 Samana Group LLC

Usage: %s  [options]
-h              To get this help message
'''
    def __init__(self, argv):
        self._argv = argv
        self.process_args()
        self.check_args()

    @property
    def runtime(self):
        return self.stop - self.start

    def process_args(self):
        pass

    def check_args(self):
        if self._host == "":
            self.unknown("Host not specified.")
            return

        if self._crit is not None:
            try:
                self._crit = int(self._crit)
            except:
                self.unknown("Invalid CRITICAL threshold.")
                return

        if self._warn is not None:
            try:
                self._warn = int(self._warn)
            except:
                self.unknown("Invalid WARNING threshold.")
                return
        self.ready = True

    def run(self):
        pass

    def ok(self, msg, perf_data="", addl=""):
        self.outmsg = "OK - %s%s\n%s" % (msg, perf_data, addl)
        self.outval = 0
        self.done = True
        self.running = False
        self.stop = time.time()        


    def warning(self, msg, perf_data="", addl=""):
        self.outmsg = "WARNING - %s%s\n%s" % (msg, perf_data, addl)
        self.outval = 1
        self.done = True
        self.running = False
        self.stop = time.time()        

    def critical(self, msg, perf_data="", addl=""):
        self.outmsg = "CRITICAL - %s%s\n%s" % (msg, perf_data, addl)
        self.outval = 2
        self.done = True
        self.running = False
        self.stop = time.time()        

    def unknown(self, msg=None):
        if msg is not None:
            self.outmsg = "UNKNOWN - %s" % msg
        self.outval = 3
        self.done = True
        self.running = False
        self.stop = time.time()

    def __str__(self):
        return self.outmsg
