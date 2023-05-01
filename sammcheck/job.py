import importlib
from .utils import str2array
from threading import Thread
import logging

test_str=b'job_id=1270944\0type=0\0command=check_sammworker sammcheck.etcdcheck.SAMMEtcdCheck -H test1 -E 192.168.69.11:2379 -m cpu -w 35 -c 45\0timeout=60'.decode('ascii')

class SAMMJob():
    def __init__(self, raw_data):
        param_list=raw_data.split('\0')
        self.thread = None
        self._data = {}
        for p in param_list:
            if '=' not in p:
                continue
            (k,v) = p.split('=')
            self._data[k] = v
        if 'job_id' not in self._data:
            raise Exception("job_id not in raw_data. %s" % raw_data)
        if 'timeout' not in self._data:
            raise Exception("timeout not in raw_data. %s" % raw_data)
        self._data['timeout'] = int(self._data['timeout'])

        self.argv = str2array(self._data['command'])
        if len(self.argv) < 2:
            raise Exception("Invalid number of parameters. %s" % raw_data)
        self.plugin_name = self.argv[0].split('/')[-1]
        self.module_arr = self.argv[1].split('.')
        if len(self.argv) > 2:
            self.params = self.argv[2:]
        else:
            self.params = []
        self.module = importlib.import_module('.'.join(self.module_arr[:-1]))
        _class = getattr(self.module, self.module_arr[-1])
        try:
            self.check = _class(self.params, timeout=self.timeout)
        except Exception as e:
            print("************** ERROR %s" % e)
            raise
        #self.logger = logging.getLogger("SAMMJob")
        #self.logger.setLevel(logging.DEBUG)
        #ch = logging.StreamHandler()
        #ch.setLevel(logging.DEBUG)
        #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        #ch.setFormatter(formatter)
        #self.logger.addHandler(ch)
        #sself.logger.debug("test %s" % raw_data)
        #print(self.check)

    def run(self):
        self.thread = Thread(target=self.check.run, args=())
        self.thread.daemon = True
        self.thread.start()

    def still_running(self):
        return self.thread.is_alive()

    def __str__(self):
        if not self.check.done:
            data = {
                'job_id': self.job_id,
                'type': self.job_type,
                'start': self.check.start,
                'stop': self.check.stop,
                'runtime': self.check.runtime,
                'outstd': str(self.check),
                'outerr': 'An error happened',
                'exited_ok': 0,
                'wait_status': self.check.outval * 0x100
            }
        else:
            data = {
                'job_id': self.job_id,
                'type': self.job_type,
                'start': self.check.start,
                'stop': self.check.stop,
                'runtime': self.check.runtime,
                'outstd': str(self.check),
                'outerr': '',
                'exited_ok': 1,
                'wait_status': self.check.outval * 0x100
        }
        return 'job_id=%(job_id)s\0type=%(type)s\0start=%(start)f\0' \
            'stop=%(stop)f\0runtime=%(runtime)f\0outstd=%(outstd)s\0' \
            'wait_status=%(wait_status)d\0exited_ok=%(exited_ok)d\0' \
            'outerr=%(outerr)s\0\1\0\0\0' % data

    @property
    def job_id(self):
        return self._data['job_id']

    @property
    def job_type(self):
        return self._data['type']

    @property
    def command(self):
        return self._data['command']

    @property
    def timeout(self):
        return self._data['timeout']
