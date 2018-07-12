import pytest
import time

from sls.main import SyslogStats

def test_smoke_01 ():
    sls = SyslogStats(cfg = dict (
        loglevel = 'debug',
        filename = 'data/syslog',
    ))

    stats = sls.run()

    assert stats.get ('msg_length_avg') == 36.0
    assert stats.get ('count_emergency') == -1
    assert stats.get ('count_alert') == -1
    assert time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime (stats['oldest'])) == 'Thu, 25 Jan 1900 05:06:34 +0000'
    assert time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime (stats['youngest'])) == 'Sun, 07 Oct 1900 10:09:00 +0000'
