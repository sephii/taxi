# -*- coding: utf-8 -*-
import cookielib
from datetime import datetime
import json
import urllib
import urllib2

from taxi.projects import Project, Activity
from taxi.exceptions import TaxiException


class Remote(object):
    # Default timeout for HTTP-related operations, in seconds
    DEFAULT_TIMEOUT = 10

    def __init__(self, base_url):
        self.base_url = base_url

    def _get_request(self, url, body=None, headers={}):
        return urllib2.Request('%s/%s' % (self.base_url, url), body, headers)

    def _request(self, url, body=None, headers={}):
        request = self._get_request(url, body, headers)
        opener = urllib2.build_opener()
        response = opener.open(request)

        return response

    def _encode_parameters(self, parameters):
        """Encodes parameters to use them in a request"""
        for key, value in parameters.iteritems():
            if isinstance(value, unicode):
                parameters[key] = value.encode('utf-8')

        return urllib.urlencode(parameters)

    def login(self):
        pass

    def send_entries(self, entries, callback=None):
        pass

    def get_projects(self):
        pass


class ZebraRemote(Remote):
    def __init__(self, base_url, username, password):
        super(ZebraRemote, self).__init__(base_url)

        self.cookiejar = cookielib.CookieJar()
        self.logged_in = False
        self.username = username
        self.password = password

    def _get_request(self, url, body=None, headers={}):
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'Taxi Zebra Client'

        return super(ZebraRemote, self)._get_request(url, body, headers)

    def _request(self, url, body=None, headers={}):
        request = self._get_request(url, body, headers)
        opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(self.cookiejar)
        )

        try:
            response = opener.open(request, timeout=self.DEFAULT_TIMEOUT)
        except urllib2.URLError:
            raise TaxiException("Unable to connect to Zebra. Check your"
                                " connection status and try again.")

        self.cookiejar.extract_cookies(response, request)

        return response

    def _login(self):
        if self.logged_in:
            return

        login_url = '/login/user/%s.json' % self.username
        parameters_dict = {
            'username': self.username,
            'password': self.password,
        }

        parameters = self._encode_parameters(parameters_dict)

        response = self._request(login_url, parameters)

        if (not response.info().getheader('Content-Type')
                               .startswith('application/json')):
            self.logged_in = False
            raise TaxiException('Unable to login')
        else:
            self.logged_in = True

    def send_entries(self, entries, mappings, callback=None):
        post_url = '/timesheet/create/.json'

        pushed_entries = []
        failed_entries = []
        self._login()

        for (date, entries) in entries.iteritems():
            for entry in entries:
                parameters_dict = {
                    'time':         entry.hours,
                    'project_id':   mappings[entry.alias][0],
                    'activity_id':  mappings[entry.alias][1],
                    'day':          date.day,
                    'month':        date.month,
                    'year':         date.year,
                    'description':  entry.description,
                }
                error = None

                parameters = self._encode_parameters(parameters_dict)

                try:
                    response = self._request(post_url, parameters)
                    response_body = response.read()
                    json_response = json.loads(response_body)
                except ValueError:
                    error = (u"Unable to read response response was %s" %
                             (response_body))
                    failed_entries.append((entry, error))
                except Exception as e:
                    error = (u"Unable to send request to Zebra, error was %s" %
                             (e))
                    failed_entries.append((entry, error))
                else:
                    if 'exception' in json_response:
                        error = json_response['exception']['message']
                        failed_entries.append((entry, error))
                    elif 'error' in json_response['command']:
                        error = None
                        for element in json_response['command']['error']:
                            if 'Project' in element:
                                error = element['Project']
                                break

                        if error:
                            failed_entries.append((entry, error))
                        else:
                            error = (u"Unknown error message. (sorry that's "
                                     "not very useful!)")
                            failed_entries.append((entry, error))
                    else:
                        pushed_entries.append(entry)
                finally:
                    if callback is not None:
                        callback(entry, error)

        return (pushed_entries, failed_entries)

    def get_projects(self):
        projects_url = 'project/all.json'

        self._login()

        response = self._request(projects_url)
        response_body = response.read()

        response_json = json.loads(response_body)
        projects = response_json['command']['projects']['project']
        activities = response_json['command']['activities']['activity']
        activities_dict = {}

        for activity in activities:
            a = Activity(int(activity['id']), activity['name'],
                         activity['rate_eur'])
            activities_dict[a.id] = a

        projects_list = []
        i = 0

        for project in projects:
            p = Project(int(project['id']), project['name'],
                        project['status'], project['description'],
                        project['budget'])

            try:
                p.start_date = datetime.strptime(
                    project['startdate'], '%Y-%m-%d'
                )
            except ValueError:
                p.start_date = None

            try:
                p.end_date = datetime.strptime(project['enddate'], '%Y-%m-%d')
            except ValueError:
                p.end_date = None

            i += 1

            activities = project['activities']['activity']

            # Sometimes the activity list just contains an @attribute
            # element, in this case we skip it
            if isinstance(activities, dict):
                continue

            # If there's only 1 activity, this won't be a list but a simple
            # element
            if not isinstance(activities, list):
                activities = [activities]

            for activity in activities:
                try:
                    if int(activity) in activities_dict:
                        p.add_activity(activities_dict[int(activity)])
                except ValueError:
                    print(u"Cannot import activity %s for project %s"
                          " because activity id is not an int" %
                          (activity, p.id))

            if 'activity_aliases' in project and project['activity_aliases']:
                for alias, mapping in project['activity_aliases'].iteritems():
                    p.aliases[alias] = int(mapping)

            projects_list.append(p)

        return projects_list


class DummyRemote(Remote):
    projects = {
        111: [222, 333],
        123: [456],
    }

    def __init__(self):
        super(DummyRemote, self).__init__('dummy')

    def send_entries(self, entries, mappings, callback=None):
        pushed_entries = []
        failed_entries = []

        for (date, entries) in entries.iteritems():
            for entry in entries:
                error = None

                if (entry.project_id not in self.projects
                        or entry.activity_id not in
                        self.projects[entry.project_id]):
                    error = 'Project doesn\'t exist'
                    failed_entries.append((entry, error))
                else:
                    entry.pushed = True
                    pushed_entries.append(entry)

                if callback is not None:
                    callback(entry, error)

        return (pushed_entries, failed_entries)

    def get_projects(self):
        projects_list = []

        for (project, activities) in self.projects.iteritems():
            p = Project(project, 'foo', 1, 'bar', '1000')
            p.start_date = None
            p.end_date = None

            for activity in activities:
                p.add_activity(activity)

            projects_list.append(p)

        return projects_list
