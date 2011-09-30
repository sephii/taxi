What is taxi ?
==============

Taxi is a new interface for Zebra, based on TKS. Its main advantages are :

*    Easy to install
*    Written in Python (yes, that's an advantage !)
*    Quite extensible
*    More complete

Basically, Taxi allows you to do the following :

*    Parse timesheets and have a summary for each day
*    Create new timesheets
*    Search for projects and their activities
*    Record time spent on an activity

Installation
============

The main prerequesite for Taxi to work is to have python installed, you don't need anything else. Taxi has been tested on Python 2.6.6 and I don't know if it works on other versions, so feedback is welcome.

The installation is done through the setup.py script. Basically, all you have to do is the following (as root or with sudo) :

    python setup.py install

If you already have a working ~/.tksrc file, you're done and you can start using
Taxi by typing `taxi`. Otherwise you'll have to copy the tksrc.sample file to
~/.tksrc and adapt it with your username/password. This default config file will
tell taxi to use entries file from ~/zebra/2011/09.tks (year and month are
automatically set to the current year/month). If you don't want this, simply
change the "file" configuration option. Note that you can use all of [Python's
strftime date
placeholders](http://docs.python.org/library/datetime.html#strftime-and-strptime-behavior)
in the `file` path.

That's it, you're ready to go!

What's next?
============

The next step will be to search for projects you're working on and add them to
your ~/.tksrc file (it already contains a set of commonly used projects). First
of all you'll have to build the local projects database with the `update` command
(you'll only have to run this from time to time, run it if you don't find a
project you're looking for with the `search` command):

    taxi update

Then, use the `search` command like so:

    taxi search project_name

This will give you the project id. Then you can see the activities attached to
this project with the `show` command like so:

    taxi show project_id

Then just add the activities you're interested in with a meaningful name to your
.tksrc file. Now you can start writing your hours with the following command:

    taxi edit

... or you can simply open your entries file manually (and perhaps create it if
it doesn't exist yet), without using taxi at all. Have a look at the
zebra.sample file for an example. Also if the `edit` command doesn't open your
preferred editor, check your EDITOR environment variable.

Then when you have finished noting your hours, use the `status` (shortcut `stat`) to
check what you're about to commit:

    taxi stat

Now, if you're satisfied with this, commit your hours to the server with the
`commit` command (shortcut `ci`):

    taxi ci

Advanced usage
==============

You can use the `start` and `stop` commands to let taxi edit your entries file
for you. For example, suppose you're going to start a meeting:

    taxi start liip_meeting

This will create an entry in your entries file with the current time and an
undefined end time. Now do your meeting, and when it's finished, just type:

    taxi stop "Discussed about some great stuff"

And taxi will add the end time and the description to the previously created
entry. You'll probably need to adapt the times at the end of the day to round
them to 15 minutes since taxi is unable to handle this at the moment.
