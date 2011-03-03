from optparse import OptionParser
import sys

from parser import TaxiParser
from settings import Settings

def status(parser, settings):
    total_hours = 0

    for date, entries in parser.entries.iteritems():
        print '[%s]' % date
        for entry in entries:
            print '%-30s %.2f %s' % (entry.project_id, entry.hours, entry.description)
            total_hours += entry.hours

    print total_hours

def main():
    action = sys.argv[-1]

    p = TaxiParser('zebra.sample')
    p.parse()

    s = Settings()
    s.load('/home/sylvain/.tksrc')

    if action == 'stat' or action == 'status':
        status(p, s)


if __name__ == '__main__':
    main()
