class Entry:
    def __init__(self, project_id, hours, description):
        self.project_id = project_id
        self.hours = hours
        self.description = description

    def __str__(self):
        return '%s %s %s' % (self.project_id, self.hours, self.description)
