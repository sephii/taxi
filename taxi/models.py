# -*- coding: utf-8 -*-
import datetime
from taxi.settings import settings

class Entry:
    def __init__(self, date, project_name, hours, description):
        self.project_name = project_name
        self.duration = hours
        self.description = description
        self.date = date
        self.pushed = False

        if project_name in settings.get_projects():
            self.project_id = settings.get_projects()[project_name][0]
            self.activity_id = settings.get_projects()[project_name][1]
        else:
            self.project_id = None
            self.activity_id = None

    def __unicode__(self):
        if self.is_ignored():
            project_name = u'%s (ignored)' % (self.project_name)
        else:
            project_name = u'%s (%s/%s)' % (self.project_name, self.project_id, self.activity_id)

        return u'%-30s %-5.2f %s' % (project_name, self.get_duration() or 0, self.description)

    def __str__(self):
        return unicode(self).encode('utf-8')

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
    STATUS_NOT_STARTED = 0
    STATUS_ACTIVE = 1
    STATUS_FINISHED = 2
    STATUS_CANCELLED = 3

    STATUSES = {
            STATUS_NOT_STARTED: 'Not started',
            STATUS_ACTIVE: 'Active',
            STATUS_FINISHED: 'Finished',
            STATUS_CANCELLED: 'Cancelled',
    }

    SHORT_STATUSES = {
            STATUS_NOT_STARTED: 'N',
            STATUS_ACTIVE: 'A',
            STATUS_FINISHED: 'F',
            STATUS_CANCELLED: 'C',
    }

    def __init__(self, id, name, status = None, description = None, budget = None):
        self.id = int(id)
        self.name = name
        self.activities = []
        self.status = int(status)
        self.description = description
        self.budget = budget

    def __unicode__(self):
        if self.status in self.STATUSES:
            status = self.STATUSES[self.status]
        else:
            status = 'Unknown'

        start_date = self.get_formatted_date(self.start_date)
        if start_date is None:
            start_date = 'Unknown'

        end_date = self.get_formatted_date(self.end_date)
        if end_date is None:
            end_date = 'Unknown'

        return u"""Id: %s
Name: %s
Status: %s
Start date: %s
End date: %s
Budget: %s
Description: %s""" % (
        self.id, self.name,
        status,
        start_date,
        end_date,
        self.budget,
        self.description
    )

    def __str__(self):
        return unicode(self).encode('utf-8')

    def get_formatted_date(self, date):
        if date is not None:
            try:
                formatted_date = date.strftime('%d.%m.%Y')
            except ValueError:
                formatted_date = None
        else:
            formatted_date = None

        return formatted_date

    def add_activity(self, activity):
        self.activities.append(activity)

    def get_activity(self, id):
        for activity in self.activities:
            if activity.id == id:
                return activity

        return None

    def is_active(self):
        return (self.status == self.STATUS_ACTIVE and
                (self.start_date is None or
                    self.start_date <= datetime.datetime.now()) and
                (self.end_date is None or self.end_date >
                    datetime.datetime.now()))

    def get_short_status(self):
        if self.status not in self.SHORT_STATUSES:
            return '?'

        return self.SHORT_STATUSES[self.status]

class Activity:
    def __init__(self, id, name, price):
        self.id = int(id)
        self.name = name
        self.price = float(price)
