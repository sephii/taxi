class ProjectNotFoundError(Exception):
    def __init__(self, project_name, description):
        self.project_name = project_name
        self.description = description

    def __str__(self):
        return repr(self.description)
