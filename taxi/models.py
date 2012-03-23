import datetime
from settings import settings

class Entry:
    def __init__(self, date, project_name, hours, description):
        self.project_name = project_name
        self.duration = hours
        self.description = description
        self.date = date
        self.pushed = False

        if project_name in settings.projects:
            self.project_id = settings.projects[project_name][0]
            self.activity_id = settings.projects[project_name][1]
        else:
            self.project_id = None
            self.activity_id = None

    def __str__(self):
        if self.is_ignored():
            project_name = '%s (ignored)' % (self.project_name)
        else:
            project_name = '%s (%s/%s)' % (self.project_name, self.project_id, self.activity_id)

        return '%-30s %-5.2f %s' % (project_name, self.get_duration() or 0, self.description)

    def is_ignored(self):
        return self.project_name[-1] == '?' or self.get_duration() == 0

    def get_duration(self):
        if isinstance(self.duration, tuple):
            if None in self.duration:
                return 0

            now = datetime.datetime.now()
            time_start = now.replace(hour=self.duration[0].hour,\
                    minute=self.duration[0].minute, second=0)
            time_end = now.replace(hour=self.duration[1].hour,\
                    minute=self.duration[1].minute, second=0)
            total_time = time_end - time_start
            total_hours = total_time.seconds / 3600.0

            return total_hours

        return self.duration

class Project:
    def __init__(self, id, name, status = None, description = None, budget = None):
        self.id = int(id)
        self.name = name
        self.activities = []
        self.status = int(status)
        self.description = description
        self.budget = budget

    def __unicode__(self):
        return """\nId: %s
Name: %s
Active: %s
Budget: %s
Description: %s""" % (self.id, self.name, 'yes' if self.status else 'no', self.budget, self.description)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def add_activity(self, activity):
        self.activities.append(activity)

class Activity:
    def __init__(self, id, name, price):
        self.id = int(id)
        self.name = name
        self.price = float(price)
