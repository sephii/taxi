User guide
==========

Installation
------------

Taxi runs on Python 2.7, 3.4 and 3.5. The easiest way to install it is by using
pip::

    pip install --user taxi

You'll now need to install a backend separately to be able to push your entries and retrieve
projects and activities. For example to install the `zebra` backend::

    pip install --user taxi-zebra

For a list of available backends, refer to the :ref:`supported_backends` list.

You can now try to run the ``taxi`` command. If you're getting a "command not found" error, make sure that
`~/.local/bin/` is in your ``PATH`` environment variable (eg. by running ``echo $PATH``). To change your ``PATH``
environment variable, you can follow `this guide <https://stackoverflow.com/a/14638025>`_.

First steps with Taxi
---------------------

Once Taxi is installed, you'll probably want to fetch the projects list from
your backend::

    taxi update

Since this is the first time you run Taxi, you'll get asked a few questions::

    Welcome to Taxi!
    ================

    It looks like this is the first time you run Taxi. You will need a
    configuration file (~/.taxirc) to proceed. Please answer a few questions to
    create your configuration file.

    Backend you want to use (choices are dummy, zebra): zebra
    Username or token: b4b8123f4addb27ad0eb0b2b0a0ae81730af96b8
    Password (leave empty if you're using a token) []: 
    Editor command to edit your timesheets [vim]: 
    Hostname of the backend (eg. timesheets.example.com): zebra.example.com

Taxi is now ready to use! Let's start by recording the time we spent installing
Taxi::

    taxi edit

.. note::

    If you didn't choose the correct editor when running Taxi for the first
    time you might get into an editor called `vim` at this point. To exit it,
    type `:q!`. Then to manually set the editor Taxi should use, open your Taxi
    configuration file (by default `~/.config/taxi/taxirc`), and change the
    value of the `editor` setting to the editor you want. If you're using
    Linux, you might put `gedit`. If you're using OS X, you might put `open
    -a TextEdit`.

Your editor will pop up and you'll see the current date has been automatically
added for you. Let's add an entry so your file looks something like that::

    09/05/2016

    intro 10:15-10:30 Install Taxi

An entry consists of 3 parts:

* An alias (`intro`)
* A duration (`10:15-10:30`)
* A description (`Install Taxi`)

Aliases allow you to map meaningful names to activity ids. At that point
you'll probably don't really know what alias to use, so let's just try that for
now and we'll see what Taxi has to say about it.

Save the file and close your editor. You should see Taxi displaying a summary
of what you did::

    Staging changes :

    Monday 09 may

    intro (inexistent alias)        0.25  Install Taxi
        Did you mean one of the following: _internal, _infra, _interview?
                                    0.25

    Total                           0.25

    Use `taxi ci` to commit staging changes to the server

.. note::

    Depending on the editor you're using you might not see anything happening
    when you close the file and you might need to run `taxi status` to get this
    output.

Whoops! It looks like the alias we used doesn't exist. Taxi tried to help us by
suggesting similar matches among available aliases, and actually `_internal`
looks like the correct alias to use. We could have searched for aliases that
look like `internal` with the following command: ``taxi alias list internal``.

.. note::
    This alias `_internal` exists because we ran `taxi update` before, which
    synchronized the aliases database from the remote backend. You can also use
    custom aliases that will not be shared with the remote backend. Refer to
    the `alias` command help by running ``taxi alias --help``.

Let's edit our file once again and fix that::

    taxi edit

Replace the `intro` alias with `_internal`::

    09/05/2016

    _internal 10:15-10:30 Install Taxi

Close your editor and run `taxi status` if needed and check the output::

    Staging changes :

    Monday 09 may

    _internal (7/16, liip)          0.25  Install Taxi
                                    0.25

    Total                           0.25

    Use `taxi ci` to commit staging changes to the server

You can now see the `_internal` alias has been recognized as mapped to project
id 7, activity id 16 on the `liip` backend. If you're satisfied with that, you
can now push this to the remote server (`ci` is a shorthand for `commit`, which
is equivalent)::

    taxi ci

Searching for aliases
~~~~~~~~~~~~~~~~~~~~~

The whole point of Taxi is to record your time spend on activities, but how do you know which activities you can use?
As explained in the introduction, activities are fetched with the `update` command. To see the available aliases, use
the `alias list` command::

    $> taxi alias list

    [dummy] my_alias -> 2000/11 (My project, my activity)

The part that appears in brackets is the backend that will be used to push the entries when using the `commit` command.
The information on the right of the arrow is the "mapping", that is a project id and an activity id, whose names are in
parentheses.

You can search for a specific alias by adding a search string to the `alias list` command::

    $> taxi alias list my_awesome_alias

You can also limit the results to aliases you have already used in your timesheets with the `--used` option::

    $> taxi alias list --used

Filtering entries
~~~~~~~~~~~~~~~~~

The `status` and `commit` options support the `--since`, `--until` and `--today/--not-today` options that allow you to
specify which entries should be included in the command. For example let's say you entered entries for yesterday and
today (Wednesday 21 june)::

    $> taxi status
    Staging changes :

    Tuesday 20 june

    _internal                       0.25  Install Taxi
                                    0.25
    Wednesday 21 june

    _internal                       1.00  First steps with Taxi
                                    1.00

    Total                           1.25

    Use `taxi ci` to commit staging changes to the server

And you only want to commit yesterday's entry. You can use the `--not-today` option that will ignore today's entries.
Since you can use this option both with the `status` and `commit` command, you can review what you're about to commit
with the `status` command::

    $> taxi status --not-today
    Staging changes :

    Tuesday 20 june

    _internal                       0.25  Install Taxi
                                    0.25

    Total                           0.25

    Use `taxi ci` to commit staging changes to the server

If you wanted to only include today's entries, you could use the `--since` option. Both `--since` and `--until` support
the following notations:

    * Relative: 5 days ago, 2 weeks ago, 1 month ago, 1 year ago, today, yesterday
    * Absolute: 21.05.2017

Back to our entries, let's filter yesterday's entry::

    $> taxi status --since=today
    Staging changes :

    Wednesday 21 june

    _internal                       1.00  First steps with Taxi
                                    1.00

    Total                           1.00

    Use `taxi ci` to commit staging changes to the server

In fact, the `--today` option is just a shortcut for `--since=today --until=today`.

Ignored entries
~~~~~~~~~~~~~~~

You'll sometimes have entries for which you're not sure which alias you should
use and that shouldn't be pushed until you have a confirmation from someone
else. Simply prefix the entry line with `?` and the entry will be ignored. If we
run the ``edit`` command and add a question mark to our ``pingpong`` alias like
so::

    23/02/2015

    ? pingpong 09:00-10:30 Play ping-pong

The output becomes::

    Staging changes :

    Monday 23 february
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

Internal aliases
~~~~~~~~~~~~~~~~

Some people like to timesheet everything they do: lunch, ping-pong games, going
to the restroom... anyway, if you're that kind of people you probably don't
want these entries to be pushed. To achieve that, start by adding a dummy
backend to your configuration file (by default `~/.config/taxi/taxirc` or
`~/.taxirc`)::

    [backends]
    internal = dummy://

Then to add an internal alias, either add it in the corresponding section in
your configuration file::

    [internal_aliases]
    _pingpong
    _lunch
    _shit

Or use the ``alias`` command::

    taxi alias add -b internal _pingpong ""

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

Backends
--------

.. note::
    The `plugin` command is available starting from Taxi 4.2.

Backends are provided through Taxi plugins. To install (or upgrade) a plugin,
use the `plugin install` command::

    taxi plugin install zebra

This will fetch and install the backend plugin. Once installed, you'll still
need to tell Taxi to use it. This is explained in the next section.

You can also see which plugins are installed with `plugin list`::

    $> taxi plugin list
    zebra (1.2.0)

.. note::

    This is only valid if you installed Taxi with the install script, that
    transparently deals with installing Taxi in an isolated environment. If you
    installed it differently (eg. by using a Debian package or by using pip),
    either install the corresponding Debian package for the backend you want to
    use or use pip (eg. ``pip install taxi-zebra``).

Configuration
~~~~~~~~~~~~~

The configuration file uses the `XDG user directories <https://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html>`_ specification. This means the location is the following:

    * Linux: ``~/.local/share/taxi/.taxirc``
    * OS X: ``~/Library/Application Support/taxi/.taxirc``
    * Windows: ``C:\Documents and Settings\<User>\Application Data\Local Settings\sephii\taxi\.taxirc``

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
        >>> parse.quote('my_password', safe='')

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

You can use any datetime placeholder defined in `the strftime documentation
<http://docs.python.org/library/datetime.html#strftime-and-strptime-behavior>`_.
**However** taxi only supports the ``%Y`` and ``%m`` placeholders to check for
previous timesheets (used for example when you run ``taxi edit X``, where ``X``
is the number of timesheets to go back in time).

regroup_entries
~~~~~~~~~~~~~~~

Default: true

If set to false, similar entries (ie. entries on the same date that are on the
same alias and have the same description) won't be regrouped.

.. note::
    This setting is available starting from Taxi 4.1

nb_previous_files
~~~~~~~~~~~~~~~~~

Default: 1

Defines the number of previous timesheet files Taxi should try to parse. This
allows you to make sure you don't forget hours in files from previous months
when starting a new month.

This option only makes sense if you're using date placeholders in
:ref:`config_file`.

Flags characters customization
------------------------------

By default Taxi uses the `=` character for pushed entries and `?` for ignored entries. You can customize them in the
`[flags]` section of the configuration file. Note that using `#` as a flag character will make any flagged entry
interpreted as a comment and won't be parsed by Taxi. Example of using custom characters for the `ignored` and `pushed`
flags::

    [flags]
    ignored = !
    pushed = @
