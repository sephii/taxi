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

The easiest way to install Taxi is by using the installation script::

    curl https://raw.githubusercontent.com/sephii/taxi/installer/install.sh | sh

The installer will guide you through the process of getting Taxi installed on
your system.

Head over to the `documentation
<http://taxi-timesheets.readthedocs.org/en/master/userguide.html>`_ for a
complete guide on how to use Taxi.

.. _supported_backends:

Supported backends
==================

* `Zebra <https://github.com/sephii/taxi-zebra>`_
