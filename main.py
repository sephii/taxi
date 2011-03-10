from optparse import OptionParser
import sys
import os

from parser import TaxiParser
from settings import Settings
from pusher import Pusher

def status(parser, settings):
    total_hours = 0

    print 'Staging changes :\n'

    for date, entries in parser.entries.iteritems():
        subtotal_hours = 0
        print '[%s]' % date
        for entry in entries:
            print '%-30s %-5.2f %s' % (entry.project_id, entry.hours, entry.description)
            subtotal_hours += entry.hours

        print '%-29s %5.2f' % ('', subtotal_hours)
        print ''

        total_hours += subtotal_hours

    print '%-29s %5.2f' % ('Total', total_hours)
    print '\nUse `taxi ci` to commit staging changes to the server'

def commit(parser, settings):
    pusher = Pusher(
            settings.get('default', 'site'), 
            settings.get('default', 'username'),
            settings.get('default', 'password')
    )

    pusher.push(parser.entries)

def main():
    usage = "usage: %prog [options] action"

    opt = OptionParser(usage=usage)
    opt.add_option('-f', '--file', dest='filename', help='parse FILENAME instead of ~/.zebra', default=os.path.join(os.path.expanduser('~'), '.zebra'))
    opt.add_option('-c', '--config', dest='config', help='use CONFIG file instead of ~/.tksrc', default=os.path.join(os.path.expanduser('~'), '.tksrc'))
    (options, args) = opt.parse_args()

    if len(args) > 0:
        action = args[-1]
    else:
        opt.print_help()
        exit()

    p = TaxiParser(options.filename)
    p.parse()

    s = Settings()
    s.load(options.config)

    if action == 'stat' or action == 'status':
        status(p, s)
    elif action == 'ci' or action == 'commit':
        commit(p, s)

if __name__ == '__main__':
    main()
