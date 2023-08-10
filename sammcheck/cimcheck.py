import sys, getopt
import time
from .check import SAMMCheck
from . import __version__
from sammwr.wmi import WMIQuery
import re, string

intstr = lambda x: str(x) if x is not None else ''
class SAMMCimCheck(SAMMCheck):
    _username=None
    _password=None
    _class_name=None
    _property=None
    _property_max=None
    _where=None
    _port=5985
    _module_name="CIM"
    _label=None
    _label_column=None
    _invert_percentage=False
    def __init__(self, argv):
        super().__init__(argv)
        self._endpoint = "http://%s:%d/wsman" % (self._host, self._port)
        self._wql="SELECT * FROM %s%s" % (self._class_name, intstr(self._where))
        self._wmi=WMIQuery(wql=self._wql, endpoint=self._endpoint, username=self._username, password=self._password)
        selectlist = [self._property]
        if self._property_max is not None:
            selectlist += [self._property_max]
        if self._label_column is not None:
            selectlist += [self._label_column]


    def process_args(self):
        try:
            opts, args = getopt.getopt(self._argv, "hH:c:w:u:p:C:P:W:M:L:l:I")
            for opt, arg in opts:
                if opt == '-h':
                    return self.help()
                elif opt == "-H":
                    self._host = arg
                elif opt == "-c":
                    try:
                        self._crit = int(arg)
                    except ValueError:
                        self.unknown("Invalid critical value(%s). Must be integer." % arg)
                elif opt == "-w":
                    try:
                        self._warn = int(arg)
                    except ValueError:
                        self.unknown("Invalid warning value(%s). Must be integer." % arg)
                elif opt == "-u":
                    self._username = arg
                elif opt == "-p":
                    self._password = arg
                elif opt == "-C":
                    self._class_name = arg
                elif opt == "-P":
                    self._property = arg
                elif opt == "-M":
                    self._property_max = arg
                elif opt == "-I":
                    self._invert_percentage = True
                elif opt == "-L":
                    self._label = arg
                elif opt == "-l":
                    self._label_column = arg
                elif opt == "-W":
                    self._where = " WHERE %s" % arg
                else:
                    return self.help()

        except getopt.GetoptError as e:
            return self.help(str(e))

    def check_args(self):
        super().check_args()
        if not self.ready:
            return
        self.ready = False
        if self._username is None:
            self.unknown("Username not specified.")
            return
        if self._password is None:
            self.unknown("Password not specified.")
            return
        if self._class_name is None:
            self.unknown("CIM Class not specified.")
            return
        if self._property is None:
            self.unknown("CIM Properties not specified.")
            return
        self.ready = True

    def __repr__(self):
        return "<%s host=%s:%d>" % (self.__class__.__name__, self._host, self._port)

    def help(self, msg=""):
        self.outmsg =  "%s\n" % msg \
            + self._base_help % (self._module_name, __version__, self._argv[0]) + \
            "-H <host>       Host server address\n" \
            "-w <warning>    Warning threshold\n" \
            "-c <critical>   Critical threshold\n" \
            "-u <username>   Username with privileges to query CIM classes\n" \
            "-p <password>   Password\n" \
            "-C <class name> CIM Class name\n" \
            "-P <property>   CIM Class property name\n" \
            "-M <prop max>   CIM Class property max value. Used for percentage calculation with property.\n" \
            "-I              Invert percentage value (100%-percentage_value)\n" \
            "-L <label>      Label to use to show data\n" \
            "-l <label col>  Column name that contains the label for the data\n" \
            "-W <string>     WHERE clause to filter WQL output\n" \
            "\ncurrent command: \n%s\n" % (' '.join(self._argv))
        self.outval = 3
        self.done = True
        self.stop = time.time

    def run(self):
        if not self.ready: return
        self.start = time.time()
        self.running = True


        #self._result=self._wmi.wql(self._wql)
        #if not isinstance(self._result, list):
        #    self.unknown("Invalid data received. data=%s" % str(self._result))
        #    return
        #if len(self._result) < 1:
        #    self.unknown("No results received. data=%s" % str(self._result))
        #    return

        self._value = []
        msg = ""
        addl_data = ""
        perf_data = " |"
        special_chars=re.escape(string.punctuation.replace(".", "").replace("_", ""))
        instance_count = 0
        for r in self._wmi:
            instance_count += 1
            if self._property not in r:
                self.unknown("Property %s not in results. data=%s" % (self._property, str(self._result)))
                return

            pmax = None
            status = 0
            value = None
            if self._property_max is not None:
                if self._property_max not in r:
                    self.unknown("Property max %s not in results. data=%s" % (self._property_max, str(self._result)))
                    return
                try:
                    pmax = int(r[self._property_max])
                    if pmax == 0:
                        raise ValueError
                except (ValueError, TypeError):
                    self.unknown("Property max %s value is not integer. data=%s" % (self._property_max, str(self._result)))
                    return

            try:
                if pmax is None:
                    value = int(r[self._property])
                else:
                    value = int(r[self._property]) / pmax * 100
                    if self._invert_percentage:
                        value = 100 - value
                self._value += [value]
                if self._crit is not None and value > self._crit:
                    status = 2
                if self._warn is not None and value > self._warn and status < 1:
                    status = 1

            except (ValueError, ZeroDivisionError):
                self.unknown("Value received is not integer or zero. value=%s" % self._value)
                return

            label_array = []
            if self._label is not None:
                label_array += [self._label]
            if self._label_column is not None and self._label_column in r:
                label_array += [r[self._label_column]]
            if self._label is None and self._label_column is None:
                label = self._property
            else:
                label = '.'.join(label_array)


            addl_data+="%s = %d%s\n" % (label, value, "%" if pmax is not None else "")
            label = re.sub('['+special_chars+' ]', '_', label).lower()
            perf_data+=" '%s'=%d;%s;%s;;" % (label, value, intstr(self._warn), intstr(self._crit))

        if instance_count == 1:
            msg = addl_data
            addl_data = ""


        if status == 2:
            self.critical(msg, perf_data=perf_data, addl=addl_data)
        elif status == 1:
            self.warning(msg, perf_data=perf_data, addl=addl_data)
        else:
            self.ok(msg, perf_data=perf_data, addl=addl_data)

        self.done = True
        self.running = False
        self.stop = time.time()
