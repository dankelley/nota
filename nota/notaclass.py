#!/usr/bin/python
from __future__ import print_function
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

class Nota:
    def __init__(self, db="nota.db", authorId=1, debug=0, quiet=False):
        '''

        A class used for the storing and searching of textual notes in a
        sqlite3 database.  Keywords may be attached to notes, providing a
        convenient way to search later.

        '''
        self.debug = debug 
        self.quiet = quiet
        self.fyi("Working with database named '%s' (before path expansion)." % db)
        db = os.path.expanduser(db)
        self.fyi("Working with database named '%s' (after path expansion)." % db)
        mustInitialize = not os.path.exists(db)
        if mustInitialize:
            print("Creating new database named \"%s\"." % db)
        else:
            try:
                dbsize = os.path.getsize(db)
                self.fyi("Database file size %s bytes." % dbsize)
                mustInitialize = not dbsize
            except:
                pass
        try:
            con = sqlite.connect(db)
            con.text_factory = str # permits accented characters in notes
        except:
            self.error("Error opening connection to database named '%s'" % db)
        self.con = con
        self.cur = con.cursor()
        self.authorId = authorId
        ## 0.3: add note.modified column
        self.appversion = [0, 6, 0] # db changes on first two only
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
                        h = hashlib.sha256((str(row[0])+row[1]+row[2]).encode('utf8')).hexdigest()
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
        return("Nota %d.%d.%d" % (self.appversion[0], self.appversion[1], self.appversion[2]))


    def initialize(self, author=""):
        ''' Initialize the database.  This is dangerous since it removes any
        existing content.'''
        self.cur.execute("CREATE TABLE version(major, minor);")
        self.cur.execute("INSERT INTO version(major, minor) VALUES (?,?);",
                (self.appversion[0], self.appversion[1]))
        self.cur.execute("CREATE TABLE note(noteId integer primary key autoincrement, authorId, date, modified, due, title, content, hash, privacy DEFAULT 0, in_trash DEFAULT 0);")
        self.cur.execute("CREATE TABLE author(authorId integer primary key autoincrement, name, nickname);")
        self.cur.execute("CREATE TABLE alias(aliasId integer primary key autoincrement, item, alias);")
        self.cur.execute("CREATE TABLE keyword(keywordId integer primary key autoincrement, keyword);")
        self.cur.execute("CREATE TABLE notekeyword(notekeywordId integer primary key autoincrement, noteid, keywordid);")
        self.con.commit()


    def add(self, title="", keywords="", content="", due="", privacy=0, date="", modified=""):
        ''' Add a note to the database.  The title should be short (perhaps 3
        to 7 words).  The keywords are comma-separated, and should be similar
        in style to others in the database.  The content may be of any length.'''
        self.fyi("add with title='%s'" % title)
        self.fyi("add with keywords='%s'" % keywords)
        self.fyi("add with due='%s'" % due)
        if not isinstance(due, str):
            due = ""
        due = self.interpret_time(due)[0]
        self.fyi("due: %s" % due)
        now = datetime.datetime.now()
        if date == "":
            date = now.strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.cur.execute("INSERT INTO note(authorId, date, modified, title, content, privacy, due) VALUES(?, ?, ?, ?, ?, ?, ?);",
                (self.authorId, date, modified, title, content, 0, due))
        except:
            self.error("error adding note to the database")
        noteId = self.cur.lastrowid
        self.fyi("noteId: %s" % noteId)
        hash = hashlib.sha256((str(noteId)+date+title).encode('utf8')).hexdigest()
        self.fyi("hash: %s" % hash)
        try:
            self.cur.execute("UPDATE note SET hash=? WHERE noteId=?;", (hash, noteId))
        except:
            self.error("error adding note hash to the database")
        for keyword in keywords:
            self.fyi(" inserting keyword:", keyword)
            keywordId = self.con.execute("SELECT keywordId FROM keyword WHERE keyword = ?;", [keyword]).fetchone()
            if keywordId:
                self.fyi("(existing keyword with id %s)" % keywordId)
                keywordId = keywordId[0]
            else:
                self.fyi("(new keyword)")
                self.cur.execute("INSERT INTO keyword(keyword) VALUES (?);", [keyword])
                keywordId = self.cur.lastrowid
            self.con.execute("INSERT INTO notekeyword(noteId, keywordID) VALUES(?, ?)", [noteId, keywordId])
        self.con.commit()
        return noteId


    def hash_abbreviation_length(self):
        hash = []
        try:
            for h in self.cur.execute("SELECT hash FROM note;").fetchall():
                hash.extend(h)
        except:
            self.error("ERROR: cannot find hashes")
        n = len(hash)
        for nc in range(1, 20): # unlikely to be > 7
            h = hash[:]
            for i in range(n):
                h[i] = h[i][0:nc]
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
            keyword = keyword.decode('utf-8')
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


    def undelete(self, hash): # takes out of trash
        hash = str(hash)
        if not hash:
            self.error("must give the hash of the note that is to be undeleted")
        trash_contents = self.find_by_hash(hash, in_trash=True)
        self.fyi("trash_contents : %s" % trash_contents)
        hashlen = len(hash)
        for t in trash_contents:
            if t['hash'][0:hashlen] == hash:
                print("undeleting note with hash %s" % t['hash'][0:7])
                try:
                    self.cur.execute("UPDATE note SET in_trash = 0 WHERE noteId = ?;", [t['noteId']])
                    self.con.commit()
                except:
                    self.error("error undeleting note with hash=%s" % t['hash'][0:7])


    def rehash(self):
        print("in rehash")
        noteIds = []
        noteIds.extend(self.cur.execute("SELECT noteId,date,title,hash FROM note;"))
        for n in noteIds:
            # print("noteID:   %s" % n[0])
            # print("time:     %s" % n[1])
            # print("title:    %s" % n[2])
            print("%s" % n[2]+" "+n[1]+" "+str(n[0]))
            print("  old: %s" % n[3])
            hash = hashlib.sha256((n[2]+" "+n[1]+" "+str(n[0])).encode('utf8')).hexdigest()
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
            self.cur.execute("UPDATE note SET in_trash = 1 WHERE noteId = ?;", [id])
            self.con.commit()
        except:
            self.error("there is no note with unique hash %s" % hash)
            return False
        self.con.commit()
        return True


    def emptytrash(self):
        self.fyi("about to empty the trash")
        try:
            noteIds = []
            noteIds.extend(self.con.execute("SELECT noteId from note WHERE in_trash=1;"))
            for n in noteIds:
                self.fyi("  trashing note with noteId: %s" % n)
                self.con.execute("DELETE FROM note where noteId=?", n)
                self.fyi("  trashing notekeyword with noteId: %s" % n)
                self.con.execute("DELETE FROM notekeyword where noteid=?", n)
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
        #ee = self.editor_entry(title=old['title'], keywords=keywords, content=old['content'], privacy=old['privacy'], due=old['due'])
        ee = self.editor_entry(title=old['title'], keywords=keywords, content=old['content'], due=old['due'])
        noteId = int(old["noteId"])
        try:
            self.cur.execute("UPDATE note SET title = (?) WHERE noteId = ?;", (ee["title"], noteId))
        except:
            self.error("cannot do: UPDATE note SET title = (%s) WHERE noteId = %s;" % (ee["title"], noteId))
        try:
            self.cur.execute("UPDATE note SET content = (?) WHERE noteId = ?;", (ee["content"], noteId))
        except:
            self.error("cannot do: UPDATE note SET content = (%s) WHERE noteId = %s;" % (ee["content"], noteId))
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
            n = self.con.execute("SELECT count(noteId) FROM note WHERE in_trash=1;").fetchone()
            return(n)
        except:
            self.error("cannot determine number of items in trash")

    def find_by_hash(self, hash=None, in_trash=False):
        '''Search notes for a given (possibly abbreviated) hash'''
        in_trash = int(in_trash)
        if hash:
            self.fyi("nota.find_by_hash() with abbreviated hash %s; in_trash=%s" % (hash, in_trash))
        try:
            rows = self.cur.execute("SELECT noteId, hash FROM note WHERE in_trash=?;", [in_trash]).fetchall()
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
            # No need to check for being in trash or not, of course.
            self.fyi(" processing id=%s" % n)
            #print(" (%s) " % n, end="")
            try:
                note = self.cur.execute("SELECT noteId, authorId, date, title, content, due, privacy, modified, hash FROM note WHERE noteId=?;", n).fetchone()
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
                    "date":note[2], "modified":note[7], "hash":note[8]})
        return rval


    def find_by_keyword(self, keywords="", strict_match=False, in_trash=False):
        '''Search notes for a given keyword'''
        in_trash = int(in_trash)
        self.fyi("nota.find_by_keyword() with keywords %s; in_trash=%s" % (keywords, in_trash))
        keywordsKnown = []
        for k in self.cur.execute("SELECT keyword FROM keyword;").fetchall():
            keywordsKnown.extend(k)
        # FIXME: only using first keyword here!
        if not strict_match:
            keywords_partial = []
            kl = len(keywords[0])
            for K in keywordsKnown:
                if K[0:kl] == keywords[0]:
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
            try:
                keywordId = self.con.execute("SELECT keywordId FROM keyword WHERE keyword=?;", [keyword]).fetchone()
                if keywordId:
                    for noteId in self.cur.execute("SELECT noteId FROM notekeyword WHERE keywordId=?;", keywordId):
                        if noteId not in noteIds:
                            noteIds.append(noteId)
            except:
                self.error("problem finding keyword or note in database")
                pass
        ## convert from hash to ids. Note that one hash may create several ids.
        self.fyi("noteIds: %s" % noteIds)
        ## Find IDs of just the notes with the proper in_trash value
        noteIds2 = []
        self.fyi("ORIGINAL noteIds: %s" % noteIds)
        for n in noteIds:
            self.fyi("n=%s" % n)
            try:
                row = self.cur.execute("SELECT noteId, in_trash FROM note WHERE noteID=?;", n).fetchone()
            except:
                self.error("cannot look up noteId %s" % n)
            self.fyi("row %s; in_trash=%s" % (row, in_trash))
            if row[1] == in_trash:
                self.fyi("appending id %s" % row[0])
                noteIds2.append((row[0],))
            else:
                self.fyi("skipping id %s because in_trash is wrong" % row[0])
        noteIds = noteIds2
        self.fyi("  LATER    noteIds2: %s" % noteIds2)
        self.fyi("  LATER    noteIds: %s" % noteIds)
        rval = []
        for n in noteIds:
            self.fyi(" processing id=%s" % n)
            try:
                note = self.cur.execute("SELECT noteId, authorId, date, title, content, due, privacy, modified, hash FROM note WHERE noteId=?;", n).fetchone()
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
                    "date":note[2], "modified":note[7], "hash":note[8]})
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


    def editor_entry(self, title, keywords, content, privacy=0, due=""):
        remaining = None
        if due:
            now = datetime.datetime.now()
            #print("due: %s" % due)
            #print(due)
            try:
                DUE = datetime.datetime.strptime(due, "%Y-%m-%d %H:%M:%S.%f")
            except:
                DUE = now
            remaining = (DUE - now).total_seconds()
            #print("remaining: %s" % remaining)
            if (abs(remaining) < 86400):
                remaining = "%d hours" % round(remaining / 3600)
            else:
                remaining = "%d days" % round(remaining / 86400)
            #print("remaining: %s" % remaining)
            due = remaining
        initial_message = '''Instructions: fill in material following the ">" symbol.  (Items following
the "?>" symbol are optional.  The title and keywords must each fit on one
line. Use commas to separate keywords.  The content must start *below*
the line with the dots.

TITLE> %s

KEYWORDS?> %s

DUE (E.G. 'tomorrow' or '3 days')?> %s

CONTENT...
%s
''' % (title, ",".join(k for k in keywords), due, content)
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
            elif "CONTENT" in line:
                inContent = True
        if not title:
            self.error("no title given, so no note stored.")
        content = content.rstrip('\n')
        keywords = [key.lstrip().rstrip() for key in keywords.split(',')]
        self.fyi("LATE keywords= %s" % keywords)
        return {"title":title, "keywords":keywords, "content":content, "privacy":privacy, "due":due}


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

