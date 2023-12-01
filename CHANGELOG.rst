#########
Changelog
#########

6.3.1 (2023-12-01)
==================

Fixed
-----

* Fix plugins on Python < 3.10 (regression from 6.3.0).

6.3.0 (2023-11-30)
==================

Changed
-------

* Use flit instead of setuptools for packaging.

6.2.0 (2023-05-15)
==================

Added
-----

* Add Activity.is_active attribute. Thanks @OdyX.

Fixed
-----

* Fix virtual environment detection (#144)

6.1.1 (2021-09-21)
==================

Fixed
-----

* Fix timesheet edition on Windows (#141)

6.1.0 (2021-08-21)
==================

Changed
-------

* Write timesheet files atomically to prevent data loss
* Allow empty description in timesheets

6.0.1 (2020-11-03)
==================

Fixed
-------

* Do not crash if Taxi data dir doesn't exist (#138)

6.0 (2020-08-18)
================

Changed
-------

* Add timesheet path in error message when trying to create entries with negative duration

6.0rc2 (2020-08-06)
===================

Changed
-------

* Log to a file (``~/.local/share/taxi/taxi.log``) instead of stdout
* Push errors are now logged

6.0rc1 (2020-08-04)
===================

Added
-----

* Add support for more date format codes (days, weeks, months and years) in the ``file`` setting
* Add new ``round_entries`` setting to customize entries duration rounding
* Add installation instructions for Nix and Debian systems
* Add error message when trying to create entries with negative duration (#113)

Changed
-------

* Don't force projects and activities ids to be integers
* Remove "shared aliases" from the config file
* Remove unused ``price`` parameter from the ``Activity`` class

Fixed
-----

* Allow editing invalid configuration files with the ``config`` command (#135)

5.0 (2019-12-27)
================

Added
-----

* Add `current` command to show the current entry in progress
* Add `config` command to open the configuration file

Changed
-------

* Drop support for Python < 3.5

Fixed
-----

* Do not overwrite existing entry description when using the `stop` command
* Make `stop` command support chained durations

4.5.2 (2019-08-29)
==================

Changed
-------

* Add `--verbose` / `-v` flag

4.5.1 (2019-01-22)
==================

Changed
-------

* Allow 0 values in aliases mappings

4.5.0 (2019-01-02)
==================

Changed
-------

* Added support for more information in aliases (= roles)

4.4.2 (2018-09-25)
==================

Changed
-------

* Fix the broken stop command (#111)

4.4.1 (2017-11-27)
==================

Fixed
-----

* Accept project and activity ids longer than 4 digits

4.4.0 (2017-11-27)
==================

Added
-------

* Allow to pass the new entry description to the `start` command.

4.3.2 (2017-09-21)
==================

Changed
-------

* Display meaningful error message if end time from entry duration is not valid.

4.3.1 (2017-08-10)
==================

Added
-----

* Add `--no-inactive` flag to `alias` command to hide aliases mapped to inactive projects.
* Option `--used` in `alias` command can now be used in conjunction with a string filter.

Changed
-------

* Aliases pointing to inactive projects are now displayed in red in `alias` command output.
* Accept decimal duration without leading number in timesheets (eg. `.5`).

4.3.0 (2017-07-13)
==================

Added
-----

* Add support for flags: pushed lines are no longer commented.
* Add previously used aliases as hints to new timesheets.
* Add `--today`, `--since` and `--until` support for `status` and `commit` commands.
* Add `--used` option to `alias list` command (#89).
* Add note about config file location to the user documentation (#106).

Changed
-------

* Fix installation script on OS X when Python 3 is available (#104).
* Default configuration section renamed from `[default]` to `[taxi]`.
* Remove deprecated `search` and `add` commands.
* Make `update` command fetch closed projects as well (#103).

4.2.0 (2016-05-25)
==================

Added
-----

* Add installer script and plugin management commands.


4.1.0 (2016-03-09)
==================

Added
-----

* Add configuration option ``regroup_entries`` (#77).

Changed
-------

* Respect the XDG Base Directory specification
  (http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html).
  Thanks @krtek4.
* Fix help layout for ``alias`` command (#95).
* Merge the ``search`` and ``add`` commands into the ``project`` command (#90).
* Make the ``show`` command much more useful by allowing it to explore aliases,
  project ids and mappings (#87).
* Add colours to ``status`` command output and improve output presentation.

Removed
-------

* Remove ``local_aliases`` option, which can be mimicked by using a dummy
  backend (#85).

4.0.2 (2015-09-14)
==================

Changed
-------

* Fix warnings reported by click when using click >= 5.0.

4.0.1 (2015-04-03)
==================

Added
-----

* Add example for ``local_aliases`` in the user docs (#79).

Changed
-------

* Sort entries by date in commit confirm message (#80).
* Don't mark local aliases as deleted in ``update`` command (#84).
* Don't break indentation when committing entries that use continuation
  durations (#81).
* Comment pushed entries when interrupting ``commit`` command (#82).

4.0.0 (2015-03-11)
==================

Added
-----

* Add support for multiple backends (#40).
* Add support for Python 3 (#71).
* Add support for command matching by prefix (eg. ``taxi e`` for ``taxi
  edit``).
* Add configuration file creation wizard.
* Add file and line information in parsing error messages (#69, #75).
* Add ``--not-today`` option to the ``commit`` command. Thanks @jeanmonod
  (#63).
* Add support for ``yesterday`` and ``today`` values for date options.
* Add support for partial ranges for date options.
* Add argument to ``edit`` command to set which file should be edited (#49).

Changed
-------

* Rename ``--ignore-date-error`` to ``--yes`` and make it interactive if it is
  not set.
* Use `click <http://click.pocoo.org>`_. This should fix encoding and editor
  issues reported in #67.
* Don't display date error for unmapped or local entries.
* Move ``~/.tksrc`` configuration file to ``~/.taxirc``.

3.2.1 (2015-01-16)
==================

Changed
-------

* Preserve space character (tab or space) used in timesheets. Thanks @krtek4
  (#62).
* Don't crash when trying to push entries that don't have a start time and
  don't have a previous entry (#68).
* Correctly show ignored unmapped entries as ignored instead of not mapped in
  status output (#61).

3.2.0 (2014-12-04)
==================

Added
-----

* Add changelog.
* Add local aliases support. This can be controlled with the ``local_aliases``
  setting. Thanks @krtek4 (#24). Refer to ``doc/tksrc.sample`` for more details. 
* Regroup entries that have the same activity and description and that are on
  the same date (#14).
* Add previous entries files parsing. The default is to parse 1 previous file
  but this can be controlled with the ``nb_previous_files`` setting (#15).
  Refer to ``doc/tksrc.sample`` for more details.
* Add colors to easily spot entries that failed to be pushed. Thanks @krtek4
  (#39).
* Create a default configuration file if none exists. Thanks @ghn.

Changed
-------

* Ignore shared aliases belonging to closed projects when running the
  ``update`` command (#50).
* Improve error output by displaying the stacktrace only of Python exceptions.
* Make the ``clean-aliases`` command also clean shared aliases (#35).
* Make Taxi commands still work even if some entries contain unmapped aliases
  (#54).
* Order aliases by id in ``alias`` command output (#28).
