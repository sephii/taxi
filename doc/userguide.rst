User guide
==========

Installation
------------

Taxi runs on either Python 2.7 and 3.4. It might run on older versions as well
but it's only tested against the latest Python 2 and 3 versions. To install it,
run the following::

    pip install taxi

You'll probably want to install a backend as well. The backend is the part that
allows you to push your timesheet entries to a centralized location. For the
list of available backends, refer to the :ref:`supported_backends` list.

Getting started
---------------

Your first step will probably to get the list of projects from the backend.
This will allow you to search through your projects and, if your backend
supports this, get some shared aliases you can use without further
configuration::

    taxi update

If this is the first time you run Taxi, you'll be asked a few questions to
create the configuration file.

If your backend supports shared aliases, you can now see the list of available
aliases with the ``alias`` command::

    taxi alias

You can now start writing your timesheets. Taxi uses regular text files to keep
track of the time you record. The default location of your timesheets is
``~/zebra/%Y/%m.tks``, where ``%Y`` and ``%m`` are replaced by the current year
and current month. You'll find more information about this in the
:ref:`config` section.

While you could open your timesheet file directly with your editor, Taxi makes
your life easier with the ``edit`` command, which will open the current
timesheet in your favourite editor. Not only it will determine the correct file
to open according to the current date, but it will also automatically fill it
with date markers. All there is to do now is write your entries. For example,
let's say I played ping-pong from 9 to 10:30, and then I worked on Taxi from
10:30 to 12:00::

    23/02/2015

    pingpong 09:00-10:30 Play ping-pong
    taxi     10:30-12:00 Write documentation

Now if you close your editor you should see something like that::

    Staging changes :

    # Monday 23 february #
    pingpong (not mapped)          1.50  Play ping-pong
            Did you mean one of the following: _inno, _internal, _migration?
    taxi (2185/1369)               1.50  Write documentation
                                   3.00

    Total                          3.00

    Use `taxi ci` to commit staging changes to the server

If you don't see that, you're probably using an editor that runs in the
background. In that case, running ``taxi status`` will show you the same
output. You can see that each alias is displayed along with its mapping. If the
alias you entered is not mapped, you'll get a suggestion of close matches.

Once you're done with your editing, it's time to push it. For this, use the
``commit`` command. This command will push your entries to the backends, and
mark them as pushed so that they're ignored the next time you'll run the
``commit`` command. You'll notice the ping-pong entry wasn't pushed; since it's
not mapped to any alias it was ignored during the push phase.

Ignored entries
~~~~~~~~~~~~~~~

You'll sometimes have entries for which you're not sure which alias you should
use and that shouldn't be pushed until you have a confirmation from someone
else. Simply append a ``?`` to your alias, and the entry will be ignored. If we
run the ``edit`` command and add a question mark to our ``pingpong`` alias like
so::

    23/02/2015

    pingpong? 09:00-10:30 Play ping-pong

The output becomes::

    Staging changes :

    # Monday 23 february #
    pingpong (ignored)             1.50  Play ping-pong
                                   1.50

    Total                          1.50

    Use `taxi ci` to commit staging changes to the server

Entry continuation
~~~~~~~~~~~~~~~~~~

Having entries that follow each other, eg. 10:00-11:00, then 11:00-13:00, etc is
a common pattern. That's why you can skip the start time of an entry if the
previous entry has an end time. The previous example would become (note that
spaces don't matter, you don't need to align them)::

    23/02/2015

    pingpong 09:00-10:30 Play ping-pong
    taxi          -12:00 Write documentation

You can also chain them::

    23/02/2015

    pingpong 09:00-10:30 Play ping-pong
    taxi          -12:00 Write documentation
    internal      -13:00 Debug coffee machine

Getting help
~~~~~~~~~~~~

Use ``taxi <command> --help`` to get help on any Taxi command.

Timesheet syntax
----------------

Taxi uses a simple syntax for timesheets, which are composed of dates and
entries. If you used the ``edit`` command, you already saw the dates. A date is
a string that can have one of the following formats:

* dd/mm/yyyy
* dd/mm/yy
* yyyy/mm/dd

Actually the separator can be any special character. You can control the format
Taxi uses when automatically inserting dates in your entries file with the
:ref:`config_date_format` configuration option.

