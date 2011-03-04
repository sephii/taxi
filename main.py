from optparse import OptionParser
import sys

from parser import TaxiParser
from settings import Settings
from pusher import Pusher

def status(parser, settings):
    total_hours = 0

    print 'Staging changes :\n'

    for date, entries in parser.entries.iteritems():
        print '[%s]' % date
        for entry in entries:
            print '%-30s %-5.2f %s' % (entry.project_id, entry.hours, entry.description)
            total_hours += entry.hours

        print ''

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
    action = sys.argv[-1]

    p = TaxiParser('zebra.sample')
    p.parse()

    s = Settings()
    s.load('/home/sylvain/.tksrc')

    if action == 'stat' or action == 'status':
        status(p, s)
    elif action == 'ci' or action == 'commit':
        commit(p, s)

if __name__ == '__main__':
    main()
