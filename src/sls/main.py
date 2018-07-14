import os
import logging
import re
import time
import functools
import calendar
import itertools
import multiprocessing


class SyslogStats():
    """ read a syslog file and create some funky statistics
        format is assumed to be according to RFC 3164

        assume all log messages from one year; SyslogStats will assume it to be 1900
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

        # XXX assuming log/ directory
        handler = logging.FileHandler ('%s/../log/sls.log' % os.path.dirname (os.path.realpath (__file__)))
        handler.setFormatter (logging.Formatter (fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger = multiprocessing.get_logger()
        self.logger.addHandler (handler)
        self.logger.setLevel (loglevel)

        self.chunksize = 1
        self.process_count = cfg.get ('process_count') or 1


    def bookkeeping (self, results):
        """ take a list of results, anslyse them and return a stats-ds
        """

        stats = dict (
            msg_length_avg  = -1,
            msg_lengths     = [],
            count_emergency = 0,
            count_alert     = 0,
            oldest          = calendar.timegm (time.strptime("31 Dec 1900", "%d %b %Y")),
            youngest        = calendar.timegm (time.strptime("1 Jan 1900", "%d %b %Y")),
            lines_processed = 0,
        )

        for result in results:
            stats['msg_lengths'].append (len (result['message']))
            stats['lines_processed'] += 1

            if result['severity'] == 'Emergency':
                stats['count_emergency'] += 1
            elif result['severity'] == 'Alert':
                stats['count_alert'] += 1

            if result['timestamp'] < stats['oldest']:
                 stats['oldest'] = result['timestamp']
            elif result['timestamp'] > stats['youngest']:
                 stats['youngest'] = result['timestamp']

        stats['msg_length_avg'] = sum (stats['msg_lengths']) / len (stats['msg_lengths'])

        return stats


    def run (self):
        """ execute an instance of SLS
            returns analysis per-host and global ('summary')
        """

        start_time = time.time()

        with multiprocessing.Pool (self.process_count) as p:
            results = p.map (
                self.disect_line,
                self.lines(),
                self.chunksize,
            )

        stats = dict()

        for hostname, group in itertools.groupby (results, lambda r: r.get ('hostname')):
            stats[hostname] = self.bookkeeping ([g for g in group])

        # prevent round-off errors
        # this runs only once
        stats['summary'] = self.bookkeeping (results)

        self.log_stats (stats = stats)

        self.logger.info ('processed {lines} lines in {secs} using {procs} process{plural}'.format (
            lines = stats['summary']['lines_processed'],
            secs = time.time() - start_time,
            procs = self.process_count,
            plural = self.process_count > 1 and 'es' or '',
        ))

        return stats


    def log_stats (self, **kwa):
        for host, data in kwa.get ('stats').items():
            self.logger.info ('[{}] average message length: {}'.format (host, data['msg_length_avg']))
            self.logger.info ('[{}] count emergency severities: {}'.format (host, data['count_emergency']))
            self.logger.info ('[{}] count alert severities: {}'.format (host, data['count_alert']))
            self.logger.info ('[{}] oldest: {}'.format (host, time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime (data['oldest']))))
            self.logger.info ('[{}] youngest: {}'.format (host, time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime (data['youngest']))))


    def lines (self, **kwa):
        with open (self.filename, 'r') as fh:
            for line in fh:
                yield line.strip()


    @classmethod
    def severity (_, **kwa):
        return list (filter (lambda s: (kwa.get ('priority') - s) % 8 == 0, range (0,8))).pop()

        # or shortcircuit it
        #
        # return (
        #     (((priority    ) % 8 == 0) and 0) or
        #     (((priority - 1) % 8 == 0) and 1) or
        #     (((priority - 2) % 8 == 0) and 2) or
        #     (((priority - 3) % 8 == 0) and 3) or
        #     (((priority - 4) % 8 == 0) and 4) or
        #     (((priority - 5) % 8 == 0) and 5) or
        #     (((priority - 6) % 8 == 0) and 6) or
        #     (((priority - 7) % 8 == 0) and 7)
        # )


    @classmethod
    def disect_line (cls, line):
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
        #
        priority = int (m.group ('priority'))
        severity = cls.severity (priority = priority)
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
