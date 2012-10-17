class ProjectNotFoundError(Exception):
    def __init__(self, project_name):
        self.project_name = project_name

    def __str__(self):
        return("The alias `%s` is not mapped to any project in your "
               " configuration file.")

class UsageError(Exception):
    pass

class CancelException(Exception):
    pass
