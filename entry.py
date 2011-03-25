class Entry:
    def __init__(self, date, project_name, hours, description):
        self.project_name = project_name
        self.hours = hours
        self.description = description
        self.date = date

    def __str__(self):
        return '%s %s %s %s' % (self.date, self.project_id, self.hours, self.description)
