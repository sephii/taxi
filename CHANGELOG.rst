3.2.0 (unreleased)
==================

* Add changelog
* Add local aliases support. This be controlled with the ``local_aliases`` setting. Thanks @krtek4 (#24)
* Regroup entries that have the same activity and description and that are on the same date (#14)
* Add previous entries files parsing. This can be controlled with the ``nb_previous_files`` setting (#15)
* Add colors to easily spot entries that failed to be pushed (#39)
* Make Taxi commands still work even if some entries contain unmapped aliases (#54)
* The ``alias`` command now orders aliases by id (#28)
* The ``update`` command doesn't add shared aliases belonging to closed projects anymore (#50)
* The ``clean-aliases`` command now also cleans shared aliases (#35)
* Improve error output by displaying the stacktrace only of Python exceptions
