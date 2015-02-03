What is taxi ?
==============

Taxi is a new interface for Zebra, based on TKS. Its main advantages are :

* Easy to install
* Written in Python (yes, that's an advantage !)
* Quite extensible
* More complete

Basically, Taxi allows you to do the following :

* Parse timesheets and have a summary for each day
* Create new timesheets
* Search for projects and their activities
* Record time spent on an activity

Installation
============

The main prerequesite for Taxi to work is to have python installed, you don't
need anything else. Taxi has been tested on Python 2.6.6 and I don't know if it
works on other versions, so feedback is welcome.

The easiest way to install taxi is by using ``pip``. This will fetch the latest
stable version and install it on your system (this can also be used to upgrade
an existing taxi install) ::

    sudo pip install -U taxi

That's it! You can now skip to the `Configuration`_ section.

If you don't have ``pip``, you should be able to install it with
``easy_install`` ::

    sudo easy_install pip

Installing from the source
--------------------------

Fetch the source, extract it, and install dependencies with ::

    git clone git@github.com:sephii/taxi.git && cd taxi
    ./setup.py install

If you want to modifiy the source code and test it (aka start to be a contributor) ::

    ./setup.py develop

This command will link the ``taxi`` binary to the directory where you cloned
taxi. It is recommended you run this command in a virtualenv so that it doesn't
interfere with the version of taxi installed on your system.

To run the tests, use the following command::

    ./setup.py test

Configuration
=============

If you already have a working ~/.tksrc file (because you were using tks before),
you're done and you can start using Taxi by typing ``taxi``. Otherwise you'll
have to copy the ``doc/tksrc.sample`` file to ~/.tksrc and adapt it with your
username/password.

That's it, you're ready to go!

What's next?
============

The next step will be to search for projects you're working on and add them to
your ~/.tksrc file (it already contains a set of commonly used projects). First
of all you'll have to build the local projects database with the ``update`` command
(you'll only have to run this from time to time, run it if you don't find a
project you're looking for with the ``search`` command)::

    taxi update

Then, use the ``search`` command like so::

    taxi search project_name

This will give you the project id. Then you can see the activities attached to
this project with the ``show`` command like so::

    taxi show project_id

Then just add the activities you're interested in with a meaningful name to your
.tksrc file.

Another way to easily add an activity to your .tksrc file is the ``add`` command.
Basically, the ``add`` command is an improved version of the ``search`` which will
ask you for an alias and add it to your .tksrc file.

Now you can start writing your hours with the following command::

    taxi edit

... or you can simply open your entries file manually (and perhaps create it if
it doesn't exist yet), without using taxi at all. Have a look at the
zebra.sample file for an example. Also if the ``edit`` command doesn't open your
preferred editor, check your EDITOR environment variable.

Then when you have finished noting your hours, use the ``status`` (shortcut
``stat``) to check what you're about to commit::

    taxi stat

Now, if you're satisfied with this, commit your hours to the server with the
``commit`` command (shortcut ``ci``)::

    taxi ci

Entries file syntax
===================

The syntax of the entries file is the following::

    date_line
    activity_alias time description
    activity_alias time description
    ...

date_line is a date in one of the following formats:

    * dd/mm/yyyy
    * dd/mm/yy
    * yyyy/mm/dd

activity_alias is the alias to the activity that you put in your .tksrc file. If
it ends with a question mark, the entry will be ignored (ie. not pushed).

time is the duration of the activity in one of the following format:

    * h (duration in hours, eg. 0.75, 1.5, etc)
    * hh:mm-hh:mm
    * hh:mm-? (will make the entry to be ignored)
    * -hh:mm (will use the previous line as start time)
    * hh:mm can also be replaced by hhmm

description is the description of the entry.

Start/stop usage
================

You can use the ``start`` and ``stop`` commands to let taxi edit your entries file
for you. For example, suppose you're going to start a meeting::

    taxi start liip_meeting

This will create an entry in your entries file with the current time and an
undefined end time. Now do your meeting, and when it's finished, just type::

    taxi stop "Discussed about some great stuff"

And taxi will add the end time, rounded to 15 minutes, and the description to
the previously created entry.

Getting help
============

Run taxi without any argument to get an overview of available commands and
options. You can also use the ``help`` command followed by the name of a command
to get detailed help on any command.
