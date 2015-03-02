Developer guide
===============

Getting a development environment
---------------------------------

Start by cloning Taxi (you'll probably want to use your fork URL instead of the
public URL)::

    git clone https://github.com/sephii/taxi

Then create a virtual environment with `mkvirtualenv <http://insertlinkhere>`_::

    mkvirtualenv taxi

Now run the setup script to create the development environment::

    ./setup.py develop

Now every time you'll want to work on taxi, start by running ``workon taxi``
first, so that you're using the version you checked out instead of the
system-wide one.

Running tests
-------------

Tests use `tox <http://insertlinkhere>`_, which allows to run tests on multiple
Python versions. You'll need Python 2.7 and Python 3.4 installed to be able to
run all the tests, or you can let the continuous integration server do the job
for you. Anyway, if you want to run the tests locally, simply run::

    tox

This will create virtual environments for each Python version and run the tests
against it. If you want to limit the tests to a certain Python version, run::

    tox -e py27

This will only run the tests on Python 2.7. When developing it's useful to only
run certain tests, for this, use the following command::

    tox -- -a tests/commands/test_alias.py::AliasCommandTestCase::test_alias_list

You can also leave out ``::test_alias_list`` to run all tests in the
``AliasCommandTestCase``, or leave out ``::AliasCommandTestCase`` as well if
you have multiple test classes and you want to run them all.

Creating a backend
------------------

A backend is a Python package that can be installed independently of Taxi and
that persists the entries transmitted by the ``commit`` command. To create a
backend, you'll need to create a new Python package, which is hopefully quite
easy to do.

As an example, we'll build a simple backend that sends the timesheets it
receives by mail. We'll call it ``taxi_mail``.

A backend provides functionality but should not contain harcoded configuration
such as usernames or passwords. Think about other people who will want to use
your backend, they'll probably don't have the same credentials as you.

A backend is defined and configured by a URI that allows you to configure it.
The full syntax is::

    [backends]
    default = <backend_name>://<user>:<password>@<host>:<port><path><options>

Your backend obviously doesn't have to use all the parts of the URI. For
example an unauthenticated backend won't need any user or password, and the
user is allowed to leave them blank in the configuration file.

Let's start to write our backend. The first thing you'll want to do is define a
``setup.py`` file. Here's an example::

    #!/usr/bin/env python
    from setuptools import find_packages, setup

    setup(
        name='taxi_mail',
        version='1.0',
        packages=find_packages(),
        description='Mail backend for Taxi',
        author='Me',
        author_email='me@example.com',
        url='https://github.com/me/taxi-mail',
        license='wtfpl',
        entry_points={
            'taxi.backends': 'smtp = taxi_mail.backend:MailBackend'
        }
    )

The important part is the ``entry_points``. This is what will tell Taxi the
class to use for the backend. The key ``smtp`` is the name of the backend. This
is what the user will put in ``<backend_name>`` in the configuration file. The
part ``taxi_mail.backend:MailBackend`` is the path to our backend class. This
basically means ``from taxi_mail.backend import MailBackend``.

Let's create the backend class::

    # file: taxi_mail/backend.py

    from taxi.backends import BaseBackend

    class MailBackend(BaseBackend):
        pass

The first thing our backend will need to do is store the information we want
from the URI so that we can use it later. The ``BaseBackend`` already defines
an ``__init__`` method that stores all the parts of the backend URI so there
isn't much to do. Let's think about how the user will configure our backend.
The following syntax would probably make sense::

    [backends]
    mail = smtp://user:password@smtp.gmail.com/me@example.com

We decided to use the ``<path>`` part for the e-mail address of the recipient.
There's one detail though: the path here is ``/me@example.com``, so we need to
get rid of that initial slash. Let's do it::

    class MailBackend(BaseBackend):
        def __init__(self, **kwargs):
            super(MailBackend, self).__init__(**kwargs)
            self.path = self.path.lstrip('/')

We now have all the information we need to send mails. For the actual sending,
we could implement the ``push_entry`` method. However this will fire for
every entry, which means we would get one mail per entry. Obviously this is not
what we want, but hopefully Taxi provides signals you can hook on. There's a
``post_commit`` signal which is fired once after all entries have been
committed. Let's buffer the entries to put in the mail in the ``push_entry``
method and send them all in the ``post_commit`` method. The code could look
like that::

    from collections import defaultdict
    import smtplib

    from taxi.backends import signals
    from taxi.dispatcher import receiver

    class MailBackend(BaseBackend):
        def __init__(self, **kwargs):
            super(MailBackend, self).__init__(**kwargs)
            self.path = self.path.lstrip('/')
            self.entries = defaultdict(list)

        def push_entry(self, entry, date):
            self.entries[date].append(entry)

        @receiver(signals.post_commit)
        def post_commit(self):
            timesheet = []

            for date, entries in self.entries.items():
                timesheet.append(date.strftime('%d %m %Y'))

                for entry in entries:
                    timesheet.append(str(entry))

            smtp = smtplib.SMTP(self.hostname)
            smtp.login(self.user, self.password)
            smtp.sendmail('taxi@example.com', self.path, timesheet)
