# -*- coding: utf-8 -*-
import urllib, urllib2, urlparse, cookielib
import json
from datetime import datetime

from taxi.models import Project, Activity

class Remote(object):
    # Default timeout for HTTP-related operations, in seconds
    DEFAULT_TIMEOUT = 10

    def __init__(self, base_url):
        self.base_url = base_url

    def _get_request(self, url, body = None, headers = {}):
        return urllib2.Request('%s/%s' % (self.base_url, url), body, headers)

    def _request(self, url, body = None, headers = {}):
        request = self._get_request(url, body, headers)
        opener = urllib2.build_opener()
        response = opener.open(request)

        return response

    def _encode_parameters(self, parameters):
        """Encodes parameters to use them in a request"""
        for key, value in parameters.iteritems():
            if isinstance(value, unicode):
                # According to the HTTP spec, parameters are encoded in
                # iso-8859-1
                parameters[key] = value.encode('iso-8859-1')

        return urllib.urlencode(parameters)

    def login(self):
        pass

    def send_entries(self, entries):
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

    def _get_request(self, url, body = None, headers = {}):
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'Taxi Zebra Client';

        return super(ZebraRemote, self)._get_request(url, body, headers)

    def _request(self, url, body = None, headers = {}):
        request = self._get_request(url, body, headers)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))

        try:
            response = opener.open(request, timeout=self.DEFAULT_TIMEOUT)
        except urllib2.URLError:
            raise Exception('Unable to connect to Zebra. Check your connection status and try again.')

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
        response_body = response.read()

        if not response.info().getheader('Content-Type').startswith('application/json'):
            self.logged_in = False
            raise Exception('Unable to login')
        else:
            self.logged_in = True

    def send_entries(self, entries):
        post_url = '/timesheet/create/.json'

        self._login()

        for date, entries in entries:
            for entry in entries:
                if entry.is_ignored():
                    continue

                parameters_dict = {
                    'time':         entry.get_duration(),
                    'project_id':   entry.project_id,
                    'activity_id':  entry.activity_id,
                    'day':          date.day,
                    'month':        date.month,
                    'year':         date.year,
                    'description':  entry.description,
                }

                parameters = self._encode_parameters(parameters_dict)

                try:
                    response = self._request(post_url, parameters)
                    response_body = response.read()
                except Exception as e:
                    entry.pushed = False
                    print(u'Unable to send request to Zebra, exception was %s' %
                          e)
                    continue

                try :
                    json_response = json.loads(response_body)
                except ValueError:
                    print(u'Unable to read response after pushing entry '
                          '%s, response was %s' % (entry, response_body))
                    continue

                if 'exception' in json_response:
                    entry.pushed = False
                    print(u'Unable to push entry "%s". Error was: %s' %
                          (entry, json_response['exception']['message']))
                elif 'error' in json_response['command']:
                    error = None
                    for element in json_response['command']['error']:
                        if 'Project' in element:
                            error = element['Project']
                            break

                    entry.pushed = False

                    if error:
                        print(u'Unable to push entry "%s". Error was: %s' %
                              (entry, error))
                    else:
                        print(u'Unable to push entry "%s". Unknown error'
                              ' message. (sorry that\'s not very useful !)' %
                              (entry))
                else:
                    entry.pushed = True
                    print(entry)

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
            a = Activity(int(activity['id']),
                    activity['name'], activity['rate_eur'])
            activities_dict[a.id] = a

        projects_list = []
        i = 0
        print(u'%d projects found' % len(projects))

        for project in projects:
            p = Project(int(project['id']), project['name'],\
                    project['status'], project['description'],\
                    project['budget'])

            try:
                p.start_date = datetime.strptime(project['startdate'], '%Y-%m-%d')
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
                    print(u"Cannot import activity %s for project %s"\
                          " because activity id is not an int" %
                          (activity, p.id))

            projects_list.append(p)

        return projects_list
