import os
import yaml
import argparse

from sls.main import SyslogStats

def get_config ():
    """ load configuration from configfile
        command line options take precedence
    """

    # assume configfile at ./sls.yml
    # must start somewhere with configuration for keeping a certain amount of sanity
    #
    configfile = '%s/sls.yml' % os.path.dirname (os.path.realpath (__file__))

    if not os.path.isfile (configfile):
        raise LookupError ('missing config file <%s>' % configfile)

    with open (configfile, 'r') as config:
        cfg = yaml.load (config)

    parser = argparse.ArgumentParser()
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

    args = parser.parse_args()

    # commandline will take precedence over config file
    #
    args.processes and cfg.update (processes = args.processes)
    args.loglevel      and cfg.update (loglevel = args.loglevel)
    args.filename      and cfg.update (filename = args.filename)

    return cfg


sls = SyslogStats (cfg = get_config())
sls.run()
