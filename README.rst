**Abstract.** ``nota`` is an open-source application for recording
textual notes and associated meta-information that may be used for later
retrieval.

See also
========

This README file is a bit of an artifact, and much of its material belongs
instead on the nota website http://dankelley.github.io/nota/documentation.html.
The other weakness of this document is that it combines notes for the user and
notes for developers.

Caution
=======

``nota`` is in a phase of active development. That means that many of its
offerings are subject to change. Alterations may be made in its command-line
arguments and in its output format. There may also be changes in the schema of
the database that ``nota`` uses, although these should typically not affect
users because the first thing ``nota`` does when it launches is to check
whether the database needs updating.

The hope is for ``nota`` to settle into a stable version by the middle of 2015,
following a period of alpha/beta testing in the first quarter of the year.

Those who wish to test ``nota`` are asked to report bugs on the github website,
and advised to make frequent backups of their database.

Overview
========

Most people find it helpful to store notes on a computer. Some use specialized
applications for this, while others prefer the simplicity of recording their
thoughts in a plain-text file, using a familiar text editor. In this second
option, it is common to associate the text files with projects or tasks.
Depending on the intent, the file might be named "README" or perhaps something
more meaningful, such as "PLANS," "TASKS," "BUGS," "IDEAS," etc. Thus, for M
projects and N categories, there might be M x N files, and the handling of all
those files can grow complicated, whether adding new material or finding old
material.

A reasonable solution is to have a single file, in which notes can be stored
along with meta-information, such as keywords. For example, plans for a project
named "foo" might be flagged with the keywords *foo* and *plans*, and
retrieving those plans would be a simple matter of filtering on those keywords.

Storing notes along with keywords (and other meta-information, such as the
date, the author, etc.) is somewhat complicated in a text file that is to be
edited with a general text editor, because a typo might damage the file.
Storing notes in a database is a good solution to this problem, and it offers
the additional advantage of greatly improved lookup speed. The disadvantage of
the database, however, is that an application is required to act as an
interface between the user and the data. If the application is commercial, then
users expose themselves to the risk of losing all their work, if the company
stops supporting the software.

The ``nota`` application (named for the Latin phrase "nota bene", perhaps
pronounced "note ah" by some and "note eh" by Canadians) is designed with all
these things in mind. It is deliberately restricted in its features, focussing
on the creation of textual notes and their retrieval. Complex formatting is not
provided, nor is the ability to add non-textual material. In the present early
version, ``nota`` functions entirely at the unix command line, and is most
suited for power users who are unafraid of that environment.

The development model for ``nota`` is entirely open-source, and the coding
relies on popular tools that will be familiar to many programmers, mitigating
against obsolescence.

Using nota
==========

Installation
------------

To install from the official site, use

::

    sudo pip install nota

or, if you're upgrading, use

::

    sudo pip install nota --upgrade

To install a test version, see "Developer notes" near the end of this
file.

Specifying a database file
--------------------------

The default database file is ``~/Dropbox/nota.db``, but this may not
suit all users, so there are two ways to specify a different file. The
first way is to supply the filename as an argument, e.g.
``nota --database ~/nota.db``. The second way is to name a default
database in an initialization file named ``~/.notarc``; for example
notes on a project called ``foo`` might be referred to as follows.

::

    database = "~/Dropbox/nota-foo.db"

Create a database
-----------------

When ``nota`` is first used, it will create a database with a name as
described in the previous section.

Add notes
---------

This may be done one at a time, with commandline arguments, e.g.

::

    nota --add --keywords 'lecture,physics,MIT' --title="Walter Lewin physics lectures" --content="http://ocw.mit.edu/courses/physics/8-01-physics-i-classical-mechanics-fall-1999/index.htm"

Another method is with an editor-based supply of the information, which
is done unless ``--add`` and ``--title`` are both given

::

    nota --add # opens editor

or (using abbreviated args)

::

    nota -a -t "title"                            # no editor
    nota -a -t "title" -c "content" -k "keywords" # no editor


Listing notes
-------------

Listing notes in simplified format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To list all notes, use

::

    nota

Note that the first few characters (preceding the ``:`` character) are
a "hash" that can be used to specify particular notes.

To find notes with a given keyword, use e.g.

::

    nota --keyword "lecture"
    nota -k "lecture"

Note that the search is fuzzy, so that e.g. "leture" would get the same
results as "lecture". However, this scheme can have surprising results,
so the ``--strict`` command-line argument is provided, to do strict
searches.

To show notes with hash starting with the letter ``a``, use

::

    nota a

To find a specific note, type enough characters of the hash to make it
unique.

Listing notes in markdown
~~~~~~~~~~~~~~~~~~~~~~~~~

Do as above but use the markdown mode, e.g.

::

    nota -a -m markdown

This is perhaps most useful when piped into a markdown formatter, e.g.

::

    nota 1 -m markdown | pandoc > ~/a.html

yields an HTML file that can be reasonably well-formatted in a browser.

(For more on Markdown, see e.g.
`here <http://daringfireball.net/projects/markdown>`__.)


Editing notes
-------------

To edit e.g. a note specified with hash ``a``, use

::

    nota -e a

which opens up the text editor you have specified in your ``EDITOR``
environment variable, or the ``vim`` editor if you have not specified
this variable, just as if a new note were being created.

Alter a keyword
~~~~~~~~~~~~~~~

FIXME: this does not work at present.

Use e.g.

::

    nota -e -k OAR=oar

so that all notes with keyword "OAR" will henceforth have that keyword
changed to "oar".

Deleting notes
--------------

Continuing with the example

::

    nota --delete a

deletes the note with hash code uniquely defined by first letter ``a``
(use more letters to make unique).

Sharing notes
-------------

See the nota website.

Archiving the nota database
---------------------------

Advanced users may want to dump the whole database with

::

    echo ".dump" | sqlite3 nota.db

Back up the database
~~~~~~~~~~~~~~~~~~~~

It is a good idea to set up a crontab entry like the following, to back
up the database daily (adjust the filenames appropriately).

::

    @daily echo ".dump" | sqlite3 /Users/kelley/Dropbox/nota.db | gzip -c > /Users/kelley/backup/nota/nota-`date +\%Y-\%m-\%d-\%H\%M`.gz

(This could be done better by checking the sha value of the file, to
only backup when things have changed.)

Task count in bash prompt
~~~~~~~~~~~~~~~~~~~~~~~~~

To get a list of notes that are due today, put the following in your
``~/.bash_profile`` file:

::

    function nota_count {
        nota --due today --count
    }
    PS1="\h:\W"
    export PS1="$PS1<\$(nota_count)> "

Suggested aliases for nota
--------------------------

The developer uses the following, alias to avoid typing three characters.

::

    alias n=nota

