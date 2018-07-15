# import pytest
import time
import os
import yaml

from sls.main import SyslogStats


# relative to test_smoke.py
if os.path.isfile ('%s/../sls.yml' % os.path.dirname (os.path.realpath (__file__))):
    configfile = '%s/../sls.yml' % os.path.dirname (os.path.realpath (__file__))
elif os.path.isfile ('/etc/sls.yml'):
    configfile = '/etc/sls.yml'
else:
    raise LookupError ('missing config file <%s>' % configfile)

with open (configfile, 'r') as config:
    cfg = yaml.load (config)


def test_smoke_01 ():
    sls = SyslogStats (cfg = cfg)

    stats = sls.run().get ('summary')

    assert stats.get ('msg_length_avg') == 36.0
    assert stats.get ('count_emergency') == 0
    assert stats.get ('count_alert') == 0
    assert time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime (stats['oldest'])) == 'Thu, 25 Jan 1900 05:06:34 +0000'
    assert time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime (stats['youngest'])) == 'Sun, 07 Oct 1900 10:09:00 +0000'

def test_severity ():
    assert SyslogStats.severity (priority = 165) == 5
    assert SyslogStats.severity (priority = 34) == 2
    assert SyslogStats.severity (priority = 47) == 7
    assert SyslogStats.severity (priority = 13) == 5
    assert SyslogStats.severity (priority = 0) == 0
    assert SyslogStats.severity (priority = 191) == 7

def test_counters ():
    cfg.update (dict (
        loglevel = 'debug',
        filename = 'data/syslog.counters',
    ))

    sls = SyslogStats (cfg = cfg)

    stats = sls.run().get ('summary')

    assert stats.get ('count_emergency') == 2
    assert stats.get ('count_alert') == 2

def test_per_host ():
    cfg.update (dict (
        loglevel = 'debug',
        filename = 'data/syslog.per_host',
    ))

    sls = SyslogStats (cfg = cfg)

    stats = sls.run()

    assert stats.get ('mymachine').get ('msg_length_avg') == 33.0
    assert stats.get ('10.1.2.3').get ('msg_length_avg') == 48.0
    assert stats.get ('unicorn').get ('msg_length_avg') == 14.6
    assert stats.get ('FEDC:BA98:7654:3210:FEDC:BA98:7654:3210').get ('msg_length_avg') == 39.0
