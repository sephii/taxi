import re

from taxi.settings import settings
from taxi.projectsdb import projects_db

def print_alias(alias):
    user_alias = settings.get_projects()[alias]
    project = projects_db.get(user_alias[0])

    # Project doesn't exist in the database
    if project is None:
        project_name = '?'
        mapping_name = '%s/%s' % project.activity
    else:
        # Alias is mapped to a project, not a project/activity tuple
        if user_alias[1] is None:
            project_name = project.name
            mapping_name = user_alias[0]
        else:
            activity = project.get_activity(user_alias[1])
            activity_name = activity.name if activity else '?'

            project_name = '%s, %s' % (project.name, activity_name)
            mapping_name = '%s/%s' % user_alias

    print(u"%s -> %s (%s)" % (alias, mapping_name, project_name))

def print_mapping(mapping):
    reversed_projects = settings.get_reversed_projects()
    project = projects_db.get(mapping[0])

    if mapping not in reversed_projects:
        raise Exception("%s/%s is not mapped to any activity." % mapping)

    user_alias = reversed_projects[mapping]

    if not project:
        project_name = '?'
    else:
        activity = project.get_activity(mapping[1])

        if activity is None:
            project_name = '%s' % (project.name)
        else:
            project_name = '%s, %s' % (project.name, activity.name)

    print(u"%s/%s -> %s (%s)" % (mapping[0], mapping[1], user_alias, project_name))

def select_number(max, description, min=0):
    while True:
        char = raw_input('\n%s' % description)
        try:
            number = int(char)
            if min <= number <= max:
                return number
            else:
                print(u'Number out of range, try again')
        except ValueError:
            print(u'Please enter a number')

def select_string(description, format=None, regexp_flags=0, default=None):
    while True:
        char = raw_input(description)
        if char == '' and default is not None:
            return default

        if format is not None and re.match(format, char, regexp_flags):
            return char
        else:
            print(u'Invalid input, please try again')

