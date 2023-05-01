from setuptools import setup, find_packages
from sammcheck import __version__
import re

def set_control_version():
    with open("./debian/control.tmpl", "r") as src, open("./debian/control", "w") as dst:
        while True:
            datain = src.readline()
            if len(datain) == 0: break
            dataout = re.sub(r"%VERSION%", __version__, datain)
            dst.write(dataout)

if __name__ == "__main__":
    set_control_version()
    setup(
        name='sammcheck',
        version=__version__,
        packages=find_packages(include=['sammcheck', 'sammcheck.*']),
        scripts=['scripts/sammworker'],
        data_files=[('/usr/local/nagios/etc/sammworker', ['cfg/sammworker.cfg']),
            ('/usr/local/nagios/etc/objects/samana', ['cfg/commands-sammworker.cfg', 'cfg/role-sammworker-windows.cfg'])],
        install_requires=[ ]
    )
