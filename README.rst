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

Installation
============

The easiest way to install Taxi is by using ``pip``. This will fetch the latest
stable version and install it on your system::

    sudo pip install taxi

You'll mostly want to install a backend as well. Backends allow you to push
your timesheets to a remote location. The list of available backends can be
found below in :ref:`supported_backends`.

That's it! You should now be able to run ``taxi``. Head over to the
`documentation <http://taxi-timesheets.readthedocs.org/en/master/userguide.html>`_ for a complete guide
on how to use Taxi.

Upgrading to 4.0
================

Starting with Taxi 4, backends are shipped separately from Taxi itself. This
allows you to plug Taxi on whatever backend you're using, or even allows you to
use multiple backends in parallel.

The default backend Taxi used in previous versions is the Zebra backend. Since
it is now shipped as a separate module, you'll need to install it as well if
you're ugrading from a previous version of Taxi::

    sudo pip install taxi-zebra

.. _supported_backends:

Supported backends
==================

* `Zebra <https://github.com/sephii/taxi-zebra>`_
