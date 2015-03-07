**Abstract.** ``nota`` is an open-source application for recording
textual notes and associated meta-information that may be used for later
retrieval.

The documentation for nota resides at http://dankelley.github.io/nota. The
present README file is an historical artifact, and it will gradually be
whittled away as material is transferred to the
http://dankelley.github.io/nota.


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


