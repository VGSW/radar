SyslogStats
===========

## What ?

SyslogStats will analyse syslog RFC 3164 compliant syslog files and log the following data per-host and globally:

    average message length
    number of emergency severities
    number of alert severities
    oldest entry
    youngest entry

## building

Use the very naive Makefile to build various targes

    build ....... build an image
    run ......... run the supplied syslog file from data/
    test ........ run tests in a one-off container
    inspect ..... get a shell in a one-off container
    clean ....... clean up
    distclean ... clean up image/container

One-off Containers will mount `./data/` into the container.

SyslogStats will (as a default) read `data/syslog` and distribute disection of lines to a configureable number of processes using multiprocessing.Pool.

SyslogStat can be configured by setting options in the config file `sls.yml` (key name is the same as the long option name)  or with command line options. The configurable options are

    -p --processes ... number of processes to ru
    -l --loglevel .... loglevel
    -f --filename .... syslog file to read
