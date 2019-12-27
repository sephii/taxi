Developer guide
===============

Timesheets and entries
----------------------

The :class:`~taxi.timesheet.lines.Entry` class is the base of Taxi. An entry is the record of an activity for a certain
period of time. It consists of an activity, a time span, and a description::

    >>> from taxi.timesheet import Entry
    >>> my_entry = Entry('_internal', 1, 'Play ping-pong')

Entries duration can be expressed either as a fixed duration, in hours (eg. 0.5 for half an hour), or as time spans.
Time span notation works with 2-items tuples, like so: `(start_time, end_time)`. In the following example, the entry
starts at 9:30 and ends at 10, thus having a duration of half an hour::

    >>> from datetime import time
    >>> my_entry = Entry('_internal', (time(9, 30), time(10)), 'Play ping-ping')
    >>> my_entry.hours
    0.5

`end_time` can be left blank, in that case the entry will be considered as being "in progress". This is useful in
certain situations, for example the `start` command uses this feature to start an entry which can then be "stopped"
with the `stop` commands (which detects the last in-progress activity and sets its end time).

.. code::

    >>> my_entry = Entry('_internal', (time(9), None), 'Play ping-pong')
    >>> my_entry.hours
    0
    >>> my_entry.in_progress
    True

Now we know how to create entries, we can put them together in timesheets, which is a collection of entries and dates.
You might have noticed entries don't have an associated date: that's because the link between dates and entries is in
the timesheet itself. Let's create a timesheet::

    >>> from datetime import date
    >>> from taxi.timesheet import Timesheet
    >>> timesheet = Timesheet()
    >>> timesheet.entries
    {}

Now we have a timesheet, we can start adding entries to it::

    >>> timesheet.entries.add(date(2017, 6, 7), my_entry)
    >>> timesheet.entries
    {datetime.date(2017, 6, 7): [<Entry: "_internal 0 Play ping-pong">]}

You can dump the timesheet contents by casting it to a string::

    >>> str(timesheet)
    '07.06.2017\n\n_internal 09:00-? Play ping-pong'

Entries also have flags: `pushed` and `ignored`. Ignored and pushed entries will be excluded from the commit process::

    >>> my_entry = Entry('_internal', 1, 'Play ping-pong')
    >>> my_entry.ignored = True
    >>> timesheet = Timesheet()
    >>> timesheet.entries.add(date(2017, 6, 7), my_entry)
    >>> str(timesheet)
    '07.06.2017\n\n? _internal 1 Play ping-pong'

Loading and saving timesheets
-----------------------------

Use the `load` method to create a timesheet from a file::

    >>> timesheet = Timesheet.load('/tmp/timesheet.tks')
    >>> timesheet.entries.add(date(2017, 6, 7), Entry('_internal', 1, 'Play ping-pong'))
    >>> timesheet.save()

You can also save the timesheet to a different file from the file it was loaded from::

    >>> timesheet.save('/tmp/new_timesheet.tks')

Timesheet collections
---------------------

Dealing with multiple timesheets is achieved through the :class:`taxi.timesheet.TimesheetCollection` class. This is
useful if you want to run operations on multiple timesheets in a single command. The `TimesheetCollection` class
proxies all calls to the associated timesheets and aggregates the results. The following example illustrates how the
`entries` attribute from a timesheet collection can be used to transparently access entries from all associated
timesheets::

    >>> from taxi.timesheet import TimesheetCollection
    >>> timesheets = [Timesheet(), Timesheet()]
    >>> timesheets[0].entries.add(date(2017, 6, 8), Entry('_internal', 1, 'Play ping-pong'))
    >>> timesheets[1].entries.add(date(2017, 7, 8), Entry('_internal', 1, 'Play ping-pong'))
    >>> timesheet_collection = TimesheetCollection(timesheets)
    >>> timesheet_collection.entries
    {datetime.date(2017, 6, 8): [<Entry: ...>], datetime.date(2017, 7, 8): [<Entry: ...>]}
    >>> timesheet_collection.get_hours()
    2


Creating a backend
------------------

A backend is a Python package that can be installed independently of Taxi and
that persists the entries transmitted by the ``commit`` command. To create a
backend, you'll need to create a new Python package, which is hopefully quite
easy to do.

As an example, we'll build a simple backend that sends the timesheets it
receives by mail. We'll call it ``taxi_mail``.

.. _registering-the-backend:

