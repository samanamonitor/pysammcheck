import sys, getopt
from .check import SAMMCheck
from . import __version__
from etcd import Client
import json
import time
import etcd
import random

class SAMMDummyCheck(SAMMCheck):
    _etcdserver = "127.0.0.1"
    _etcdport = 2379
    timeout = 60
    _module_name = "Dummy"
    def __init__(self, argv):
        super().__init__(argv)

    def process_args(self):
        try:
            opts, args = getopt.getopt(self._argv, "hH:E:t:")
            for opt, arg in opts:
                if opt == '-h':
                    return self.help()
                elif opt == "-H":
                    self._hostid = arg
                elif opt == "-E":
                    temp = arg.split(':')
                    self._etcdserver = temp[0]
                    if len(temp) > 1:
                        self._etcdport = int(temp[1])
                elif opt == "-t":
                    self.timeout = arg
                else:
                    return self.help()

        except getopt.GetoptError as e:
            return self.help(str(e))
        self._etcdclient = etcd.Client(host=self._etcdserver, port=self._etcdport, read_timeout=self.timeout)

    def check_args(self):
        super().check_args()
        if not self.ready: return
        self.ready = False

        try:
            self.timeout = int(self.timeout)
        except ValueError:
            self.unknown("Timeout can only be an integer.")
        self.ready = True

    def __repr__(self):
        return "<%s etcdserver=%s:%d>" % (self.__class__.__name__, self._etcdserver, self._etcdport)

    def help(self, msg=""):
        self.outmsg =  "%s\n" % msg \
            + self._base_help % (self._module_name, __version__, self._argv[0]) + \
            "-E <etcdserver> Etcd server and port <ip>:<port> port is optional" \
            "\ncurrent command: \n%s\n" % (' '.join(self._argv))
        self.outval = 3
        self.done = True
        self.stop = time.time

    def run(self):
        if not self.ready: return
        self.start = time.time()
        key='/samanamonitor/servers/%s/classes/%s'
        host=self._hostid

        PercentUserTime=random.gauss(mu=20, sigma=15.0)
        PercentPrivilegedTime=random.gauss(mu=5, sigma=3)
        class_name="Win32_PerfFormattedData_PerfOS_Processor"
        self._etcdclient.set(key % (host, class_name), json.dumps({
            'epoch': time.time(),
            'data':{
                'PercentIdleTime': 100-PercentUserTime-PercentPrivilegedTime,
                'PercentUserTime': PercentUserTime,
                'PercentPrivilegedTime': PercentPrivilegedTime,
                'PercentInterruptTime': 0
                }
            }))


        class_name="Win32_OperatingSystem"
        self._etcdclient.set(key % (host, class_name), json.dumps({
            'epoch': time.time(),
            'data': {
                'TotalVisibleMemorySize': 1048576,
                'FreePhysicalMemory': random.gauss(mu=524288, sigma=1000),
                'TotalSwapSpaceSize': 1048576,
                'FreeSpaceInPagingFiles': random.gauss(mu=524288, sigma=1000),
                'LastBootUpTime': {'Datetime': '2023-04-24T00:42:29.485306-04:00'}
                }
            }))

        class_name="Win32_PageFileUsage"
        self._etcdclient.set(key % (host, class_name), json.dumps({
            'epoch': time.time(),
            'data': [{
                'Caption': "C:\\swap",
                'AllocatedBaseSize': 1048576,
                'CurrentUsage': random.gauss(mu=524288, sigma=1000),
                'PeakUsage': 0
                }]}))

        class_name="Win32_NTLogEvent/Application"
        self._etcdclient.set(key % (host, class_name), json.dumps({
            'epoch': time.time(),
            'data': [{
                'EventCode': "1000",
                'Message': "Error...this is a test message",
                'EventType': 1,
                'Type': 'Error',
                'SourceName': "This is a source name"
                },{
                'EventCode': "1001",
                'Message': "Warning...this is a test message",
                'EventType': 2,
                'Type': 'Warning',
                'SourceName': "This is a source name"
                }]}))

        class_name="Win32_NTLogEvent/System"
        self._etcdclient.set(key % (host, class_name), json.dumps({
            'epoch': time.time(),
            'data': [{
                'EventCode': "1000",
                'Message': "Error...this is a test message",
                'EventType': 1,
                'Type': 'Error',
                'SourceName': "This is a source name"
                },{
                'EventCode': "1001",
                'Message': "Warning...this is a test message",
                'EventType': 2,
                'Type': 'Warning',
                'SourceName': "This is a source name"
                }]}))

        class_name="Win32_Service"
        self._etcdclient.set(key % (host, class_name), json.dumps({
            'epoch': time.time(),
            'data': [{
                'DisplayName': 'This is a service 1',
                'ServiceName': 'servicename1',
                'Status': 4,
                'State': "Running"
                },{
                'DisplayName': 'This is a service 2',
                'ServiceName': 'servicename2',
                'Status': 1,
                'State': "Stopped"
                }]}))

        class_name="Win32_LogicalDisk"
        self._etcdclient.set(key % (host, class_name), json.dumps({
            'epoch': time.time(),
            'data': [{'Access': '0', 'Availability': None, 'BlockSize': None, 'Caption': 'C:', 
            'Compressed': 'false', 'ConfigManagerErrorCode': None, 'ConfigManagerUserConfig': None, 
            'CreationClassName': 'Win32_LogicalDisk', 'Description': 'Local Fixed Disk', 'DeviceID': 'C:', 
            'DriveType': '3', 'ErrorCleared': None, 'ErrorDescription': None, 'ErrorMethodology': None, 'FileSystem': 
            'NTFS', 'FreeSpace': '35471372288', 'InstallDate': None, 'LastErrorCode': None, 'MaximumComponentLength': '255', 
            'MediaType': '12', 'Name': 'C:', 'NumberOfBlocks': None, 'PNPDeviceID': None, 'PowerManagementSupported': None, 
            'ProviderName': None, 'Purpose': None, 'QuotasDisabled': 'true', 'QuotasIncomplete': 'false', 'QuotasRebuilding': 
            'false', 'Size': '106837307392', 'Status': None, 'StatusInfo': None, 'SupportsDiskQuotas': 'true', 
            'SupportsFileBasedCompression': 'true', 'SystemCreationClassName': 'Win32_ComputerSystem', 
            'SystemName': 'SMNNOVCTXVDA1', 'VolumeDirty': 'false', 'VolumeName': {}, 'VolumeSerialNumber': '1441F0E9'}, 
            {'Access': '0', 'Availability': None, 'BlockSize': None, 'Caption': 'F:', 'Compressed': 'false', 
            'ConfigManagerErrorCode': None, 'ConfigManagerUserConfig': None, 'CreationClassName': 'Win32_LogicalDisk', 
            'Description': 'Local Fixed Disk', 'DeviceID': 'F:', 'DriveType': '3', 'ErrorCleared': None, 'ErrorDescription': None, 
            'ErrorMethodology': None, 'FileSystem': 'NTFS', 'FreeSpace': '174804992', 'InstallDate': None, 'LastErrorCode': None, 
            'MaximumComponentLength': '255', 'MediaType': '12', 'Name': 'F:', 'NumberOfBlocks': None, 'PNPDeviceID': None, 
            'PowerManagementSupported': None, 'ProviderName': None, 'Purpose': None, 'QuotasDisabled': 'true', 
            'QuotasIncomplete': 'false', 'QuotasRebuilding': 'false', 'Size': '524283904', 'Status': None, 'StatusInfo': None, 
            'SupportsDiskQuotas': 'true', 'SupportsFileBasedCompression': 'true', 'SystemCreationClassName': 'Win32_ComputerSystem', 
            'SystemName': 'SMNNOVCTXVDA1', 'VolumeDirty': 'false', 'VolumeName': 'System Reserved', 'VolumeSerialNumber': '604115A1'}]}))

        state = "OK"
        self.outval = 0
        self.outmsg = "%s - Data Uploaded" % (state)

        self.done = True
        self.running = False
        self.stop = time.time()
        
