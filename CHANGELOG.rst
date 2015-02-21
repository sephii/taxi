#########
Changelog
#########

4.0.0 (unreleased)
==================

Added
-----

* Add support for multiple backends (#40).
* Add support for Python 3 (#71).

Changed
-------

* Don't display date error for unmapped or local entries.

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