Registering the backend
~~~~~~~~~~~~~~~~~~~~~~~

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

Pushing entries
~~~~~~~~~~~~~~~

We now have all the information we need to send mails. For the actual sending,
we could implement the ``push_entry`` method. However this will fire for every
entry, which means we would get one mail per entry. Obviously this is not what
we want, but hopefully you can implement the ``post_push_entries`` method,
which is called once after all entries have been committed. This method also
gives you a chance to raise an exception for failing entries.

So let's buffer the entries to put in the mail in the ``push_entry`` method and
send them all in the ``post_push_entries`` method. The code could look like
that::

    from collections import defaultdict
    import smtplib

    from taxi.backends import BaseBackend

    class MailBackend(BaseBackend):
        def __init__(self, **kwargs):
            super(MailBackend, self).__init__(**kwargs)
            self.path = self.path.lstrip('/')
            self.entries = defaultdict(list)

        def push_entry(self, date, entry):
            self.entries[date].append(entry)

        def post_push_entries(self):
            timesheet = []

            for date, entries in self.entries.items():
                timesheet.append(date.strftime('%d %m %Y'))

                for entry in entries:
                    timesheet.append(str(entry))

            smtp = smtplib.SMTP_SSL(self.hostname)
            smtp.login(self.username, self.password)
            smtp.sendmail('taxi@example.com', self.path, '\n'.join(timesheet))
            smtp.quit()

Note that for the sake of brevity, we didn't catch any exception at all in this
example. It's of course a good idea to do it, so that the user knows why the
entries couldn't be pushed. If your backends raises an exception, all entries
will be considered to have failed and will be reported as such. If you want to
report only certain entries as failed in ``post_push_entries``, raise a
``PushEntriesFailed`` exception, with a parameter ``entries`` that will be a
`entry: error` dictionary.

We now have a fully working backend that can be used to push entries!

Creating custom commands
------------------------

Taxi will load any module defined in the ``taxi.commands`` entry point. Let's create a ``current`` command that displays
the path to the current timesheet. First, let's create the command (in ``taxi_current/commands.py``)::

    import click

    from taxi.commands.base import cli

    @cli.command()
    @click.pass_context
    def current(ctx):
        timesheet_path = ctx.obj['settings'].get_entries_file_path(expand_date=True)
        click.echo("Current timesheet path is " + timesheet_path)

The ``cli.command`` part allows us to create a Taxi subcommand. For more information on how to use Click, refer to the
`official Click documentation <http://click.pocoo.org/5/>`_. Also feel free to check the source code of the existing
commands that can give a good base to start from.

As with custom backend creation, your package should also have a ``setup.py`` file. The commands module should be
registered in the ``taxi.commands`` entry point (in the ``setup.py`` file)::

    #!/usr/bin/env python
    from setuptools import find_packages, setup

    setup(
        name='taxi_current',
        version='1.0',
        packages=find_packages(),
        description='Show current timesheet',
        author='Me',
        author_email='me@example.com',
        url='https://github.com/me/taxi-current',
        license='wtfpl',
        entry_points={
            'taxi.commands': 'current = taxi_current.commands'
        }
    )

That's it! If you install your custom plugin (eg. with ``./setup.py install`` or by using ``./setup.py develop`` as
explained in the :ref:`development-environment` section, you will now be able to type ``taxi current``!

.. _development-environment:

Getting a development environment
---------------------------------

Start by cloning Taxi (you'll probably want to use your fork URL instead of the
public URL)::

    git clone https://github.com/sephii/taxi

Then create a virtual environment with `mkvirtualenv
<http://virtualenvwrapper.readthedocs.org/>`_::

    mkvirtualenv taxi

Now run the setup script to create the development environment::

    ./setup.py develop

Now every time you'll want to work on taxi, start by running ``workon taxi``
first, so that you're using the version you checked out instead of the
system-wide one.

Running tests
-------------

Setup a virtual environment as explained in the previous section, then install
the test requirements in it::

    pip install -r requirements_test.txt

To run the tests, run the following command::

    pytest

When developing it's useful to only run certain tests, for this, use the
following command::

    pytest tests/commands/test_alias.py::AliasCommandTestCase::test_alias_list

You can also leave out ``::test_alias_list`` to run all tests in the
``AliasCommandTestCase``, or leave out ``::AliasCommandTestCase`` as well if
you have multiple test classes and you want to run them all.
