import httplib, urllib, urlparse

class Pusher:
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password

    def _request(self, method, url, body = '', headers = {}):
        base_url = urlparse.urlparse(self.url)

        if base_url.scheme == 'https':
            conn = httplib.HTTPSConnection(base_url.netloc)
        elif base_url.sceme == 'http':
            conn = httplib.HTTPConnection(base_url.netloc)
        else:
            raise ValueError('Unknown URI scheme for host %s (you must use http or https)' % self.url)

        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'Taxi Zebra Client';

        conn.set_debuglevel(9)
        conn.request(method, url, body, headers)

        return conn.getresponse()

    def _login(self):
        login_url = '/login/.json'
        parameters = urllib.urlencode({
            'username': self.username,
            'password': self.password,
        })

        response = self._request('POST', login_url, parameters)
        response_body = response.read()

        return response.getheader('Location', None) is not None and response.status == 301

    def _send_entries(self):
        post_url = '/timesheet/create/.json'

        for entry in self.entries:
            parameters = urllib.urlencode({
                'time':         entry.hours,
                'project_id':   entry.project_id,
                'activity_id':  entry.activity_id,
                'day':          entry.date.day,
                'month':        entry.date.month,
                'year':         entry.date.year,
                'description':  entry.description,
            })

            response = self._request('POST', login_url, parameters)
            response_body = response.read()

    def push(self, entries):
        if not self._login():
            raise ValueError('Can\'t login')

        #self._send_entries()
