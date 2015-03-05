from __future__ import unicode_literals

import six


class BaseBackend(object):
    def __init__(self, username, password, hostname, port, path, options):
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self.path = path
        self.options = options

    def push_entry(self, date, entry):
        pass

    def get_projects(self):
        return []

    def post_push_entries(self):
        pass


class PushEntryFailed(Exception):
    pass


@six.python_2_unicode_compatible
class PushEntriesFailed(Exception):
    def __init__(self, message=None, entries=None):
        self.entries = entries
        self.message = message

    def __str__(self):
        return self.message