Timesheets also contain comments, which are denoted by the ``#`` character.
Any line starting with ``#`` will be ignored.

Entries are the entity that allow you to record the time spent an various
activities. The basic syntax is::

    alias duration description

``alias`` can be any string matching a mapping defined either by your
configuration, or a shared alias. If an alias is not found in the configured
aliases, a list of suggestions will be given and the alias will be ignored when
pushing entries.

``duration`` can either be a time range or a duration in hours. If it's a time
range, it should be in the format ``start-end``, where ``start`` can be left
blank if the previous entry also used a time range and had a time defined, and
``end`` can be ``?`` if the end time is not known yet, leading to the entry
being ignored. Each part of the range should have the format ``HH:mm``, or
``HHmm``. If ``duration`` is a duration, it should just be a number, eg. 2 for
2 hours, or 1.75 for 1 hour and 45 minutes.

``description`` can be any text but cannot be left blank.

.. _config:

Configuration options
---------------------

.. _config_auto_add:

auto_add
~~~~~~~~

Default: auto

This specifies where the new entries will be inserted when you use `start` and
`edit` commands. Possible values are `auto` (automatic detection based on your
current entries), `bottom` (values are added to the end of the file), or `top`
(values are added to the top of the file) or `no` (no auto add for the edit
command).

auto_fill_days
~~~~~~~~~~~~~~

Default: 0,1,2,3,4

When running the `edit` command, Taxi will add all the dates that are not
present in your entries file until the current date if they match any day
present in ``auto_fill_days`` (0 is Monday, 6 is Sunday). You must have
:ref:`config_auto_add` set to something else than `no` for this option to take
effect.

.. _config_date_format:

date_format
~~~~~~~~~~~

Default: %d/%m/%Y

This is the format of the dates that'll be automatically inserted in your
entries file(s), for example when using the `start` and `edit` commands. You
can use the same date placeholders as for the `file` option.

editor
~~~~~~

When running the `edit` command, your editor command will be deducted from your
environment but if you want to use a custom command you can set it here.

.. _config_file:

file
~~~~

Default: ~/zebra/%Y/%m.tks

The path of your entries file. You're free to use a single file to store all
your entries but you're strongly encouraged to use date placeholders here. The
following will expand to ``~/zebra/2011/11.tks`` if you're in November 2011.
See `the strftime documentation
<http://docs.python.org/library/datetime.html#strftime-and-strptime-behavior>`_
for a complete list of available formats.

local_aliases
~~~~~~~~~~~~~

Defines a list of local aliases that you will be able to use in your timesheets
but that will never be pushed. These aliases will appear in the timesheet
summary and will get marked as pushed when running the `commit` command.

The list should be separated by commas. For example the following value will
define the `__lunch` and `__hacking` local aliases (note that the double
underscore is just a personal convention to distinguish them from standard
aliases, you're free to use any name you want): ``local_aliases = __lunch,
__hacking``.

nb_previous_files
~~~~~~~~~~~~~~~~~

Default: 1

Defines the number of previous timesheet files Taxi should try to parse. This
allows you to make sure you don't forget hours in files from previous months
when starting a new month.

This option only makes sense if you're using date placeholders in
:ref:`config_file`.

Backends configuration
----------------------

The configuration file has a section named ``backends`` that allows you to
define the active backends and the credentials you want to use. The syntax of
the backends part is::

    [backends]
    default = <backend_name>://<user>:<password>@<host>:<port><path><options>

Here a backend named *default* is defined. The ``backend_name`` is the adapter
this backend will use. You'll find this name in the specific backend package
documentation. The ``backend_name`` is the only mandatory part, as some
backends won't care about the ``user``, ``password``, or other configuration
options.

The name of each backend should be unique, and it will be used when defining
aliases. Each backend will have a section named ``[backend_name_aliases]`` and
``[backend_name_shared_aliases]``, where *backend_name* is the name of the
backend, each containing the user-defined aliases, and the automatic aliases
fetched with the ``update`` command.

.. note::

    If you have any special character in your password, make sure it is
    URL-encoded, as Taxi won't be able to correctly parse the URI otherwise.
    You can use the following snippet to encode your password::

        >>> import urllib
        >>> urllib.quote('my_password', safe='')

    On Python 3::

        >>> from urllib import parse
        >>> parse.quote('my_password, safe='')
