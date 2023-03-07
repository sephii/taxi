.. image:: https://raw.githubusercontent.com/sephii/taxi/main/doc/images/taxi.png

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

Getting started
===============

Refer to the `"Installation" section
<https://taxi-timesheets.readthedocs.io/en/main/userguide.html#installation>`_
in the docs.

.. _supported_backends:

Supported backends
==================

* `zebra <https://github.com/sephii/taxi-zebra>`__ : Liip's zebra backend
* `tempo <https://github.com/alexandreblin/taxi-tempo>`__ : Atlassian JIRA's `Tempo Timesheets <https://tempo.io>`__ backend
* `tipee <https://github.com/alexandreblin/taxi-tipee>`__ : Gammadia's `tipee <https://tipee.ch>`__ backend
* `bexio <https://github.com/alexandreblin/taxi-bexio>`__ : Bexio `Timesheets <https://bexio.com>`__ backend
* `multi <https://github.com/alexandreblin/taxi-multi>`__ : a special backend to push entries over multiple other backends
* `clockify <https://github.com/sephii/taxi-clockify>`__ : backend for the free timesheeting tool `clockify.me <https://clockify.me/>`_

Contrib packages
================

These resources, not part of Taxi core, provide an enhanced experience for certain use cases.

* `Cabdriver <https://github.com/metaodi/cabdriver>`_ (generate taxi entries based on Google Calendar, Slack, etc)
* `Syntax highlighting for VSCode <https://marketplace.visualstudio.com/items?itemName=LeBen.taxi-syntax-highlighting>`_
* `Vim plugin <https://github.com/schtibe/taxi.vim>`_ (features syntax highlighting, auto completion)
