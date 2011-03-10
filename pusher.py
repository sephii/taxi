import urllib, urllib2, urlparse, cookielib

class Pusher:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password

        self.cookiejar = cookielib.CookieJar()

    def _get_request(self, url, body = None, headers = {}):
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'Taxi Zebra Client';

        return urllib2.Request('%s/%s' % (self.base_url, url), body, headers)

    def _request(self, url, body = None, headers = {}):
        request = self._get_request(url, body, headers)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))

        response = opener.open(request)

        self.cookiejar.extract_cookies(response, request)

        return response

    def _login(self):
        login_url = '/login/user/%s.json' % self.username
        parameters = urllib.urlencode({
            'username': self.username,
            'password': self.password,
        })

        response = self._request(login_url, parameters)
        response_body = response.read()

        return response.getheader('Location', None) is not None and response.status == 301

    def _send_entries(self, entries):
        post_url = '/timesheet/create/.json'

        for date, entries in entries.iteritems():
            for entry in entries:
                parameters = urllib.urlencode({
                    'time':         entry.hours,
                    'project_id':   entry.project_id,
                    'activity_id':  0,
                    'day':          date.day,
                    'month':        date.month,
                    'year':         date.year,
                    'description':  entry.description,
                })

                response = self._request(post_url, parameters)
                response_body = response.read()

                print response_body

    def push(self, entries):
        if not self._login():
            raise ValueError('Can\'t login')

        self._send_entries(entries)
