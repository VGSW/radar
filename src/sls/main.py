"""
SyslogStats

Offers simple analysis of syslog files
"""


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
        final analysis is logged per host and per file in the logfile

        assume all log messages from one year; SyslogStats will assume it to be 1900
    """

    def __init__ (self, **kwa):
        """
        kwa.cfg.loglevel .... loglevel to use
        kwa.cfg.logfile ..... logfile
        kwa.cfg.processes ... number of processes in process pool
        kwa.cfg.filename .... syslogfile to analyse
        """

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

        logfile = cfg.get ('logfile') and cfg.get ('logfile') or 'log/sls.log'

        handler = logging.FileHandler (logfile)
        handler.setFormatter (logging.Formatter (fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger = multiprocessing.get_logger()
        self.logger.addHandler (handler)
        self.logger.setLevel (loglevel)

        self.processes = cfg.get ('processes') or os.cpu_count()


    def bookkeeping (self, **kwa):
        """ take a list of results, anslyse them and return a stats-ds
        """

        results = kwa.get ('results')

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

        # a number of nice and fancy list comprehensions,
        # while more elegant would loop a lot
        #
        # stats.update (dict(
        #     lines_processed = len (results),
        #     count_alert     = sum ([1 for r in results if r.get('severity') == 'Alert']),
        #     count_emergency = sum ([1 for r in results if r.get('severity') == 'Emergency']),
        #     oldest          = min ([r.get ('timestamp') for r in results]),
        #     youngest        = max ([r.get ('timestamp') for r in results]),
        #     msg_length_avg  = sum ([len (r.get ('message')) for r in results]) / len (results),
        # ))

        return stats


    def run (self):
        """ execute an instance of SLS
            returns analysis per-host and global ('summary')
        """

        start_time = time.time()

        with multiprocessing.Pool (self.processes) as p:
            results = [
                result for result in p.map (
                    self.disect_line,
                    self.lines (filename = self.filename),
                )
                if len (result)
            ]

            # leaving the context manager will apply terminate()
            p.close()
            p.join()

        lap_time = time.time()

        stats = dict()

        for hostname, group in itertools.groupby (
            sorted (results, key = lambda r: r.get ('hostname')),
            lambda r: r.get ('hostname')
        ):
            stats[hostname] = self.bookkeeping (results = [g for g in group])

        # prevent round-off errors
        # this runs only once
        stats['summary'] = self.bookkeeping (results = results)

        self.log_stats (stats = stats)

        self.logger.info ('processed {lines} lines in {secs} (disection: {secs_disection}, bookkeeping: {secs_bookkeeping}) using {procs} process{plural}'.format (
            lines = stats['summary']['lines_processed'],
            secs = time.time() - start_time,
            secs_disection = lap_time - start_time,
            secs_bookkeeping = time.time() - lap_time,
            procs = self.processes,
            plural = self.processes > 1 and 'es' or '',
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
        """ yield lines from file

            kwa.filename
        """
        filename = kwa.get ('filename')

        with open (filename, 'r') as fh:
            # omit empty lines
            for line in [l for l in [joe.strip() for joe in fh] if l]:
                yield line


    @classmethod
    def severity (_, **kwa):
        """ get severity from given priority

            kwa.priority
        """
        priority = kwa.get ('priority')

        return [
            severity for severity in range (8)
            if (priority - severity) % 8 == 0
        ].pop()

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

            line ... line to disect

            parts of the line are set in the returned dictionary at the keys of the same name
                priority
                severity
                facility
                timestamp
                hostname
                message
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

        if not m:
            return dict()

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
