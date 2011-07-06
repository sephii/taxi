#!/usr/bin/python
from optparse import OptionParser
import ConfigParser
import sys
import os
import datetime

from parser import TaxiParser
from settings import settings
from pusher import Pusher
from projectsdb import ProjectsDb

import locale

VERSION = '1.0'

def start(options, args):
    if len(args) < 2:
        raise Exception('Usage: start project_name')

    project_name = args[1]

    if not settings.project_exists(project_name):
        raise Exception('Error: the project \'%s\' doesn\'t exist' %\
                project_name)

    if not os.path.exists(options.file):
        os.makedirs(os.path.dirname(options.file))
        myfile = open(options.file, 'w')
        myfile.close()

    parser = get_parser(options.file)
    parser.add_entry(datetime.date.today(), project_name,\
            (datetime.datetime.now().time(), None))
    parser.update_file()

def stop(options, args):
    if len(args) < 2:
        raise Exception('Usage: stop project_name [description]')

    project_name = args[1]

    if len(args) > 2:
        description = args[2]
    else:
        description = None

    if not settings.project_exists(project_name):
        raise Exception('Error: the project \'%s\' doesn\'t exist' %\
                project_name)

    parser = get_parser(options.file)
    parser.continue_entry(datetime.date.today(), project_name,\
            datetime.datetime.now().time(), description)
    parser.update_file()

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
        raise Exception('Usage: search search_string')

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
        raise Exception('Usage: show project_id')

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

        print u"""Id: %s
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

    parser = get_parser(options.file)
    check_entries_file(parser, settings)

    print 'Staging changes :\n'

    for date, entries in parser.get_entries(date=options.date):
        subtotal_hours = 0
        print '# %s #' % date.strftime('%A %d %B').capitalize()
        for entry in entries:
            print entry
            subtotal_hours += entry.get_duration() or 0

        print '%-29s %5.2f' % ('', subtotal_hours)
        print ''

        total_hours += subtotal_hours

    print '%-29s %5.2f' % ('Total', total_hours)
    print '\nUse `taxi ci` to commit staging changes to the server'

def commit(options, args):
    parser = get_parser(options.file)
    check_entries_file(parser, settings)

    pusher = Pusher(
            settings.get('default', 'site'),
            settings.get('default', 'username'),
            settings.get('default', 'password')
    )

    pusher.push(parser.get_entries(date=options.date))

    total_hours = 0
    for date, entries in parser.get_entries(date=options.date):
        for entry in entries:
            if entry.pushed:
                total_hours += entry.get_duration()

    print '\n%-29s %5.2f' % ('Total', total_hours)

    parser.update_file()

def get_parser(filename):
    p = TaxiParser(filename)
    p.parse()

    return p

def check_entries_file(parser, settings):
    for date, entries in parser.entries.iteritems():
        for entry in entries:
            if not settings.project_exists(entry.project_name):
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
    opt.add_option('-f', '--file', dest='file', help='parse FILE instead of the '\
            'one defined in your CONFIG file')
    opt.add_option('-d', '--date', dest='date', help='only process entries for date '\
            'DATE (eg. 31.01.2011, 31.01.2011-05.02.2011)')
    (options, args) = opt.parse_args()

    actions = [
            (['stat', 'status'], status),
            (['ci', 'commit'], commit),
            (['up', 'update'], update),
            (['search'], search),
            (['show'], show),
            (['start'], start),
            (['stop'], stop),
    ]

    if len(args) == 0:
        opt.print_help()
        exit()

    settings.load(options.config)
    if not os.path.exists(settings.TAXI_PATH):
        os.mkdir(settings.TAXI_PATH)

    if options.file is None:
        try:
            options.file = settings.get('default', 'file')
        except ConfigParser.NoOptionError:
            raise Exception("""Error: no file to parse. You must either define \
one in your config file with the 'file' setting, or use the -f option""")

    options.file = datetime.date.today().strftime(os.path.expanduser(options.file))

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


    try:
        call_action(actions, options, args)
    except Exception as e:
        if options.verbose:
            raise

        print e

if __name__ == '__main__':
    main()
