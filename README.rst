.. image:: https://raw.githubusercontent.com/sephii/taxi/master/doc/images/taxi.png

What is Taxi ?
==============

Taxi is a timesheeting tool that focuses on simplicity to help you write your
timesheets without wasting time. All you'll do is edit a text file and write
down what you've worked on and how long, like so::

    23/01/2014

    pingpong 09:00-10:00 Play ping-pong
    infra         -11:00 Repair coffee machine

You can then get a summary of your timesheet::

    Staging changes :

    # Thursday 23 january #
    pingpong (123/456)             1.00  Play ping-pong
    infra (123/42)                 1.00  Repair coffee machine
                                   2.00

    Total                          2.00

    Use `taxi ci` to commit staging changes to the server

Through the use of backends, Taxi allows you to push your timesheets to
different systems.

Installation
============

Refer to the `"Installation" section
<https://taxi-timesheets.readthedocs.io/en/master/userguide.html#installation>`_
in the docs.

.. _supported_backends:

Supported backends
==================

* `zebra <https://github.com/sephii/taxi-zebra>`_ : Liip's zebra backend
* `tempo <https://github.com/alexandreblin/taxi-tempo>`_ : Atlassian JIRA's `Tempo Timesheets <https://tempo.io>`_ backend
* `tipee <https://github.com/alexandreblin/taxi-tipee>`_ : Gammadia's `tipee <https://tipee.ch>`_ backend
* `bexio <https://github.com/alexandreblin/taxi-bexio>`_ : Bexio `Timesheets <https://bexio.com>`_ backend
* `multi <https://github.com/alexandreblin/taxi-multi>`_ : a special backend to push entries over multiple other backends

Contrib packages
================

These resources, not part of Taxi core, provide an enhanced experience for certain use cases.

* `Cabdriver <https://github.com/metaodi/cabdriver>`_ (generate taxi entries based on Google Calendar, Slack, etc)
* `Syntax highlighting for VSCode <https://marketplace.visualstudio.com/items?itemName=LeBen.taxi-syntax-highlighting>`_
* `Vim plugin <https://github.com/schtibe/taxi.vim>`_ (features syntax highlighting, auto completion)
