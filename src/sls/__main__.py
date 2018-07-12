import os
import yaml

from sls.main import SyslogStats

configfile = '%s/sls.yml' % os.path.dirname (os.path.realpath (__file__))
if not os.path.isfile (configfile):
    raise LookupError ('missing config file <%s>' % configfile)

with open (configfile, 'r') as config:
    sls = SyslogStats (cfg = yaml.load (config))
    sls.run()
