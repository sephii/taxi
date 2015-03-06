Welcome to Taxi's documentation!
================================

Contents:

.. toctree::
   :maxdepth: 2

   userguide
   devguide
   api

Taxi is a timesheeting tool that focuses on simplicity to help you write your
timesheets without wasting time. All you'll do is edit a text file and write
down what you've worked on and how long, like so::

    23/01/2014

    pingpong 09:00-10:00 Played ping-pong
    infra         -11:00 Repaired coffee machine

.. _backends_list:

Backends
--------

Your timesheets are stored as plaintext files on your computer, but you'll most
likely want to push them to a central timesheeting tool. To do that, you can
use a Taxi backend. Here's a list of the existing Taxi backends:

* `Zebra <https://github.com/sephii/taxi-zebra>`_

Want to know more? Head over to the :doc:`userguide`.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

