#########
Changelog
#########

3.2.1 (unreleased)
==================

Changed
-------

* Preserve space character (tab or space) used in timesheets. Thanks @krtek4
  (#62).

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
