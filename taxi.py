#!/usr/bin/python
from optparse import OptionParser
import sys
import os

from parser import TaxiParser
from settings import settings
from pusher import Pusher

import locale

def status(parser):
    total_hours = 0

    print 'Staging changes :\n'

    for date, entries in parser.entries.iteritems():
        subtotal_hours = 0
        print '# %s #' % date.strftime('%A %d %B').capitalize()
        for entry in entries:
            print entry
            subtotal_hours += entry.hours

        print '%-29s %5.2f' % ('', subtotal_hours)
        print ''

        total_hours += subtotal_hours

    print '%-29s %5.2f' % ('Total', total_hours)
    print '\nUse `taxi ci` to commit staging changes to the server'

def commit(parser):
    pusher = Pusher(
            settings.get('default', 'site'), 
            settings.get('default', 'username'),
            settings.get('default', 'password')
    )

    pusher.push(parser.entries)
    parser.update_file()

def main():
    usage = "usage: %prog [options] action"
    locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())

    opt = OptionParser(usage=usage)
    opt.add_option('-f', '--file', dest='filename', help='parse FILENAME instead of ~/.zebra', default=os.path.join(os.path.expanduser('~'), '.zebra'))
    opt.add_option('-c', '--config', dest='config', help='use CONFIG file instead of ~/.tksrc', default=os.path.join(os.path.expanduser('~'), '.tksrc'))
    (options, args) = opt.parse_args()

    if len(args) > 0:
        action = args[-1]
    else:
        opt.print_help()
        exit()

    settings.load(options.config)

    p = TaxiParser(options.filename)
    p.parse()

    for date, entries in p.entries.iteritems():
        for entry in entries:
            if entry.project_name[-1] != '?' and entry.project_name not in settings.projects:
                raise ValueError('Project `%s` is not mapped to any project number in your settings file' % entry.project_name)

    if action == 'stat' or action == 'status':
        status(p)
    elif action == 'ci' or action == 'commit':
        commit(p)

if __name__ == '__main__':
    main()
