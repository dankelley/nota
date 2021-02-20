#!/usr/bin/python3

import sys
import sqlite3 as sqlite
import datetime
import os.path
import difflib
from distutils.version import StrictVersion
import re
import tempfile
import subprocess
import hashlib
import random
import string
from math import trunc

#reload(sys)
#sys.setdefaultencoding('utf8')

class Nota:
    def __init__(self, db="nota.db", authorId=1, debug=0, quiet=False):
        '''

        A class used for the storing and searching of textual notes in a
        sqlite3 database.  Keywords may be associated to notes, providing a
        convenient way to search for content. File attachments may also be
        made.

        '''
        self.debug = debug
        self.quiet = quiet
        self.db = db
        self.fyi("Database '%s' (before path expansion)." % self.db)
        self.db = os.path.expanduser(self.db)
        self.fyi("Database '%s' (after path expansion)." % self.db)
        mustInitialize = not os.path.exists(self.db)
        if mustInitialize:
            print("Creating new database named \"%s\"." % self.db)
        else:
            try:
                dbsize = os.path.getsize(self.db)
                self.fyi("Database file size %s bytes." % dbsize)
                mustInitialize = not dbsize
            except:
                pass
        try:
            con = sqlite.connect(self.db)
            con.text_factory = str # permits accented characters in notes
        except:
            self.error("Error opening connection to database named '%s'" % db)
        self.con = con
        self.cur = con.cursor()
        self.authorId = authorId
        ## 0.3: add note.modified column
        self.appversion = [0, 8, 9] # db schema changes always yield first or second digit increment
        self.dbversion = self.appversion
        if mustInitialize:
            print("Initializing database; run 'nota' again to use it.")
            self.initialize()
            return(None)
        try:
            v = self.cur.execute("SELECT * FROM version;").fetchone()
            self.dbversion = v
        except:
            self.warning("cannot get version number in database")
            self.dbversion = [0, 0, 0] # started storing version at [0, 1]
            pass
        appversion = "%s.%s.%s" % (self.appversion[0], self.appversion[1], self.appversion[2])
        if len(self.dbversion) == 2:
            dbversion = "%s.%s.%s" % (self.dbversion[0], self.dbversion[1], 0)
        else:
            dbversion = "%s.%s.%s" % (self.dbversion[0], self.dbversion[1], self.dbversion[2])
        self.fyi("appversion: %s" % appversion)
        self.fyi("dbversion: %s" % dbversion)
        self.fyi("self.dbversion: %s" % [self.dbversion])
        if StrictVersion(appversion) > StrictVersion(dbversion):
            if StrictVersion(dbversion) < StrictVersion("0.2"):
                print("Updating database %s to version 0.2.x ..." % db)
                try:
                    self.cur.execute('ALTER TABLE note ADD due DEFAULT "";')
                    self.con.commit()
                    print("  Added column 'due' to database table 'note'.")
                except:
                    self.error("  Problem adding a column named 'due' to the table 'note'")
            if StrictVersion(dbversion) < StrictVersion("0.3"):
                print("Updating database %s to version 0.3.x ..." % db)
                try:
                    self.cur.execute('ALTER TABLE note ADD modified DEFAULT "";')
                    self.cur.execute('UPDATE note SET modified = date;')
                    self.con.commit()
                    print("  Added 'modified' column to 'note' table.")
                except:
                    self.error("  Problem adding a column named 'modified' to the table named 'note'")
            if StrictVersion(dbversion) < StrictVersion("0.4"):
                print("Updating database %s to version 0.4.x ..." % db)
                try:
                    cmd = 'ALTER TABLE note ADD hash DEFAULT "";'
                    self.cur.execute(cmd)
                    self.con.commit()
                except:
                    self.error("Problem creating a 'hash' column in the 'note' table")
                try:
                    cmd = "SELECT noteId,date,title FROM note;"
                    rows = []
                    rows.extend(self.cur.execute(cmd))
                    hash = []
                    noteIds = []
                    for row in rows:
                        noteIds.extend([row[0]])
                        h = self.compute_hash(noteId=row[0], date=row[1], title=row[2])
                        hash.append(h)
                except:
                    self.error("Problem computing hashes of existing notes")
                try:
                    for i in range(len(rows)):
                        self.fyi("UPDATE note SET hash = \"%s\" WHERE noteId=%s;" % (str(hash[i]), noteIds[i]))
                        self.cur.execute("UPDATE note SET hash = ? WHERE noteId=?;", (str(hash[i]), noteIds[i]))
                    self.con.commit()
                    print("  Added 'hash' column to 'note' table.")
                except:
                    self.error("Problem adding a column named 'hash' to the table named 'note'")
                    self.error("Problem saving data to the newly-formed 'hash' column in the 'note' table")
            if StrictVersion(dbversion) < StrictVersion("0.5"):
                # Add 'in_trash' column (removed in version 0.7.x)
                print("Updating database %s to version 0.5.x ..." % db)
                try:
                    cmd = 'ALTER TABLE note ADD in_trash DEFAULT 0;'
                    self.cur.execute(cmd)
                    self.con.commit()
                    print("  Added 'in_trash' column to 'note' table.")
                except:
                    self.error("Problem adding a column named 'in_trash' to the table named 'note'")
            if StrictVersion(dbversion) < StrictVersion("0.6"):
                print("Updating database %s to version 0.6.x ..." % db)
                try:
                    self.cur.execute("DROP TABLE version;")
                    self.cur.execute("CREATE TABLE version(major, middle, minor);")
                    self.cur.execute("INSERT INTO version(major, middle, minor) VALUES (?,?,?);",
                            (self.appversion[0], self.appversion[1], self.appversion[2]))
                    self.con.commit()
                    print("  Added 'middle' column to 'version' table.")
                except:
                    self.error("Problem adding a 'middle' column to the 'version' table.")
            if StrictVersion(dbversion) < StrictVersion("0.7"):
                # Books were added in 0.7.0, so the in_book column of the note table must be
                # removed and a new column, 'book', added. This requires copying the whole
                # 'note' table, because sqlite3 doesn't permit such modifications (!).
                # The new table will have new noteId values, so we also must alter the
                # contents of the notekeyword table. The work is chopped up into
                # little steps, so that if errors arise, it will be easier to see what
                # went wrong.
                print("Updating database %s to version 0.7.x ..." % db)
                try:
                    oldIds = []
                    oldIds.extend(self.cur.execute("SELECT noteId from note;"))
                except:
                    self.error("Cannot access old note Ids")
                try:
                    self.cur.execute('ALTER TABLE note RENAME TO note_orig;')
                except:
                    self.error("Problem with step 1 of update to version 0.7.x (renaming note table to note_orig)")
                try:
                    self.cur.execute('CREATE TABLE note (noteId integer primary key autoincrement, authorId, date, modified, due, title, content, hash, privacy DEFAULT 0, book DEFAULT 1);')
                except:
                    self.error("Problem with step 2 of update to version 0.7.x (creating new note table)")
                try:
                    self.cur.execute('INSERT INTO note(authorId, date, modified, due, title, content, hash, privacy, book) SELECT authorId, date, modified, due, title, content, hash, privacy, in_trash AS book FROM note_orig;')
                except:
                    self.error("Problem with step 3 of update to version 0.7.x (filling up the new note table)")
                try:
                    self.cur.execute("DROP TABLE note_orig;")
                except:
                    self.error("Problem with step 4 of update to version 0.7.x (dropping note_orig)")
                try:
                    noteIds = []
                    noteIds.extend(self.cur.execute("SELECT noteId,book FROM note;"))
                except:
                    self.error("Problem with step 5 of update to version 0.7.x")
                # convert in_trash to book
                for n in noteIds:
                    try:
                        self.cur.execute("UPDATE note SET book=? WHERE noteId=?;", (int(1-n[1]), n[0]))
                    except:
                        self.error("Problem with step 5 of update to version 0.7.x (noteId=%s)" % n[0])
                self.con.commit()
                print("  Replaced 'in_trash' column in 'note' with 'book' column, and set up 'book' table.")
                # Fix up the note-keyword connections.
                if len(noteIds) != len(oldIds):
                    self.error("error in number of notes")
                #print("oldIds: %s" % oldIds)
                #print("noteIds: %s" % noteIds)
                for i in range(len(noteIds)):
                    self.fyi("UPDATE notekeyword SET noteid=%s WHERE noteid=%s;" % (oldIds[i][0], noteIds[i][0]))
                    try:
                        self.cur.execute("UPDATE notekeyword SET noteid=? WHERE noteid=?;", (noteIds[i][0], oldIds[i][0]))
                    except:
                        self.error("error in: UPDATE notekeyword SET noteid=%s WHERE noteid=%s;" % (noteIds[i][0], oldIds[i][0]))
                self.con.commit()
                print("  Updated note-keyword linkage table.")

                # set up book names
                self.cur.execute("CREATE TABLE book(bookId integer primary key autoincrement, number, name DEFAULT '');")
                self.cur.execute("INSERT INTO book(number, name) VALUES (0, 'Trash');")
                self.cur.execute("INSERT INTO book(number, name) VALUES (1, 'Default');")
                print("  Created books named Trash and Default.")

            if StrictVersion(dbversion) < StrictVersion("0.8"):
                # Attachments were added in 0.8.0, so we need a table to cross-reference
                # each attachment to a storage location, plus a table linking notes and
                # attachments.
                print("Updating database %s to version 0.8.x ..." % db)
                ## Attachments
                try:
                    self.cur.execute("CREATE TABLE attachment (attachmentId integer primary key autoincrement, filename, contents BLOB);")
                except:
                    self.error("Problem with step 1 of update to version 0.8.x (adding table for internal attachments)")
                try:
                    self.cur.execute("CREATE TABLE note_attachment (note_attachmentId integer primary key autoincrement, noteId, attachmentId);")
                except:
                    self.error("Problem with step 2 of update to version 0.8.x (adding note-attachment table)")
            # OK, done with the updates, so we now update the actual version number.
            try:
                self.cur.execute("DROP TABLE version;")
                self.cur.execute("CREATE TABLE version(major, middle, minor);")
                self.cur.execute("INSERT INTO version(major, middle, minor) VALUES (?,?,?);",
                        (self.appversion[0], self.appversion[1], self.appversion[2]))
                self.con.commit()
            except:
                self.error("  Problem updating database version to %d.%d.%d" %
                        (self.appversion[0], self.appversion[1], self.appversion[2]))
            print("Database %s is now up-to-date with this version of 'nota'." % db)
        else:
            self.fyi("Database %s version is up-to-date." % db)


    def fyi(self, msg, prefix="  "):
        if self.debug:
            print(prefix + msg, file=sys.stderr)


    def warning(self, msg, prefix="Warning: "):
        if not self.quiet:
            print(prefix + msg, file=sys.stderr)


    def error(self, msg, level=1, prefix="Error: "):
        if not self.quiet:
            print(prefix + msg, file=sys.stderr)
        sys.exit(level)


    def version(self):
        return("nota version %d.%d.%d" % (self.appversion[0], self.appversion[1], self.appversion[2]))


    def compute_hash(self, noteId, date, title):
        '''
        Compute a hash. This is somewhat resistant to errors, e.g. if somehow the date is None,
        this will still work.
        '''
        if not noteId:
            noteId = ''.join(random.choice(string.digits) for _ in range(4))
        if not date:
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not title:
            title = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(100))
        #print(str(title)+str(noteId)+str(date))
        return(hashlib.sha256((str(title) + str(noteId) + str(date)).encode('utf8')).hexdigest())


    def book_name(self, number):
        '''Return name of book with given index.'''
        try:
            name = self.cur.execute("SELECT name FROM book WHERE number = ?;", [number]).fetchone()
        except:
            self.error("cannot look up name of book number %s" % number)
        return(str(name[0]))


    def book_number(self, name):
        '''Return number of book with given name.'''
        try:
            number = self.cur.execute("SELECT number FROM book WHERE name= ?;", [name]).fetchone()
        except:
            self.error("cannot look up number of book with name %s" % name)
        return(number)


    def list_books(self):
        ''' Return the list of book names '''
        names = []
        try:
            for n in self.cur.execute("SELECT name FROM book;").fetchall():
                names.extend(n)
        except:
            self.error("ERROR: cannot find database table 'book'")
        return(names)


    def create_book(self, name):
        """Create a new book"""
        name = name.strip()
        if not len(name):
            self.error("Cannot have a blank book name")
        # The next could be relaxed, if users want commas in book names, but
        # I prefer to keep it, in case later there could be a syntax for multiple
        # book names, using comma.
        if name.find(",") >= 0:
            self.error("Cannot have a ',' in a book name")
        existing = self.list_books()
        nexisting = len(existing)
        if name in existing:
            self.error("Already have a book named '%s'" % name)
        try:
            self.cur.execute("INSERT INTO book (number, name) VALUES(?, ?);", (nexisting, name))
            self.con.commit()
        except:
            self.fyi("Error adding a book named '%s'" % name)


    def book_index(self, book):
        match = len(book) # permit initial-letters partial match
        existing = self.list_books()
        matches = {}
        for i in range(len(existing)):
            if book.lower() == existing[i][0:match].lower():
                matches[existing[i]] = i
        return(matches)


    def change_book(self, hash, book):
        b = self.book_index(book)
        if len(b) > 1:
            self.error("Abbreviation '%s' matches to %d books: %s" % (book, len(b), list(b.keys())))
        if len(b) == 0:
            self.error("No book '%s'" % book)
        book_number = int(list(b.values())[0])
        note = self.find_by_hash(hash)
        if len(note) > 1:
            self.error("The hash '%s' matches more than one note; try giving more letters" % hash)
        if len(note) == 0:
            self.error("The hash '%s' does not match any notes" % hash)
        noteId = int(note[0]['noteId'])
        self.fyi("UPDATE note SET book=%s WHERE noteId=%s;" % (book_number, noteId))
        try:
            self.cur.execute("UPDATE note SET book=? WHERE noteId=?;", [book_number, noteId])
            self.con.commit()
        except:
            self.error("Cannot change book number to %s where noteId is %s" % (book_number, noteId))


    def rename_book(self, old, new):
        if old == "Trash":
            self.error("Cannot rename the 'Trash' book.")
        if new == "Trash":
            self.error("Cannot rename any book to 'Trash'.")
        existing = self.list_books()
        if old in existing:
            try:
                self.cur.execute("UPDATE book SET name=(?) WHERE name=(?);", (new, old))
                self.con.commit()
            except:
                self.fyi("Error changing book name from '%s' to '%s'" % (old, new))
        else:
            self.error("There is no book named '%s'." % old)



    def initialize(self, author=""):
        ''' Initialize the database.  This is dangerous since it removes any
        existing content.'''
        self.cur.execute("CREATE TABLE version(major, minor);")
        self.cur.execute("INSERT INTO version(major, minor) VALUES (?,?);",
                (self.appversion[0], self.appversion[1]))
        #20150314 self.cur.execute("CREATE TABLE note(noteId integer primary key autoincrement, authorId, date, modified, due, title, content, hash, privacy DEFAULT 0, in_trash DEFAULT 0);")
        self.cur.execute("CREATE TABLE note(noteId integer primary key autoincrement, authorId, date, modified, due, title, content, hash, privacy DEFAULT 0, book DEFAULT 1);")
        self.cur.execute("CREATE TABLE author(authorId integer primary key autoincrement, name, nickname);")
        self.cur.execute("CREATE TABLE alias(aliasId integer primary key autoincrement, item, alias);")
        self.cur.execute("CREATE TABLE keyword(keywordId integer primary key autoincrement, keyword);")
        self.cur.execute("CREATE TABLE notekeyword(notekeywordId integer primary key autoincrement, noteid, keywordid);")
        self.cur.execute("CREATE TABLE book(bookId integer primary key autoincrement, number, name DEFAULT '');")
        self.cur.execute("INSERT INTO book(number, name) VALUES (0, 'Trash');")
        self.cur.execute("INSERT INTO book(number, name) VALUES (1, 'Default');")
        self.con.commit()


    def add(self, title="", keywords="", content="", attachments="", due="", book=1, privacy=0, date="", modified=""):
        ''' Add a note to the database.  The title should be short (perhaps 3
        to 7 words).  The keywords are comma-separated, and should be similar
        in style to others in the database.  The content may be of any length. The
        attachments are comma-separated, and must be full pathnames to files
        that exist.'''
        #self.debug = 1
        try:
            known_books = []
            for b in self.cur.execute("SELECT number FROM book;").fetchall():
                known_books.extend(b)
        except:
            self.error("cannot look up list of known books")
        #print("known_books %s" % known_books)
        #print("book %s initially" % book)
        if not book in known_books:
            if book != -1:
                self.warning("the book is not known, so switching to \"Default\"")
            book = 1
        #print("book %s later" % book)
        self.fyi("add with title='%s'" % title)
        self.fyi("add with keywords='%s'" % keywords)
        self.fyi("add with attachments='%s' (comma-separated string)" % attachments)
        self.fyi("add with due='%s'" % due)
        self.fyi("add with book='%s'" % book)
        if not isinstance(due, str):
            due = ""
        due = self.interpret_time(due)[0]
        self.fyi("due: %s" % due)
        now = datetime.datetime.now()
        if date == "":
            date = now.strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.cur.execute("INSERT INTO note(authorId, date, modified, title, content, privacy, due, book) VALUES(?, ?, ?, ?, ?, ?, ?, ?);",
                (self.authorId, date, modified, title, content, 0, due, book))
        except:
            self.error("error adding note to the database")
        noteId = self.cur.lastrowid
        self.fyi("noteId: %s" % noteId)
        hash = self.compute_hash(noteId=noteId, date=date, title=title)
        self.fyi("hash: %s" % hash)
        try:
            self.cur.execute("UPDATE note SET hash=? WHERE noteId=?;", (hash, noteId))
        except:
            self.error("error adding note hash to the database")
        for keyword in keywords:
            self.fyi("  inserting keyword:", keyword)
            keywordId = self.con.execute("SELECT keywordId FROM keyword WHERE keyword = ?;", [keyword]).fetchone()
            if keywordId:
                self.fyi("  (existing keyword with id %s)" % keywordId)
                keywordId = keywordId[0]
            else:
                self.fyi("  (new keyword)")
                self.cur.execute("INSERT INTO keyword(keyword) VALUES (?);", [keyword])
                keywordId = self.cur.lastrowid
            self.con.execute("INSERT INTO notekeyword(noteId, keywordID) VALUES(?, ?)", [noteId, keywordId])
        # Handle attachments, which must be existing files.
        attachments = [key.lstrip().rstrip() for key in attachments.split(',')]
        attachments = [_f for _f in attachments if _f] # remove blanks
        for attachment in attachments:
            self.fyi("processing attachment '%s'" % attachment)
            if not os.path.isfile(attachment):
                self.warning(" cannot attach file '%s' because it does not exist" % attachment)
            else:
                self.fyi("    '%s' exists" % attachment)
                attachment = os.path.expanduser(attachment)
                afile = open(attachment, "rb")
                try:
                    blob = afile.read()
                    self.fyi("    read file '%s'" % attachment)
                    self.cur.execute('INSERT INTO attachment(filename,contents) VALUES(?,?)', [attachment,buffer(blob)])
                    attachmentId = self.cur.lastrowid
                    self.fyi("    inserted OK; attachmentID=%d" % attachmentId)
                    self.con.commit()
                    self.fyi("    added to attachment table")
                    self.fyi('    try "INSERT INTO note_attachment(noteId, attachmentId) VALUES(%d,%d)"' % (noteId,attachmentId))
                    self.cur.execute('INSERT INTO note_attachment(noteId, attachmentId) VALUES(?,?)', [noteId,attachmentId])
                    self.con.commit()
                    self.fyi("    ... OK")
                except:
                    self.error("Problem storing attachment named '%s'" % attachment)
                finally:
                    afile.close()
                self.fyi(" ... all done, writing attachment")
        self.con.commit()
        self.fyi("add() returning noteId=%d ... is all ok?" % noteId)
        return noteId


    def hash_abbreviation_length(self):
        hash = []
        #print("hash_abbreviation_length step 1")
        try:
            for h in self.cur.execute("SELECT hash FROM note;").fetchall():
                hash.extend(h)
        except:
            self.error("ERROR: cannot find hashes")
        #print("hash_abbreviation_length step 2")
        n = len(hash)
        #print("hash_abbreviation_length step 3; n=%d" % n)
        for nc in range(1, 20): # unlikely to be > 7
            #print("hash_abbreviation_length step 4; nc=%d" % nc)
            h = hash[:]
            for i in range(n):
                #print("h[%d] '%s'" % (i, hash[i]))
                h[i] = h[i][0:nc]
            #print("h %s" % h)
            hs = sorted(h)
            duplicate = False
            for i in range(n-1):
                if hs[i] == hs[i+1]:
                    duplicate = True
                    break
            if not duplicate:
                break
        return(nc)


    def keyword_hookup(self, noteId, keywords):
        '''
        Unhook existing cross-linking entries.
        '''
        try:
            self.cur.execute("DELETE FROM notekeyword WHERE noteid=?", [noteId])
        except:
            self.error("ERROR: cannot unhook previous keywords")
        # Now, hook up new the entries, one by one.
        for keyword in keywords:
            self.fyi(" inserting keyword:", keyword)
            # Make sure the keyword table contains the word in question.
            keywordId = self.con.execute("SELECT keywordId FROM keyword WHERE keyword = ?;", [keyword]).fetchone()
            try:
                if keywordId:
                    self.fyi("  (existing keyword with id: %s)" % keywordId)
                    keywordId = keywordId[0]
                else:
                    self.fyi("  (new keyword)")
                    self.cur.execute("INSERT INTO keyword(keyword) VALUES (?);", [keyword])
                    keywordId = self.cur.lastrowid
                # Finally, do the actual hookup for this word.
                self.con.execute("INSERT INTO notekeyword(noteId, keywordID) VALUES(?, ?)", [noteId, keywordId])
            except:
                self.error("error hooking up keyword '%s'" % keyword)
        self.con.commit()


    def list_keywords(self):
        ''' Return the list of keywords '''
        names = []
        try:
            for n in self.cur.execute("SELECT keyword FROM keyword;").fetchall():
                # Strip out leading and trailing whitespaces (can be artifacts of old data)
                k = n[0].strip()
                if len(k):
                    names.extend([k])
        except:
            self.error("ERROR: cannot find database table 'keyword'")
        names = list(set(names)) # remove duplicates
        names = sorted(names, key=lambda s: s.lower())
        return(names)


    def rename_keyword(self, old, new):
        existing = self.list_keywords()
        if old in existing:
            self.fyi("should rename keyword '%s' to '%s'" % (old, new))
            try:
                self.cur.execute("UPDATE book SET name=(?) WHERE name=(?);", (new, old))
                self.con.commit()
            except:
                self.error("Error changing keyword '%s' to '%s'" % (old, new))
        else:
            self.error("There is no keyword '%s'." % old)
        exit(0)


    def undelete(self, hash): # takes out of trash
        hash = str(hash)
        if not hash:
            self.error("must give the hash of the note that is to be undeleted")
        trash_contents = self.find_by_hash(hash, book=0)
        self.fyi("trash_contents : %s" % trash_contents)
        hashlen = len(hash)
        for t in trash_contents:
            if t['hash'][0:hashlen] == hash:
                self.fyi("undeleting note with hash %s" % t['hash'][0:7])
                try:
                    # put into book 1
                    self.cur.execute("UPDATE note SET book = 1 WHERE noteId = ?;", [t['noteId']])
                    self.con.commit()
                except:
                    self.error("error undeleting note with hash=%s" % t['hash'][0:7])


    def rehash(self):
        print("rehashing all notes")
        noteIds = []
        noteIds.extend(self.cur.execute("SELECT noteId,date,title,content,due,book,hash FROM note;"))
        for n in noteIds:
            print("%s" % n[2] + " " + n[1] + " " + str(n[0]))
            if not n[0]:
                print("Database malfunction: noteId is missing. Trying to fix with following SQL:")
                try:
                    print(" DELETE FROM note WHERE date='%s' AND title='%s';" % (n[1], n[2]))
                    self.cur.execute("DELETE FROM note WHERE date=? AND title=?;", (n[1], n[2]))
                    self.con.commit()
                except:
                    self.error("cannot delete the faulty note")
                print(" ... this worked; the database has been cleared of the faulty note")
                #try:
                #    self.cur.execute("INSERT INTO note(date,title,content,due,book) VALUES(?,?,?,?,?);",
                #            (n[1], n[2], n[3], n[4], n[5]))
                #    id = self.cur.lastrowid
                #    print(" id %d" % id)
                #    self.con.commit()
                #    id = self.cur.lastrowid
                #    print(" id %d" % id)
                #except:
                #    self.error("cannot insert a replacement for the faulty note")
                #print(" ... done?")
                #id = self.cur.lastrowid
                #print("id %d" % id)
                #n[0] = id # FIXME: fails
                #print(" ... ok, here goes")
            else:
                print("  old: %s" % n[6])
                hash = self.compute_hash(noteId=n[0], date=n[1], title=n[2])
                print("  new: %s" % hash)
                try:
                    self.cur.execute("UPDATE note SET hash=? WHERE noteId=?;", (hash, n[0]))
                except:
                    self.error("problem updating hash for noteId=%s" % n[0])
        self.con.commit()


    def delete(self, hash=""): # moves to trash
        hash = str(hash)
        if 0 == len(hash):
            exit(0)
        old = self.find_by_hash(hash)
        self.fyi("old: %s" % old)
        if not len(old):
            self.error("no active notes match abbreviated hash '%s'" % hash)
        if 1 != len(old):
            self.error("cannot delete %d notes at once; try adding more letters to the hash code" % len(old))
        id = int(old[0]["noteId"])
        self.fyi("in delete(), id=%s" % id)
        try:
            self.fyi("move note with noteId = %s to the trash." % id)
            self.cur.execute("UPDATE note SET book = 0 WHERE noteId = ?;", [id])
            self.con.commit()
        except:
            self.error("there is no note with hash %s" % hash)
            return False
        return True


    def empty_trash(self):
        self.fyi("about to empty the trash")
        try:
            noteIds = []
            noteIds.extend(self.con.execute("SELECT noteId from note WHERE book=0;"))
            for n in noteIds:
                self.fyi("  trashing note with noteId: %s" % n)
                self.con.execute("DELETE FROM note WHERE noteId=?", n)
                # keywords
                self.fyi("  trashing notekeyword with noteId: %s" % n)
                self.con.execute("DELETE FROM notekeyword WHERE noteId=?", n)
                # attachments
                attachmentIds = []
                attachmentIds.extend(self.con.execute("SELECT attachmentId from note_attachment WHERE noteId=?", n))
                if len(attachmentIds):
                    self.fyi("  trashing note_attachment with noteId: %s" % n)
                    self.con.execute("DELETE FROM note_attachment WHERE noteId=?", n)
                    for a in attachmentIds:
                        self.fyi("  trashing attachmentId: %s" % a)
                        self.con.execute("DELETE FROM attachment WHERE attachmentId=?", a)
                else:
                    self.fyi("  this note has no attachments")
            self.fyi("trashed %s notes" % len(noteIds))
            self.con.commit()
        except:
            self.error("problem encountered when emptying the trash")


    def edit(self, hash=""):
        '''
        Edit a note, given its abbreviated hash, which must be unique
        across both visible and trashed notes. (It is permitted to edit
        notes in the trash.)
        '''
        if not len(hash):
            exit(0)
        self.fyi("nota.edit() has hash: %s" % hash)
        ## do not use find_by_hash() because can be in hash or not.
        rows = self.cur.execute("SELECT noteId, hash FROM note;").fetchall()
        hash_len = len(hash)
        noteIds = []
        for r in rows:
            if r[1][0:hash_len] == hash:
                noteIds.append((r[0],))
        if not len(noteIds):
            self.error("no active notes match abbreviated hash '%s'" % hash)
        if 1 != len(noteIds):
            self.error("cannot edit %d notes at once; try adding more letters to the hash code" % len(noteIds))
        old = self.find_by_hash(hash)
        if 1 != len(old):
            self.error("cannot edit %d notes at once; try adding more letters to the hash code" % len(old))
        old = old[0]
        keywords = []
        keywords.extend(self.get_keywords(old['noteId']))
        ee = self.editor_entry(title=old['title'], keywords=keywords, content=old['content'],
                attachments='', book=old['book'], due=old['due'])
        noteId = int(old["noteId"])
        try:
            self.cur.execute("UPDATE note SET title = (?) WHERE noteId = ?;", (ee["title"], noteId))
        except:
            self.error("cannot do: UPDATE note SET title = (%s) WHERE noteId = %s;" % (ee["title"], noteId))
        try:
            self.cur.execute("UPDATE note SET content = (?) WHERE noteId = ?;", (ee["content"], noteId))
        except:
            self.error("cannot do: UPDATE note SET content = (%s) WHERE noteId = %s;" % (ee["content"], noteId))
        try:
            self.cur.execute("UPDATE note SET book = (?) WHERE noteId = ?;", (ee["book"], noteId))
        except:
            self.error("cannot do: UPDATE note SET book = (%s) WHERE noteId = %s;" % (ee["book"], noteId))
        self.keyword_hookup(noteId, ee["keywords"])
        if ee["due"] and ee["due"] != "None":
            try:
                due = self.interpret_time(ee["due"])[0]
                self.cur.execute("UPDATE note SET due=(?) WHERE noteId=?;", (due, noteId))
            except:
                self.error("cannot update the 'due' date")
        self.con.commit()
        return noteId


    def cleanup(self):
        ''' Clean up the database, e.g. removing unused keywords.'''
        allList = []
        allList.extend(self.cur.execute("SELECT keywordid FROM keyword;"))
        usedList = []
        usedList.extend(self.cur.execute("SELECT keywordid FROM notekeyword;"))
        unusedList = [val for val in allList if val not in usedList]
        for key in unusedList:
            if self.debug:
                print("About to delete keyword with ID %s" % key)
            try:
                self.cur.execute("DELETE FROM keyword WHERE keywordId = ?;", key)
            except:
                self.error("There was a problem deleting keyword %s" % key)
        self.con.commit()


    def get_id_list(self):
        '''Return list of ID values'''
        noteIds = []
        noteIds.extend(self.con.execute("SELECT noteId FROM note;"))
        return(noteIds)


    def trash_length(self):
        try:
            n = self.con.execute("SELECT count(noteId) FROM note WHERE book=0;").fetchone()
            return(n)
        except:
            self.error("cannot determine number of items in trash")

    def find_by_hash(self, hash=None, book=-1):
        '''Search notes for a given (possibly abbreviated) hash'''
        if hash:
            self.fyi("nota.find_by_hash() with abbreviated hash %s; book=%s" % (hash, book))
        try:
            if book < 0:
                rows = self.cur.execute("SELECT noteId, hash FROM note WHERE book > 0;").fetchall()
            else:
                rows = self.cur.execute("SELECT noteId, hash FROM note WHERE book=?;", [book]).fetchall()
        except:
            self.error("nota.find_by_hash() cannot look up note list")
        # Possibly save time by finding IDs first.
        noteIds = []
        if hash:
            l = len(hash)
            for r in rows:
                if hash == r[1][0:l]:
                    noteIds.append((r[0],))
        else:
            for r in rows:
                noteIds.append((r[0],))
        self.fyi("noteIds: %s" % noteIds)
        rval = []
        for n in noteIds:
            try:
                note = self.cur.execute("SELECT noteId, authorId, date, title, content, due, privacy, modified, hash, book FROM note WHERE noteId=?;", n).fetchone()
            except:
                self.warning("Problem extracting note %s from database" % n)
                next
            if note:
                date = note[2]
                due = note[5]
                privacy = note[6]
                keywordIds = []
                keywordIds.extend(self.con.execute("SELECT keywordid FROM notekeyword WHERE notekeyword.noteid=?;", n))
                keywords = []
                for k in keywordIds:
                    keywords.append(self.cur.execute("SELECT keyword FROM keyword WHERE keywordId=?;", k).fetchone()[0])
                rval.append({"noteId":note[0], "title":note[3], "keywords":keywords,
                    "content":note[4], "due":note[5], "privacy":note[6],
                    "date":note[2], "modified":note[7], "hash":note[8], "book":note[9]})
        return rval


    def find_by_keyword(self, keywords="", strict_match=False, book=-1):
        self.fyi("find_by_keyword, ... book=%s" % book)
        '''Search notes for a given keyword'''
        self.fyi("nota.find_by_keyword() with keywords %s; book=%s" % (keywords, book))
        keywordsKnown = []
        if not strict_match:
            keywords[0] = keywords[0].lower()
        for k in self.cur.execute("SELECT keyword FROM keyword;").fetchall():
            if strict_match:
                keywordsKnown.extend(k)
            else:
                keywordsKnown.extend(k)
                keywordsKnown.extend([str(k[0]).lower()])
        self.fyi("keywordsKnown: %s" % keywordsKnown)
        # FIXME: only using first keyword here!
        if not strict_match:
            keywords_partial = []
            kl = len(keywords[0])
            if kl > 3:
                for K in keywordsKnown:
                    if K[0:kl] == keywords[0]:
                        if K not in keywords_partial:
                            keywords_partial.append(K)
            # Try fuzzy search only if no direct matches
            keywords_fuzzy = []
            if not len(keywords_partial):
                keywords_fuzzy = difflib.get_close_matches(keywords[0], keywordsKnown, n=1, cutoff=0.6)
            self.fyi("  keywords_partial %s" % keywords_partial)
            self.fyi("  keywords_fuzzy %s" % keywords_fuzzy)
            keywords = list(set(keywords_partial + keywords_fuzzy))
        self.fyi("nota.find_by_keyword() later, keywords: %s" % keywords)
        noteIds = []
        for keyword in keywords:
            self.fyi("keyword: %s" % keyword)
            if strict_match:
                self.fyi("strict match on keyword '%s'" % keyword)
                try:
                    keywordId = self.con.execute("SELECT keywordId FROM keyword WHERE keyword=?;",
                            [keyword]).fetchone()
                except:
                    self.error("cannot look up keyword '%s'" % [keyword])
            else:
                self.fyi("non-strict match on keyword '%s'" % keyword)
                try:
                    keywordId = []
                    for k in self.cur.execute("SELECT keywordId FROM keyword WHERE keyword=? COLLATE NOCASE;", [keyword]).fetchall():
                        keywordId.extend(k)
                except:
                    self.error("cannot look up keyword '%s'" % [keyword])
            try:
                if len(keywordId):
                    self.fyi("looking for noteID matches to keywordId %s" % keywordId)
                    for k in keywordId:
                        self.fyi("k: %s" % k)
                        try:
                            if strict_match:
                                noteIdtest = self.cur.execute("SELECT noteId FROM notekeyword WHERE keywordId=?;", [k])
                            else:
                                noteIdtest = self.cur.execute("SELECT noteId FROM notekeyword WHERE keywordId=? COLLATE NOCASE;", [k])
                        except:
                            self.error("cannot query database to find noteId corresponding to keywordId value %s" % [k])
                        for noteId in noteIdtest:
                            self.fyi("got match to noteID %s" % noteId)
                            if noteId not in noteIds:
                                noteIds.append(noteId)
                                self.fyi("adding to list")
                            else:
                                self.fyi("already in list")
                        self.fyi("done with keyword %s" % k)
                else:
                    pass
            except:
                #20150314 self.error("problem finding keyword or note in database")
                #20150314 shouldn't be an error to not find a note!
                pass
        ## convert from hash to ids. Note that one hash may create several ids.
        self.fyi("noteIds: %s" % noteIds)
        ## Find IDs of just the notes with the proper book value
        noteIds2 = []
        self.fyi("ORIGINAL noteIds: %s" % noteIds)
        for n in noteIds:
            self.fyi("n=%s" % n)
            try:
                row = self.cur.execute("SELECT noteId, book FROM note WHERE noteID=?;", n).fetchone()
            except:
                self.error("cannot look up noteId %s" % n)
            self.fyi("row %s; book=%s" % (row, book))
            if book < 0 or row[1] == book:
                self.fyi("appending id %s" % row[0])
                noteIds2.append((row[0],))
            else:
                self.fyi("skipping id %s because book is wrong" % row[0])
        noteIds = noteIds2
        #self.fyi("  LATER    noteIds2: %s" % noteIds2)
        #self.fyi("  LATER    noteIds: %s" % noteIds)
        rval = []
        for n in noteIds:
            #self.fyi(" processing id=%s" % n)
            try:
                note = self.cur.execute("SELECT noteId, authorId, date, title, content, due, privacy, modified, hash, book FROM note WHERE noteId=?;", n).fetchone()
            except:
                self.warning("Problem extracting note %s from database" % n)
                next
            if note:
                date = note[2]
                due = note[5]
                privacy = note[6]
                keywordIds = []
                keywordIds.extend(self.con.execute("SELECT keywordid FROM notekeyword WHERE notekeyword.noteid=?;", n))
                keywords = []
                for k in keywordIds:
                    keywords.append(self.cur.execute("SELECT keyword FROM keyword WHERE keywordId=?;", k).fetchone()[0])
                rval.append({"noteId":note[0], "title":note[3], "keywords":keywords,
                    "content":note[4], "due":note[5], "privacy":note[6],
                    "date":note[2], "modified":note[7], "hash":note[8], "book":note[9]})
        return rval


    def find_recent(self, nrecent=4):
        '''Find recent non-trashed notes'''
        try:
            rows = self.cur.execute("SELECT noteId FROM note WHERE book > 0 ORDER BY date DESC LIMIT %d;"%nrecent).fetchall()
        except:
            self.error("nota.find_recent() cannot look up note list")
        # Possibly save time by finding IDs first.
        noteIds = []
        for r in rows:
            noteIds.append(r[0],)
        self.fyi("noteIds: %s" % noteIds)
        rval = []
        for n in noteIds:
            note = None
            try:
                note = self.cur.execute("SELECT noteId, date, title, content, hash, book FROM note WHERE noteId = ?;", [n]).fetchone()
            except:
                self.warning("Problem extracting note %s from database for recent-list" % n)
                next
            if note:
                keywordIds = []
                keywordIds.extend(self.con.execute("SELECT keywordid FROM notekeyword WHERE notekeyword.noteid=?;", [n]))
                keywords = []
                for k in keywordIds:
                    keywords.append(self.cur.execute("SELECT keyword FROM keyword WHERE keywordId=?;", k).fetchone()[0])
                rval.append({"noteId":note[0], "date":note[1], "title":note[2], "keywords":keywords,
                    "content":note[3], "hash":note[4], "book":note[5]})
        return rval


    def get_keywords(self, id):
        if id < 0:
            self.error("Cannot have a negative note ID")
            return None
        keywordIds = []
        keywordIds.extend(self.con.execute("SELECT keywordid FROM notekeyword WHERE notekeyword.noteid = ?;", [id]))
        keywords = []
        for k in keywordIds:
            keywords.append(self.cur.execute("SELECT keyword FROM keyword WHERE keywordId = ?;", k).fetchone()[0])
        return keywords

    def get_attachment_list(self, noteId):
        if noteId < 0:
            self.error("Cannot have a negative note ID")
            return None
        #print("get_attachments id=%d" % noteId)
        attachmentIds = []
        attachmentIds.extend(self.con.execute("SELECT attachmentid FROM note_attachment WHERE note_attachment.noteid = ?;", [noteId]))
        attachmentIds = []
        attachmentIds.extend(self.con.execute("SELECT attachmentid FROM note_attachment WHERE note_attachment.noteid = ?;", [noteId]))
        return attachmentIds

    def get_attachment_filename(self, attachmentId):
        filename = []
        filename.extend(self.con.execute("SELECT filename FROM attachment WHERE attachmentId = ?;", [attachmentId]))
        return filename

    def get_attachment_contents(self, attachmentId):
        contents = self.con.execute("SELECT contents FROM attachment WHERE attachmentId=?;",
                [attachmentId]).fetchone()
        return contents

    def interpret_time(self, due):
        # catch "tomorrow" and "Nhours", "Ndays", "Nweeks" (with N an integer)
        now = datetime.datetime.now()
        sperday = 86400
        if due == "today":
            due = (now + datetime.timedelta(hours=8), sperday/24)
        elif due == "tomorrow":
            due = (now + datetime.timedelta(days=1), sperday)
        else:
            ## try hours, then days, then weeks.
            test = re.compile(r'(\d+)([ ]*hour)(s*)').match(due)
            if test:
                due = (now + datetime.timedelta(hours=int(test.group(1))), sperday/24)
            else:
                test = re.compile(r'(\d+)([ ]*day)(s*)').match(due)
                if test:
                    due = (now + datetime.timedelta(days=int(test.group(1))), sperday/1)
                else:
                    test = re.compile(r'(\d+)([ ]*week)(s*)').match(due)
                    if test:
                        due = (now + datetime.timedelta(weeks=int(test.group(1))), sperday*7)
                    else:
                        test = re.compile(r'(\d+)([ ]*month)(s*)').match(due)
                        if test:
                            due = (now + datetime.timedelta(weeks=4*int(test.group(1))), sperday*7)
                        else:
                            due = (None, None)
        self.fyi("due '%s'; tolerance '%s'" % (due[0], due[1]))
        return due


    def editor_entry(self, title, content, keywords, attachments, book=1, privacy=0, due=""):
        remaining = None
        books = self.list_books()
        nbooks = len(books)
        if due:
            now = datetime.datetime.now()
            try:
                DUE = datetime.datetime.strptime(due, "%Y-%m-%d %H:%M:%S.%f")
            except:
                DUE = now
            remaining = (DUE - now).total_seconds()
            if (abs(remaining) < 86400):
                remaining = "%d hours" % round(remaining / 3600)
            else:
                remaining = "%d days" % round(remaining / 86400)
            due = remaining
        booklist = ""
        for i in range(1, nbooks):
            booklist = booklist + str(i) + " (" + books[i] + ") "
        if book < 0:
            book = 1
        initial_message = '''Instructions: fill in material following the ">" symbol.  (Items following
the "?>" symbol are optional.  The title and keywords must each fit on one
line. Use commas to separate keywords.  The content must start *below*
the line with the dots.

TITLE > %s

KEYWORDS (optional) > %s

ATTACHMENTS (optional) > %s

BOOK (integer, one of: %s) > %s

DUE (E.G. 'tomorrow' or '3 days')?> %s

CONTENT...
%s
''' % (title, ",".join(k for k in keywords), ",".join(a for a in attachments), booklist, book, due, content)
        #print(initial_message)
        #exit(0)
        try:
            # FIXME: is this polluting filespace with tmp files?
            file = tempfile.NamedTemporaryFile(suffix=".tmp") #, delete=False)
        except:
            self.error('cannot create tempfile')
        file.write(initial_message.encode('utf-8'))
        file.flush()
        EDITOR = os.environ.get('EDITOR','vi')
        try:
            call([EDITOR, file.name])
        except:
            try:
                os.system(EDITOR + ' ' + file.name)
            except:
                self.error("cannot spawn an editor")
        lines = open(file.name).readlines()
        inContent = False
        content = ""
        for line in lines:
            line = line.rstrip('\n')
            if inContent:
                content = content + line + '\n'
            elif "TITLE" in line:
                title = re.sub(r'.*>', '', line).strip()
            elif "DUE" in line:
                due = re.sub(r'.*>', '', line).strip()
            elif "PRIVACY" in line:
                PRIVACY = re.sub(r'.*>', '', line).strip()
            elif "KEYWORDS" in line:
                keywords = re.sub(r'.*>', '', line).strip()
            elif "ATTACHMENTS" in line:
                attachments = re.sub(r'.*>', '', line).strip()
            elif "BOOK" in line:
                book = int(re.sub(r'.*>', '', line).strip())
                if book < 1:
                    self.error("book cannot be < 1")
                if book > nbooks - 1:
                    self.error("book cannot be > %s" % nbooks)
            elif "CONTENT" in line:
                inContent = True
        content = content.rstrip('\n')
        keywords = [key.lstrip().rstrip() for key in keywords.split(',')]
        if not title and not content and (len(keywords) == 1 and not keywords[0]):
            self.error("empty note, not stored. Please add title, keywords, or content.")
        self.fyi("LATE keywords= %s" % keywords)
        return {"title":title, "keywords":keywords, "content":content, "attachments":attachments,
                "privacy":privacy, "book":book, "due":due}


    def rename_keyword(self, old, new):
        # FIXME: hook this up to args
        self.fyi("UPDATE keyword SET keyword=\"%s\" WHERE keyword=\"%s\";" % (new, old))
        try:
            self.cur.execute("UPDATE keyword SET keyword = ? WHERE keyword = ?;", (new, old))
        except:
            self.error("cannot change keyword from '%s' to '%s'" % (old, new))
        try:
            self.con.commit()
        except:
            self.error("cannot commit the database after changing keyword from '%s' to '%s'" % (old, new))


    def age(self, d):
        d = datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
        diff = datetime.datetime.now() - d
        s = diff.seconds
        if diff.days < 0:
            return d.strftime('%b %d, %Y')
        elif diff.days > 200:
            return d.strftime('%b %d, %Y')
        elif diff.days > 7*4:
            return '{} months ago'.format(trunc(0.5+diff.days/28))
        elif diff.days > 7*2:
            return '{} weeks ago'.format(trunc(0.5+diff.days/7))
        elif diff.days > 1 and diff.days < 14:
            return '{} days ago'.format(trunc(diff.days))
        elif s <= 1:
            return 'just now'
        elif s < 60:
            return '{} seconds ago'.format(trunc(s))
        elif s < 120:
            return 'about a minute ago'
        elif s < 3600:
            return '{} minutes ago'.format(trunc(s/60))
        elif s < 7200:
            return 'about an hour ago'
        else:
            return '{} hours ago'.format(trunc(s/3600))
