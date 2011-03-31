from settings import settings

class Entry:
    def __init__(self, date, project_name, hours, description):
        self.project_name = project_name
        self.hours = hours
        self.description = description
        self.date = date

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

        return '%-30s %-5.2f %s' % (project_name, self.hours, self.description)

    def is_ignored(self):
        return self.project_name[-1] == '?'
