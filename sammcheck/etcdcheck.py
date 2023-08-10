import getopt
from .check import SAMMCheck
from . import __version__
import json
import re
import etcd
import time

intstr = lambda x: str(x) if x is not None else ''
class SAMMEtcdCheck(SAMMCheck):
    _etcdserver = "127.0.0.1"
    _etcdport = 2379
    _excl = None
    _submod = None
    _logfilters = []
    _module = None
    _max_age = 600
    timeout = 60
    _data = None
    _module_name = "Etcd"
    def __init__(self, argv):
        super().__init__(argv)
        self._etcdclient = etcd.Client(host=self._etcdserver, port=self._etcdport, read_timeout=self.timeout)

    def process_args(self):
        try:
            opts, args = getopt.getopt(self._argv, "hH:m:c:w:s:i:e:x:E:a:t:")
            for opt, arg in opts:
                if opt == '-h':
                    return self.help()
                elif opt == "-H":
                    self._host = arg
                elif opt == "-m":
                    self._module = arg
                elif opt == "-c":
                    self._crit = arg
                elif opt == "-w":
                    self._warn = arg
                elif opt == "-s":
                    self._submod = arg
                elif opt == "-i":
                    self._incl = arg
                elif opt == "-e":
                    self._excl = arg
                elif opt == "-x":
                    for f in arg.split("|"):
                        logfilter = tuple(f.split(','))
                        if len(logfilter) < 2:
                            logfilter += tuple('')
                        self._logfilters += logfilter
                elif opt == "-E":
                    temp = arg.split(':')
                    self._etcdserver = temp[0]
                    if len(temp) > 1:
                        self._etcdport = int(temp[1])
                elif opt == "-a":
                    self._max_age = arg
                elif opt == "-t":
                    self.timeout = arg
                else:
                    return self.help()

        except getopt.GetoptError as e:
            return self.help(str(e))

    def check_args(self):
        super().check_args()
        if not self.ready: return
        self.ready = False
        if self._module is None:
            self.unknown("Module is a mandatory parameter.")
            return
        try:
            self._max_age = int(self._max_age)
        except ValueError:
            self.unknown("Max Age can only be an integer.")
            return

        try:
            self.timeout = int(self.timeout)
        except ValueError:
            self.unknown("Timeout can only be an integer.")
            return
        self.ready = True

    def __repr__(self):
        return "<%s etcdserver=%s:%d>" % (self.__class__.__name__, self._etcdserver, self._etcdport)

    def help(self, msg=""):
        self.outmsg =  "%s\n" % msg \
            + self._base_help % (self._module_name, __version__, self._argv[0]) + \
            "-H <host>       Id of the host in Etcd database\n" \
            "-w <warning>    Warning threshold\n" \
            "-c <critical>   Critical threshold\n" \
            "-E <etcdserver> Etcd server and port <ip>:<port> port is optional" \
            "-m <module>     Module to query. (cpu|ram|swap|log|services|hddrives|uptime)\n" \
            "-s <logname>    Log name when using \"log\" module.\n" \
            "-i <include>    Regex of the services that need to be included when using the \"services\" module.\n" \
            "-e <exclude>    Regex of the services that need to be excluded when using the \"services\" module.\n" \
            "-x <logfilter>  When using \"log\" module, this attribute is used to filter out events. the format is:\n" \
            "                logfilter format:  <eventid>,<text>;<eventid>,text;....\n" \
            "                Multiple filters must be separated by ';'\n" \
            "-a <seconds>    Max age of record in etcd. Default: 600\n" \
            "-t <seconds>    Timeout in seconds when communicating with etcd server. Default: 60.\n" \
            "\ncurrent command: \n%s\n" % (' '.join(self._argv))
        self.outval = 3
        self.done = True
        self.stop = time.time

    def run(self):
        if not self.ready: return
        self.start = time.time()
        self.running = True
            
        if self._module == 'cpu':
            self._cpu()
        elif self._module == 'ram':
            self._ram()
        elif self._module == 'swap':
            self._swap()
        elif self._module == 'log':
            self._log()
        elif self._module == 'services':
            self._services()
        elif self._module == 'hddrives':
            self._hddrives()
        elif self._module == 'uptime':
            self._uptime()
        else:
            self.outmsg = "UNKNOWN - Invalid Module %s" % self._module
            self.outval = 3
        self.done = True
        self.running = False
        self.stop = time.time()

    def _get(self, key):
        try:
            res=self._etcdclient.get(key).value
            self._data = json.loads(res)

        except IndexError as e:
            return self.unknown(str(e))
        except etcd.EtcdKeyNotFound:
            return self.unknown("ServerID \"%s\" not found in the database." % self._host)
        except ValueError:
            return self.unknown("Data for ServerID \"%s\" is corrupt." % self._host)
        except etcd.EtcdException as e:
            return self.unknown("Server \"%s\" not responding." % str(e))
        if 'epoch' not in self._data:
            self.unknown("Epoch not found in data.")
            return
        age_secs = time.time() - self._data.get('epoch', 0)
        if age_secs > self._max_age:
            self.unknown("Data is too old %d seconds." % age_secs)
            return
        self._data=self._data['data']

    def _cpu(self):
        self._get("/samanamonitor/servers/%s/classes/Win32_PerfFormattedData_PerfOS_Processor" % self._host)
        if self.done: return

        if self._data is None:
            self.unknown("Data has not been fetched.")
            return

        state = "UNKNOWN"
        graphmax = 100

        if 'PercentIdleTime' not in self._data or 'PercentUserTime' not in self._data \
            or 'PercentInterruptTime' not in self._data or 'PercentPrivilegedTime' not in self._data:
            self.unknown("Missing attributes from class")
            return

        val = 100.0 - float(self._data['PercentIdleTime'])

        perfusage = " | Load=%d;%s;%s;0;%d" % (
            int(val), 
            intstr(self._warn), 
            intstr(self._crit), 
            graphmax)
        perfusage += " PercentIdleTime=%d;;;0;100" % int(self._data['PercentIdleTime'])
        perfusage += " PercentUserTime=%d;;;0;100" % int(self._data['PercentUserTime'])
        perfusage += " PercentPrivilegedTime=%d;;;0;100" % int(self._data['PercentPrivilegedTime'])
        perfusage += " PercentInterruptTime=%d;;;0;100" % int(self._data['PercentInterruptTime'])

        msg = "CPU Usage %0.f %%" % val
        if self._crit is not None and val > self._crit:
            self.critical(msg, perf_data=perfusage)
        elif self._warn is not None and val > self._warn:
            self.warning(msg, perf_data=perfusage)
        else:
            self.ok(msg, perf_data=perfusage)

    def _ram(self):
        self._get("/samanamonitor/servers/%s/classes/Win32_OperatingSystem" % self._host)
        if self.done: return

        if self._data is None:
            raise Exception("Data has not been fetched.")

        state = "UNKNOWN"
        
        total = float(self._data['TotalVisibleMemorySize']) / 1024.0
        free = float(self._data['FreePhysicalMemory']) / 1024.0
        used = total - free
        percused = used * 100.0 / total
        percfree = free * 100.0 / total

        perfused = " | PercentMemoryUsed=%d;%s;%s;0;100 MemoryUsed=%d;;;0;%d" % (
            percused,
            intstr(self._warn),
            intstr(self._crit),
            free,
            total)

        msg = "Physical Memory: Total: %.2fGB - " \
            "Used: %.2fGB (%.1f%%) - Free %.2fGB (%.2f%%)" % \
                (total, used, percused, free, percfree)

        if self._crit is not None and percused > self._crit:
            self.critical(msg, perf_data=perfusage)
        elif self._warn is not None and percused > self._warn:
            self.warning(msg, perf_data=perfusage)
        else:
            self.ok(msg, perf_data=perfusage)

    def _swap(self):
        self._get("/samanamonitor/servers/%s/classes/Win32_OperatingSystem" % self._host)
        if self.done: return

        if self._data is None:
            raise Exception("Data has not been fetched.")

        state = "UNKNOWN"

        TotalSwapSpaceSize = self._data.get('TotalSwapSpaceSize')
        if TotalSwapSpaceSize is None or TotalSwapSpaceSize == 0.0:
            self.outval = 0
            self.outmsg = 'OK - No Page File configured | Swap Memory Used=0;0;0;0;100'
            return

        total = float(TotalSwapSpaceSize) / 1024
        free = float(self._data.get('FreeSpaceInPagingFiles', 0.0)) / 1024
        used = total - free
        percused = used * 100.0 / total
        percfree = free * 100.0 / total

        perfused = "| Total_PercentageUsed=%d;%s;%s;0;100" % (
            percused,
            intstr(self._warn),
            intstr(self._crit))

        self._get("/samanamonitor/servers/%s/classes/Win32_PageFileUsage" % self._host)
        if self.done: return

        for pf in self._data:
            name = pf['Caption'].replace(':', '_').replace('\\', '').replace('.', '_')
            perfused += " %s_AllocatedBaseSize=%d;;;;" % (name, int(pf['AllocatedBaseSize']))
            perfused += " %s_CurrentUsage=%d;;;;" % (name, int(pf['CurrentUsage']))
            perfused += " %s_PercentageUsage=%d;;;;" % (name, int((int(pf['CurrentUsage'])*100/int(pf['AllocatedBaseSize'])) if pf['AllocatedBaseSize'] != 0 else 0))
            perfused += " %s_PeakUsage=%d;;;;" % (name, int(pf['PeakUsage']))

        msg = "Swap Memory: Total: %.2fGB - " \
            "Used: %.2fGB (%.1f%%) - Free %.2fGB (%.2f%%)" % (
            total, used, percused, free, percfree)

        if self._crit is not None and percused > self._crit:
            self.critical(msg, perf_data=perfusage)
        elif self._warn is not None and percused > self._warn:
            self.warning(msg, perf_data=perfusage)
        else:
            self.ok(msg, perf_data=perfusage)


    def _log(self):
        logname = self._submod
        self._get("/samanamonitor/servers/%s/classes/Win32_NTLogEvent/%s" % (self._host, logname))
        if self.done: return

        if self._data is None:
            raise Exception("Data has not been fetched.")

        excl = self._excl
        state = "UNKNOWN"
        messages = ""
        eventtype_names = [
            "None",
            "Error",
            "Warning",
            "AuditSuccess",
            "AuditFailure"
        ]
        event_count = [
            0, # None
            0, # Error
            0, # Warning
            0, # Information
            0, # Audit Success
            0, # Audit Failure
        ]

        events = self._data

        if isinstance(events, dict):
            if len(events) == 0:
                events = []
            else:
                events = [ events ]
        elif isinstance(events, list):
            pass
        else:
            raise Exception('UNKNOWN - Invalid log data(%s): %s' % (logname, data['Events'][logname]))

        addl = "\n"
        val=0
        for event in events:
            skip=False
            for eid, msg in self._logfilters:
                if event['EventCode'] == eid:
                    if re.search(msg, event['Message']) is not None:
                        skip=True
                        break
            if skip: continue
            event_count[int(event['EventType'])] += 1
            val += 1
            if len(addl) > 4096: continue
            addl += "%s - EventId:%s Source:\"%s\" Message:\"%s\"\n" % \
                    (event.get('Type', 'Unknown'),
                        event.get('EventCode', 'Unknown'),
                        event.get('SourceName', 'Unknown'),
                        event.get('Message', '')[:80])

        if self._crit is not None and val > self._crit:
            state = "CRITICAL"
            self.outval = 2
        elif self._warn is not None and val > self._warn:
            state = "WARNING"
            self.outval = 1
        else:
            state = "OK"
            self.outval = 0

        perfused = " |"
        for i in range(1, len(eventtype_names)):
            perfused += " %s=%d;;;;" % (eventtype_names[i], event_count[i])

        self.outmsg = "%s - Error or Warning Events=%d %s %s" %  \
            (state, val, perfused, addl)

    def _uptime(self):
        self._get("/samanamonitor/servers/%s/classes/Win32_OperatingSystem" % self._host)
        if self.done: return

        if self._data is None:
            raise Exception("Data has not been fetched.")

        state = "UNKNOWN"

        LastBootUpTime=self._data['LastBootUpTime']['Datetime']
        timezone=LastBootUpTime[-6:]
        timezonesecs=(int(timezone[-2:])+int(timezone[1:3])*60) * (-1 if timezone[0] == '+' else 1) *60
        lbt=time.strptime(LastBootUpTime.split('.')[0], "%Y-%m-%dT%H:%M:%S")
        val=(time.time() - time.mktime(lbt)+timezonesecs)/3600

        if self._crit is not None and val > self._crit:
            state = "CRITICAL"
            self.outval = 2
        elif self._warn is not None and val > self._warn:
            state = "WARNING"
            self.outval = 1
        else:
            state = "OK"
            self.outval = 0

        perfused = "| uptime=%.0f;%s;%s;;" % \
            (val, intstr(self._warn), intstr(self._crit))
        self.outmsg = "%s - Uptime of server is %.0f Hours %s\n%s" % \
            (state, val, perfused, ' '.join(self._argv))

    def _services(self):
        self._get("/samanamonitor/servers/%s/classes/Win32_Service" % (self._host, logname))
        if self.done: return

        if self._data is None:
            raise Exception("Data has not been fetched.")

        state = 'UNKNOWN'
        r = 0
        s = 0
        stopped_services = '\nStopped Services:\n'
        for service in self._data:
            displayname = service.get('DisplayName').lower()
            name = service.get('ServiceName').lower()
            if self._excl is not None and self._excl != '' and \
                    (re.search(self._excl, displayname) is not None or \
                        re.search(self._excl, name) is not None):
                continue
            if re.search(self._incl, displayname) is not None or \
                re.search(self._incl, name) is not None:
                status = service.get('Status')
                state = service.get('State', 'Stopped')
                if (isinstance(status, int) and status == 4) or state == 'Running':
                    r += 1
                else:
                    s += 1
                    stopped_services += " * %s(%s)\n" % \
                        (service.get('DisplayName', 'Unknown'), name)

        if self._crit is not None and s >= self._crit:
            state = "CRITICAL"
            self.outval = 2
        elif self._warn is not None and s >= self._warn:
            state = "WARNING"
            self.outval = 1
        else:
            state = "OK"
            self.outval = 0

        perfused = " | Stopped=%d;%s;%s;; Running=%d;;;;" % \
            (s, intstr(self._warn),
                intstr(self._crit), r)
        self.outmsg = "%s - %d Services Stopped - %d Services Running %s\n%s" % \
            (state, s, r, perfused, stopped_services if self.outval > 0 else '')

    def _hddrives(self):
        self._get("/samanamonitor/servers/%s/classes/Win32_LogicalDisk" % self._host)
        if self.done: return

        if self._data is None:
            raise Exception("Data has not been fetched.")

        state = 'UNKNOWN'

        disk_messages = []
        disk_addl = []
        disk_perfs = []
        status_crit = 0
        status_warn = 0

        def check_disk(disk):
            totalg = float(disk['Size']) / 1024.0 / 1024.0 / 1024.0
            freeg = float(disk['FreeSpace']) / 1024.0 / 1024.0 / 1024.0
            usedg = totalg - freeg
            percused =  usedg / totalg * 100.0
            disk_messages.append(" %s=%.1f%%Used" % (disk.get('Name'), percused))
            addl = "Disk %s Total: %.2fG - Used: %.2fG (%.1f%%)" % (
                disk['Name'],
                totalg,
                usedg,
                percused)
            disk_addl.append(addl)
            perf = "%s=%.1f;%s;%s;0;100 " % (
                disk['Name'].replace(':', '').lower(),
                percused,
                intstr(self._warn),
                intstr(self._crit))
            disk_perfs.append(perf)
            if self._crit is not None and percused >= self._crit:
                disk_addl[-1] += "***"
                return 2
            elif self._warn is not None and percused >= self._warn:
                disk_addl[-1] += "***"
                return 1
            return 0

        disklist = self._data
        if isinstance(disklist, dict):
            disklist = [ disklist ]
        elif isinstance(disklist, list):
            pass
        else:
            disklist = []

        for disk in disklist:
            if int(disk['DriveType']) != 3:
                continue
            s = check_disk(disk)
            if s == 2:
                status_crit += 1
            elif s == 1:
                status_warn += 1

        if status_crit > 0:
            state = "CRITICAL"
            self.outval = 2
        elif status_warn > 0:
            state = "WARNING"
            self.outval = 1
        else:
            state = "OK"
            self.outval = 0

        self.outmsg = "%s - %s | %s\n%s" % \
            (state, ",".join(disk_messages), " ".join(disk_perfs), "\n".join(disk_addl))

