import urllib, urllib2, urlparse, cookielib
import json

from models import Project, Activity

class Remote(object):
    def __init__(self, base_url):
        self.base_url = base_url

    def _get_request(self, url, body = None, headers = {}):
        return urllib2.Request('%s/%s' % (self.base_url, url), body, headers)

    def _request(self, url, body = None, headers = {}):
        request = self._get_request(url, body, headers)
        opener = urllib2.build_opener()
        response = opener.open(request)

        return response

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

        response = opener.open(request)

        self.cookiejar.extract_cookies(response, request)

        return response

    def _login(self):
        if self.logged_in:
            return

        login_url = '/login/user/%s.json' % self.username
        parameters = urllib.urlencode({
            'username': self.username,
            'password': self.password,
        })

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

        for date, entries in entries.iteritems():
            for entry in entries:
                if entry.is_ignored():
                    continue

                parameters = urllib.urlencode({
                    'time':         entry.hours,
                    'project_id':   entry.project_id,
                    'activity_id':  entry.activity_id,
                    'day':          date.day,
                    'month':        date.month,
                    'year':         date.year,
                    'description':  entry.description,
                })

                response = self._request(post_url, parameters)
                response_body = response.read()

                try :
                    json_response = json.loads(response_body)
                except ValueError:
                    print 'Unable to read response after pushing entry %s, response was %s' % (entry, response_body)
                    continue

                if 'exception' in json_response:
                    entry.pushed = False
                    print 'Unable to push entry "%s". Error was : %s' % (entry, json_response['exception']['message'])
                elif 'error' in json_response['command']:
                    entry.pushed = False
                    print 'Unable to push entry "%s". Unknown error message.  (sorry that\'s not very useful !)' % (entry)
                else:
                    entry.pushed = True
                    print entry

    def get_projects(self):
        projects_url = 'project/.json'

        self._login()

        response = self._request(projects_url)
        response_body = response.read()

        response_json = json.loads(response_body)
        projects = response_json['command']['projects']['project']

        projects_list = []
        i = 0
        print '%d projects found' % len(projects)

        for project in projects:
            p = Project(project['id'], project['name'], project['status'], project['description'], project['budget'])
            i += 1

            if i % 50 == 0:
                print '%d%% projects processed' % (int(i / float(len(projects)) * 100))

            if p.status == 1:
                activities_url = 'project/%d/activities.json' % int(project['id'])
                response = self._request(activities_url)
                response_body = response.read()
                response_json = json.loads(response_body)
                used = response_json['command']['activities']['used']

                if 'activity' in used:
                    activities = used['activity']

                    if not isinstance(activities, list):
                        activities = [activities];

                    for activity in activities:
                        a = Activity(activity['id'], activity['name'], activity['price'])
                        p.add_activity(a)

            projects_list.append(p)

        return projects_list
