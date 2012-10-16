from taxi import terminal
from taxi.exceptions import CancelException

class BaseUi(object):
    def msg(self, message):
        print(message)

    def projects_list(self, projects, numbered=False):
        for (key, project) in enumerate(projects):
            if numbered:
                self.msg(u"(%d) %-4s %s" % (key, project.id, project.name))
            else:
                self.msg(u"%-4s %s" % (key, project.id, project.name))

    def project_with_activities(self, project, numbered_activities=False):
        self.msg(project)
        self.msg(u"\nActivities:")
        for (key, activity) in enumerate(project.activities):
            self.msg(u"(%d) %-4s %s" % (key, activity.id, activity.name))

    def select_project(self, projects):
        try:
            return terminal.select_number(len(projects), u"Choose the project "
                                          "(0-%d), (Ctrl-C) to exit: " %
                                          (len(projects) - 1))
        except KeyboardError:
            raise CancelException()

    def select_activity(self, activities):
        try:
            return terminal.select_number(len(activities), u"Choose the "
                                          "activity (0-%d), (Ctrl-C) to exit: " %
                                          (len(project.activities) - 1))
        except KeyboardError:
            raise CancelException()

    def select_alias(self):
        try:
            return terminal.select_string(u"Enter the alias for .tksrc (a-z, - "
                                          "and _ allowed), (Ctrl-C) to exit: ",
                                          r'^[\w-]+$')
        except KeyboardError:
            raise CancelException()

    def overwrite_alias(self):
        overwrite = terminal.select_string(u"The selected alias you entered "
                                           "already exists, overwrite? "
                                           "[y/n/R(etry)]: ", r'^[ynr]$',
                                           re.I, 'r')

        if overwrite == 'n':
            return False
        elif overwrite == 'y':
            return True

        return None

    def alias_added(self, alias, mapping):
        print(u"The following alias has been added to your configuration "
              "file: %s = %s/%s" % ((alias) + mapping))
