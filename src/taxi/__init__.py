#!/usr/bin/python
from optparse import OptionParser
import sys
import os
import datetime

from parser import TaxiParser
from settings import settings
from pusher import Pusher
from projectsdb import ProjectsDb

import locale

VERSION = '1.0'

def update(options, args):
    db = ProjectsDb()

    db.update(
            settings.get('default', 'site'),
            settings.get('default', 'username'),
            settings.get('default', 'password')
    )

def search(options, args):
    db = ProjectsDb()

    if len(args) < 2:
        raise Exception('Error: you must specify a search string')

    try:
        search = args
        search = search[1:]
        projects = db.search(search)
    except IOError:
        print 'Error: the projects database file doesn\'t exist. Please run `taxi update` to create it'
    else:
        for project in projects:
            print '%-4s %s' % (project.id, project.name)

def show(options, args):
    db = ProjectsDb()

    if len(args) < 2:
        raise Exception('Error: you must specify a project id')

    try:
        project = db.get(int(args[1]))
    except IOError:
        print 'Error: the projects database file doesn\'t exist. Please run `taxi update` to create it'
    except ValueError:
        print 'Error: the project id must be a number'
    else:
        if project.status == 1:
            active = 'yes'
        else:
            active = 'no'

        print """Id: %s
Name: %s
Active: %s
Budget: %s
Description: %s""" % (project.id, project.name, active, project.budget, project.description)

        if project.status == 1:
            print "\nActivities:"
            for activity in project.activities:
                print '%-4s %s' % (activity.id, activity.name)

def status(options, args):
    total_hours = 0

    if len(args) < 2:
        raise Exception('Error: you must specify a filename to parse')

    parser = get_parser(args[1])
    check_entries_file(parser, settings)

    print 'Staging changes :\n'

    for date, entries in parser.get_entries(date=options.date):
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

def commit(options, args):
    if len(args) < 2:
        raise Exception('Error: you must specify a filename to parse')

    parser = get_parser(args[1])
    check_entries_file(parser, settings)

    pusher = Pusher(
            settings.get('default', 'site'),
            settings.get('default', 'username'),
            settings.get('default', 'password')
    )

    pusher.push(parser.get_entries(date=options.date))

    total_hours = 0
    for date, entries in parser.entries.iteritems():
        for entry in entries:
            if entry.pushed:
                total_hours += entry.hours

    print '\n%-29s %5.2f' % ('Total', total_hours)

    parser.update_file()

def get_parser(filename):
    p = TaxiParser(filename)
    p.parse()

    return p

def check_entries_file(parser, settings):
    for date, entries in parser.entries.iteritems():
        for entry in entries:
            if entry.project_name[-1] != '?' and entry.project_name not in settings.projects:
                raise ValueError('Error: project `%s` is not mapped to any project number in your settings file' % entry.project_name)

def call_action(actions, options, args):
    user_action = args[0]

    for action in actions:
        for action_name in action[0]:
            if action_name == user_action:
                action[1](options=options, args=args)

                return

    raise Exception('Error: action not found')

def main():
    usage = "usage: %prog [options] status|commit|update|search|show"
    locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())

    opt = OptionParser(usage=usage, version='%prog ' + VERSION)
    opt.add_option('-c', '--config', dest='config', help='use CONFIG file instead of ~/.tksrc', default=os.path.join(os.path.expanduser('~'), '.tksrc'))
    opt.add_option('-v', '--verbose', dest='verbose', action='store_true', help='make taxi verbose', default=False)
    opt.add_option('-d', '--date', dest='date', help='only process entries for date '\
            'DATE (eg. 31.01.2011, 31.01.2011-05.02.2011)')
    (options, args) = opt.parse_args()

    actions = [
            (['stat', 'status'], status),
            (['ci', 'commit'], commit),
            (['up', 'update'], update),
            (['search'], search),
            (['show'], show),
    ]

    if len(args) == 0:
        opt.print_help()
        exit()

    if options.date is not None:
        date_format = '%d.%m.%Y'

        try:
            if '-' in options.date:
                splitted_date = options.date.split('-', 1)

                options.date = (datetime.datetime.strptime(splitted_date[0],\
                        date_format).date(),
                        datetime.datetime.strptime(splitted_date[1],
                            date_format).date())
            else:
                options.date = datetime.datetime.strptime(options.date,\
                        date_format).date()
        except ValueError:
            opt.print_help()
            exit()

    settings.load(options.config)

    if not os.path.exists(settings.TAXI_PATH):
        os.mkdir(settings.TAXI_PATH)

    try:
        call_action(actions, options, args)
    except Exception as e:
        if options.verbose:
            raise

        print e

if __name__ == '__main__':
    main()
