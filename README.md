SyslogStats
===========

## What ?

SyslogStats will analyse RFC 3164 compliant syslog files and log the following data per-host and globally:

    average message length
    number of emergency severities
    number of alert severities
    oldest entry
    youngest entry

## How ?

SyslogStats will (as a default) read `data/syslog` and distribute disection of lines to a configureable number of processes using multiprocessing.Pool. After grouping the results by the message's hostname some interesting data is extracted from it.

## Building

Use the very naive Makefile to build various targes

    build ....... build an image
    run ......... run the supplied syslog file from data/
    test ........ run tests in a one-off container
    local-test .. run tests locally and ensure config file
    inspect ..... get a shell in a one-off container
    clean ....... clean up
    distclean ... clean up image/container

One-off docker containers will mount `./data/` into the container.

SyslogStat can be configured by setting options in the config file `sls.yml` (key name is the same as the long option name)  or with command line options. The configurable options are

    -p --processes ... number of processes to ru
    -l --loglevel .... loglevel
    -f --filename .... syslog file to read

## Examples

Analyse the supplied syslog file

`[user@host] $ make build run`

Same manually inside a container

`[user@host] $ make build inspect`

`~ # python3 -m sls --processes 4 &  tail -f log/sls.log`
