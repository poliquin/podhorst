#!/usr/bin/env python2.7
# -*- coding: utf_8 -*-

import argparse
import sys, os
from capturadio import Configuration, Station, Show, Recorder

if __name__ == "__main__":

    config = Configuration()

    config.log.debug(config.shows.keys())
    from capturadio.util import parse_duration

    if len(sys.argv) == 1:
        sys.argv.append('--help')

    parser = argparse.ArgumentParser(
        description='Capture internet radio programs broadcasted in mp3 encoding format.',
        epilog = "Here is a list of defined radio stations: %s" % config.get_station_ids()
    )
    parser.add_argument('-d', metavar='destination', required=False, help='Destination directory')

    detailled_group = parser.add_argument_group()
    detailled_group.add_argument('-l', metavar='length', required=False, help='Length of recording in seconds')
    detailled_group.add_argument('-s', metavar='station', required=False, help='Name of the station, defined in ~/.capturadio/capturadiorc.')
    detailled_group.add_argument('-b', metavar='broadcast', required=False, help='Title of the broadcast')
    detailled_group.add_argument('-t', metavar='title', required=False, help='Title of the recording')

    show_group = parser.add_argument_group()
    show_group.add_argument('-S', metavar='show', required=False, help='ID of the show, has to  be defined in configuration file')

    args = parser.parse_args()

    if args.S is not None:
        show_ids = map(lambda id: id.encode('ascii'), config.shows.keys())
        if args.S not in config.shows.keys():
            print "Show '%s' is unknown. Use one of these: %s." % (args.S, show_ids)
            exit(1)
        show = config.shows[args.S]
    else:
        duration = parse_duration(args.l)
        if duration < 1:
            print "Length of '%d' is not a valid recording duration. Use a value greater 1." % duration
            exit(1)

        if args.d is not None:
            config.set_destination(os.path.expanduser(args.d))

        if args.s not in config.get_station_ids():
            print "Station '%s' is unknown. Use one of these: %s." % (args.s, config.get_station_ids())
            exit(1)
        station = config.stations[str.lower(args.s)]

        title = u'%s' % unicode(args.t if (args.t is not None) else args.b, 'utf8')
        show = config.add_show(station, title, title, duration)

    recorder = Recorder()
    recorder.capture(show)
