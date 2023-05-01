import sys, getopt
from .check import SAMMCheck
from etcd import Client
import json
import time
import etcd

class SAMMDummyCheck(SAMMCheck):
    def __init__(self, argv=None, timeout=60):
        self._etcdserver = "127.0.0.1"
        self._etcdport = 2379
        self.timeout = timeout
        super().__init__(argv)

    def process_args(self, argv):
        try:
            opts, args = getopt.getopt(argv, "hH:E:")
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
                else:
                    return self.help()

        except getopt.GetoptError as e:
            return self.help(str(e))
        self._etcdclient = etcd.Client(host=self._etcdserver, port=self._etcdport, read_timeout=self.timeout)


    def help(self, msg=""):
        self.outmsg =  "%s\n" \
            "Check Samana Dummy v2.0.0\n" \
            "This nagios plugin come with ABSOLUTELY NO WARRANTY and is property of\n" \
            "SAMANA GROUP LLC. If you want to use it, you should contact us before\n" \
            "to get a license.\n" \
            "Copyright (c) 2021 Samana Group LLC\n\n" \
            "Usage: %s  [options]\n" \
            "-H <hostid>     Id of the host in Etcd database\n" \
            "-E <etcdserver> Etcd server and port <ip>:<port> port is optional" \
            "-h              To get this help message\n" \
            "%s" % (msg, sys.argv[0], ' '.join(sys.argv))
        self.outval = 3
        self.done = True
        self.stop = time.time

    def run(self):
        self.start = time.time()
        key='/samanamonitor/servers/%s/classes/%s'
        host=self._hostid

        class_name="Win32_PerfFormattedData_PerfOS_Processor"
        self._etcdclient.set(key % (host, class_name), json.dumps({
            'epoch': time.time(),
            'data':{
                'PercentIdleTime': 90,
                'PercentUserTime': 5,
                'PercentPrivilegedTime': 1,
                'PercentInterruptTime': 0
                }
            }))


        class_name="Win32_OperatingSystem"
        self._etcdclient.set(key % (host, class_name), json.dumps({
            'epoch': time.time(),
            'data': {
                'TotalVisibleMemorySize': 1048576,
                'FreePhysicalMemory': 0,
                'TotalSwapSpaceSize': 1048576,
                'FreeSpaceInPagingFiles': 0,
                'LastBootUpTime': {'Datetime': '2023-04-24T00:42:29.485306-04:00'}
                }
            }))

        class_name="Win32_PageFileUsage"
        self._etcdclient.set(key % (host, class_name), json.dumps({
            'epoch': time.time(),
            'data': [{
                'Caption': "C:\\swap",
                'AllocatedBaseSize': 0,
                'CurrentUsage': 1048576,
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
        
