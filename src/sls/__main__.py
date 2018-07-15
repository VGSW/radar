import os
import yaml
import argparse

from sls.main import SyslogStats

def get_config ():
    """ load configuration from configfile
        command line options take precedence
    """

    parser = argparse.ArgumentParser()
    parser.add_argument (
        '-c', '--config',
        type   = str,
        action = 'store',
        dest   = 'configfile',
        help   = 'configfile location',
    )
    parser.add_argument (
        '-p', '--processes',
        type   = int,
        action = 'store',
        dest   = 'processes',
        help   = 'number of processes to execute',
    )
    parser.add_argument (
        '-f', '--filename',
        type   = str,
        action = 'store',
        dest   = 'filename',
        help   = 'syslog filename to use',
    )
    parser.add_argument (
        '-l', '--loglevel',
        type   = str,
        action = 'store',
        dest   = 'loglevel',
        help   = 'Loglevel',
    )
    parser.add_argument (
        '-L', '--logfile',
        type   = str,
        action = 'store',
        dest   = 'logfile',
        help   = 'logfile location',
    )

    args = parser.parse_args()

    configfile = ''

    if args.configfile:
        configfile = args.configfile
    elif os.path.isfile ('/etc/sls.yml'):
        configfile = '/etc/sls.yml'
    else:
        raise LookupError ('missing config file <%s>' % configfile)

    with open (configfile, 'r') as config:
        cfg = yaml.load (config)

    # commandline will take precedence over config file
    #
    args.processes and cfg.update (processes = args.processes)
    args.loglevel  and cfg.update (loglevel = args.loglevel)
    args.filename  and cfg.update (filename = args.filename)
    args.logfile   and cfg.update (logfile = args.logfile)

    return cfg


sls = SyslogStats (cfg = get_config())
sls.run()
