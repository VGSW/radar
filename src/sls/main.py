import os
import logging
import re
import time
import functools
import calendar


class SyslogStats():
    """ read a syslog file and create some funky statistics
        format is assumed to be according to RFC 3164

        TODO: check dates and arithmetic
    """

    def __init__ (self, **kwa):
        cfg = kwa.get ('cfg')

        self.filename = cfg.get ('filename')

        loglevel = dict (
            debug = logging.DEBUG,
            info  = logging.INFO,
            warn  = logging.WARN,
            error = logging.ERROR,
        ).get (
            cfg.get ('loglevel'),
            logging.INFO,
        )

        handler = logging.FileHandler ('%s/../log/sls.log' % os.path.dirname (os.path.realpath (__file__)))
        handler.setFormatter (logging.Formatter (fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger = logging.getLogger ('sls')
        self.logger.addHandler (handler)
        self.logger.setLevel (loglevel)


    def run (self):
        stats = dict (
            msg_length_avg  = -1,
            msg_lengths     = [],
            count_emergency   = -1,
            count_alert       = -1,
            oldest          = calendar.timegm (time.strptime("31 Dec 1900", "%d %b %Y")),
            youngest        = calendar.timegm (time.strptime("1 Jan 1900", "%d %b %Y")),
        )

        for line in self.lines():
            result = self.disect_line (line)

            stats['msg_lengths'].append (len (result['message']))

            if result['severity'] == 'Emergency':
                stats['count_emergency'] += 1
            elif result['severity'] == 'Alert':
                stats['count_alert'] += 1

            if result['timestamp'] < stats['oldest']:
                 stats['oldest'] = result['timestamp']
            elif result['timestamp'] > stats['youngest']:
                 stats['youngest'] = result['timestamp']

        stats['msg_length_avg'] = (
            functools.reduce (lambda a, b: a + b, stats['msg_lengths']) /
            len (stats['msg_lengths'])
        )

        self.log_stats (stats = stats)

        return stats


    def log_stats (self, **kwa):
        stats = kwa.get ('stats')

        self.logger.debug ('average message length: {}'.format (stats['msg_length_avg']))
        self.logger.debug ('count emergency severities: {}'.format (stats['count_emergency']))
        self.logger.debug ('count alert severities: {}'.format (stats['count_alert']))
        self.logger.debug ('oldest: {}'.format (time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime (stats['oldest']))))
        self.logger.debug ('youngest: {}'.format (time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime (stats['youngest']))))


    def lines (self, **kwa):
        with open (self.filename, 'r') as fh:
            for line in fh:
                yield line.strip()


    def disect_line (self, line):
        """ take one syslog line and return a dict with its parts
        """

        compiled = re.compile (r"""
            <
            (?P<priority>\d{1,3})
            >
            # pretty ... that date sub regexp
            (?P<timestamp>\w{3}\ ((\ \d)|(\d\d))\ \d{2}:\d{2}:\d{2})
            (\ )
            # obviously this will match a lot of invalid IP addresses
            (?P<hostname>[\w.:]+)
            (\ )
            (?P<message>.+)
            .*
        """, re.VERBOSE)

        m = compiled.match (line)

        # priority = facility * 8 + severity

        priority = int (m.group ('priority'))

        severity = (
            (((priority    ) % 8 == 0) and 0) or
            (((priority - 1) % 8 == 0) and 1) or
            (((priority - 2) % 8 == 0) and 2) or
            (((priority - 3) % 8 == 0) and 3) or
            (((priority - 4) % 8 == 0) and 4) or
            (((priority - 5) % 8 == 0) and 5) or
            (((priority - 6) % 8 == 0) and 6) or
            (((priority - 7) % 8 == 0) and 7)
        )

        facility = int ((priority - severity) / 8)

        return dict (
            priority = priority,
            severity = {
                0 : 'Emergency',
                1 : 'Alert',
                2 : 'Critical',
                3 : 'Error',
                4 : 'Warning',
                5 : 'Notice',
                6 : 'Informational',
                7 : 'Debug',
            }.get (severity, 'UNKNOWN SEVERITY'),
            facility = {
                0  : 'kernel messages',
                1  : 'user-level messages',
                2  : 'mail system',
                3  : 'system daemons',
                4  : 'security/authorization messages (note 1)',
                5  : 'messages generated internally by syslogd',
                6  : 'line printer subsystem',
                7  : 'network news subsystem',
                8  : 'UUCP subsystem',
                9  : 'clock daemon (note 2)',
                10 : 'security/authorization messages (note 1)',
                11 : 'FTP daemon',
                12 : 'NTP subsystem',
                13 : 'log audit (note 1)',
                14 : 'log alert (note 1)',
                15 : 'clock daemon (note 2)',
                16 : 'local use 0  (local0)',
                17 : 'local use 1  (local1)',
                18 : 'local use 2  (local2)',
                19 : 'local use 3  (local3)',
                20 : 'local use 4  (local4)',
                21 : 'local use 5  (local5)',
                22 : 'local use 6  (local6)',
                23 : 'local use 7  (local7)',
            }.get (facility, 'UNKNOWN FACILITY'),
            # XXX this will assume the year 1900
            timestamp = calendar.timegm (time.strptime (m.group ('timestamp'), '%b %d %H:%M:%S')),
            hostname = m.group ('hostname'),
            message = m.group ('message'),
        )
