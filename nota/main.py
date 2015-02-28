#!/usr/bin/python
from __future__ import print_function
from .notaclass import Nota
import argparse
import sys
import json
import os
import re
import textwrap
import datetime
from random import randint, seed
from time import strptime
import subprocess

def nota():
    hints = [
            'add a note: "nota -a" (opens an editor)', 
            'list all notes: "nota"',
            # 'read notes from a JSON file: "nota -a -m json < notes.json"',
            # 'store notes into a JSON file: "nota -m json > notes.json"',
            'export notes with hash \'ab...\': "nota --export ab" (output handled by \'--import\')',
            'export all notes: "nota --export -" (output handled by \'--import\')',
            'import notes in file \'file.json\': "nota --import file.json" (file made by \'--export\')',
            'list notes in markdown format: "nota -m markdown"',
            #'list notes in json format: "nota -m json"',
            'edit note with hash \'ab...\': "nota -e ab" (opens an editor)',
            'delete note with hash \'ab...\': "nota -d ab"',
            'list notes with keyword \'foo\': "nota -k foo"',
            'list note with hash \'ab...\': "nota ab"',
            'list notes in the trash: "nota --trash"',
            'untrash notes with hash \'ab...\': "nota --undelete ab"',
            'recreate note hashes: "nota --rehash" (a RARE need)']
    
    def random_hint():
        return hints[randint(0, len(hints)-1)]
    
    def get_from_dotfile(file, token, default=""):
        try:
            with open(os.path.expanduser(file), "r") as f:
                for line in f.readlines():
                    line = re.sub(r'#.*', r'', line)
                    tokens = line.split("=")
                    if 2 == len(tokens):
                        tokens = line.split("=")
                        tokens[0] = tokens[0].strip()
                        tokens[1] = tokens[1].strip()
                        tokens[1] = tokens[1].strip('"')
                        if tokens[0] == token:
                            if tokens[1] == "True":
                                return True
                            elif tokens[1] == "False":
                                return False
                            else:
                                return(tokens[1])
                return(default)
        except:
            return(default)
    
    
    # If second arg is a number, it is a noteId
    id_desired = None
    if len(sys.argv) > 1:
        try:
            id_desired = sys.argv[1]
            #del sys.argv[1]
        except:
            pass
    
    show_id = get_from_dotfile("~/.notarc", "show_id", False)
    debug = get_from_dotfile("~/.notarc", "debug", None)
    
   
    parser = argparse.ArgumentParser(prog="nota", description="Nota: an organizer for textual notes",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=textwrap.dedent('''\
    There are several ways to use nota.  Try 'nota -h' for some hints.  The most common uses are
    
        nota         # list notes, with first column being hash code
        nota -k key  # list notes with indicated keyword
        nota ab      # list notes with hash starting 'ab' (in detail, if only one note)
        nota -a      # add a note (opens a text editor)
        nota -e ab   # edit note with hash starting with 'ab' (opens a text editor)
        nota -d ab   # delete note with hash starting with 'ab'
    
    The ~/.notarc file may be used for customization, and may contain e.g. the
    following:
    
        db = \"~/Dropbox/nota.db\" # this permits the use of different files
        pretty = \"oneline\" # no other option
        show_id = False      # (only for developer) show database key in listings
        debug = False        # set True (or use --debug flag) to turn on debugging
        color = True         # set False to avoid colors (optionally customized as below)
                             # Colours (as below) are specified with just the suffix part,
                             # e.g. "36m" stands for "\\033[36m". 
                             #
                             # It is also possible to specify a color scheme, with the 
                             # choices being as follows (SUBJECT TO CHANGE!)
                             #   color = "bubblegum" # red hash, cyan keywords
                             #   color = "forest" # green hash, straw keywords
                             #   color = "bun" # blue hash, underlined keywords
                             #   color = "gun" # green hash, underlined keywords
                             #   color = "run" # red hash, underlined keywords
                             #   color = "default" # same as "bubblegum"
                             # (see http://en.wikipedia.org/wiki/ANSI_escape_code)
        color.hash = "36m"   # darkcyan
        color.title = "1m"   # bold
        color.keyword = "4m" # underline
        '''))
    
    parser.add_argument("hash", nargs="?", default="", help="abbreviated hash to search for", metavar="hash")
    parser.add_argument("-a", "--add", action="store_true", dest="add", default=False, help="add a note")
    parser.add_argument("-e", "--edit", type=str, default=None, help="edit note with abbreviated hash 'h'", metavar="h")
    parser.add_argument("-d", "--delete", type=str, default=None, help="move note abbreviated hash 'h' to trash", metavar="h")
    parser.add_argument("--color", type=str, default=None, help="specify named scheme or True/False", metavar="c")
    parser.add_argument("--undelete", type=str, default=None, help="remove note abbreviated hash 'h' from trash", metavar="h")
    parser.add_argument("--emptytrash", action="store_true", dest="emptytrash", default=False, help="empty the trash, permanently deleting notes therein")
    #parser.add_argument("-i", "--id", type=int, help="ID number of note to work with (MAY BE REMOVED)")
    parser.add_argument("-H", "--Hints", action="store_true", dest="hints", default=False, help="get hints")
    parser.add_argument("-m", "--mode", type=str, default="interactive", choices=['interactive', 'plain', 'markdown'],
            metavar="m", help="i/o mode: 'interactive', 'plain', or 'markdown'")
    parser.add_argument("-t", "--title", type=str, default="", help="a short title", metavar="t")
    parser.add_argument("-k", "--keywords", type=str, default="", help="string containing comma-separated keywords", metavar="k")
    parser.add_argument("-c", "--content", type=str, default="", help="string to be used for content", metavar="c")
    parser.add_argument("--count", action="store_true", dest="count", default=False, help="report only count of found results")
    parser.add_argument("--debug", action="store_true", dest="debug", default=False, help="set debugging on")
    parser.add_argument("--export", type=str, default=None, help="export notes matching hash (use has '-' for all notes)", metavar="hash")
    parser.add_argument("--import", type=str, default=None, dest="do_import", help="import notes from file created by --export", metavar="file")
    parser.add_argument("--privacy", type=int, default=0, help="set privacy level (0=open, 1=closed)", metavar="level")
    parser.add_argument("--file", type=str, help="filename for i/o", metavar="name")
    # Process the dotfile (need for next parser call)
    defaultDatabase = get_from_dotfile("~/.notarc", "database", "~/Dropbox/nota.db")
    # Back to the parser
    parser.add_argument("--rehash", action="store_true", dest="rehash", default=False, help="create new hashes")
    parser.add_argument("--trash", action="store_true", dest="trash", default=False, help="show contents of trash")
    parser.add_argument("--database", type=str, default=defaultDatabase, help="filename for database", metavar="db")
    parser.add_argument("--strict", action="store_true", default=False, help="use strict search?")
    parser.add_argument("--due", type=str, default="", help="time when item is due", metavar="when")
    parser.add_argument("-p", "--pretty", type=str, default="", metavar="fmt", help="format for note output")
    parser.add_argument("-v", "--version", action="store_true", dest="version", default=False, help="get version number")
    parser.add_argument("--developer", action="store_true", default=False, help="flag for the developer *only*")
    args = parser.parse_args()
    
    args.keywordsoriginal = args.keywords
    args.keywords = [key.lstrip().rstrip() for key in args.keywords.split(',')]

    # Handle color scheme
    class color:
        hash = '\033[33m'   # yellow [git hash color]
        title = '\033[1m'   # bold
        keyword = '\033[4m' # darkcyan [git '@@' color]
        normal = '\033[0m' # black
    if args.color:
        if args.color == "True":
            color_scheme = True
        elif args.color == "False":
            color_scheme = False
        else:
            color_scheme = args.color
    else:
        color_scheme = get_from_dotfile("~/.notarc", "color", True)
    use_color = True
    if isinstance(color_scheme, str):
        if color_scheme == "forest": # green-straw
            color.hash = '\033[' + '32m' # green
            color.title = '\033[' + '1m' # bold
            #color.keyword = '\033[' + '4m' # underline
            color.keyword = '\033[' + '33m' # yellow (like commit hash from git)
        elif color_scheme == "gun": # green-underline
            color.hash = '\033[' + '32m' # green
            color.title = '\033[' + '1m' # bold
            color.keyword = '\033[' + '4m' # underline
        elif color_scheme == "bun": # blue-underline
            color.hash = '\033[' + '34m' # blue
            color.title = '\033[' + '1m' # bold
            color.keyword = '\033[' + '4m' # underline
        elif color_scheme == "run": # red-underline
            color.hash = '\033[' + '31m' # red 
            color.title = '\033[' + '1m' # bold
            color.keyword = '\033[' + '4m' # underline
        elif color_scheme == "bubblegum":
            color.hash = '\033[' + '31m' # red
            color.title = '\033[' + '1m' # bold
            color.keyword = '\033[' + '35m'
        elif color_scheme == "default":
            color.hash = '\033[' + '31m' # red
            color.title = '\033[' + '1m' # bold
            color.keyword = '\033[' + '35m'
        else:
            print("Unknown color scheme '%s'; using 'default' instead." % color_scheme)
            color.hash = '\033[' + '31m' # red
            color.title = '\033[' + '1m' # bold
            color.keyword = '\033[' + '35m'
        use_color = True
    elif isinstance(color_scheme, bool):
        use_color = color_scheme
        if use_color:
            color.hash = '\033[' + get_from_dotfile("~/.notarc", "color.hash", '31m')
            color.title = '\033[' + get_from_dotfile("~/.notarc", "color.title", '1m')
            color.keyword = '\033[' + get_from_dotfile("~/.notarc", "color.keyword", '35m')
    else:
        print("The color scheme given in the ~/.notarc file should be a string or logical")
        exit(1)
    
    if not use_color:
        color.hash = ''
        color.title = ''
        color.keyword = ''
        color.normal = ""
 
    
    if not args.debug:
        args.debug = debug
    if not args.database:
        args.database = defaultDatabase
    
    nota = Nota(debug=args.debug, db=args.database, quiet=args.count)
    
    if args.version:
        print(nota.version())
        sys.exit(0)
    
    if args.hints:
        for hint in hints:
            if use_color:
                print(hint.replace(' "',' \'\033[1m').replace('"', '\033[0m\''))
            else:
                print(hint)
        sys.exit(0)
    
    # look in ~/.notarc to see if a database is named there
    if not args.pretty:
        args.pretty = get_from_dotfile("~/.notarc", "pretty", "oneline")
    
    if args.developer:
        nota.warning("--developer does nothing at the present time")
    
    if args.file:
        file = args.file
    else:
        file = "stdout"
    
    if args.title:
        title = args.title
    else:
        title = ""
    if args.content:
        content = args.content
    else:
        content = ""
    
    if args.delete:
        nota.fyi("should now delete note %s" % args.delete)
        nota.delete(args.delete)
        sys.exit(0)
    
    if args.undelete:
        nota.fyi("should now undelete note with hash %s" % args.undelete)
        nota.undelete(args.undelete)
        sys.exit(0)
    
    if args.emptytrash:
        nota.fyi("should now empty the trash")
        nota.emptytrash()
        sys.exit(0)
    
    if args.edit:
        nota.fyi("should now edit note %s" % args.edit)
        idnew = nota.edit(args.edit)
        sys.exit(0)
    
    if args.rehash:
        nota.fyi("should rehash now")
        nota.rehash()
        sys.exit(0)

    if args.do_import: # need do_ in name to avoid language conflict
        try:
            f = open(args.do_import, "r")
        except:
            nota.error("cannot read file '%s'" % args.do_import)
        notes = []
        i = 0
        for line in f:
            try:
                notes.append(json.loads(line))
            except:
                nota.error("cannot read line %d of file '%s'" % (line, args.do_import))
            i = i + 1
        for n in notes:
            # date will get set to now, which means also a new hash will be made
            try:
                id = nota.add(title=n["title"], keywords=n['keywords'], content=n["content"], due=n['due'])
            except:
                nota.error("cannot create note with title '%s'" % n["title"])

    if args.export:
        nota.fyi("should export now; hash=%s" % args.export)
        if args.export == '-':
            args.export = None
        noteIds = nota.find(args.export)
        for n in noteIds:
            print(json.dumps(n))
        sys.exit(0)
     
    if args.trash:
        nota.fyi("should show trash contents now")
        trashed = nota.find(trash=True)
        hal = nota.hash_abbreviation_length()
        for t in trashed:
            print(color.hash + "%s: " % t['hash'][0:hal] + color.normal, end="")
            if show_id:
                print("(%s) " % t['noteId'], end="")
            print(color.title + "%s" % t['title'] + color.normal + " ", end="\n")
        sys.exit(0)
    
    if args.add:
        if args.hash:
            nota.error("cannot specify a hash-code if the -a argument is given")
        #if args.mode == 'json':
        #    if not args.file:
        #        nota.error("Must use --file to name an input file")
        #    for line in open(args.file, "r"):
        #        line = line.rstrip()
        #        if args.debug:
        #            print(line, '\n')
        #        if (len(line)) > 1:
        #            try:
        #                j = json.loads(line)
        #                if args.debug:
        #                    print(j)
        #            except:
        #                nota.error("JSON file is not in proper format on line: %s" % line)
        #            if 'title' not in j:
        #                sys.exit(1)
        #            if 'content' not in j:
        #                j['content'] = ""
        #            ## FIXME keywords (chop whitespace)
        #            if 'keywords' in j:
        #                keyword = j['keywords'].split(',')
        #            else:
        #                keyword = ''
        #            if 'privacy' not in j:
        #                j['privacy'] = 0
        #            ## FIXME keywords (next does nothing?)
        #            j['keywords'].split(',')
        #            id = nota.add(title=j['title'], keywords=keyword, content=j['content'], privacy=j['privacy'])
        #    sys.exit(0)
        #elif args.mode== 'plain' and (args.title == "" and args.content == ""):
        if args.mode== 'plain' and (args.title == "" and args.content == ""):
            lines = sys.stdin.readlines()
            nota.fyi('reading from stdin')
            # trim newlines, plus any blank lines at start and end [FIXME: inelegant in the extreme]
            trim = 0
            nlines = len(lines)
            for l in range(nlines):
                if len(lines[l].strip()) < 1:
                    trim += 1
                else:
                    break
            lines = [lines[i].rstrip('\n') for i in range(trim, nlines)]
            trim = 0
            nlines = len(lines)
            for l in reversed(list(range(nlines))):
                if len(lines[l].strip()) < 1:
                    trim += 1
                else:
                    break
            lines = [lines[i].rstrip('\n') for i in range(0, nlines-trim)]
            # finally (after all that bad code!) we can parse for content
            title = ""
            content = ""
            keywords = []
            for line in lines:
                if nota.debug:
                    print("analysing line \"%s\"" % line)
                if title == "":
                    if line == "":
                        next # FIXME: should this be 'continue'?
                    title = line.strip()
                elif '<' in line:
                    keywords = re.sub(r'<.*>', '', line).strip()
                    keywords = re.sub(r' *\] *\[ *', ',', keywords).strip()
                    keywords = re.sub(r' *\[ *', '', keywords).strip()
                    keywords = re.sub(r' *\] *', '', keywords).strip()
                    #keywords = keywords.split(',')
                    keywords = [key.lstrip().rstrip() for key in keywords.split(',')]
                else:
                    if content == "" and line == "":
                        next # FIXME: should this be 'continue'?
                    content = content.lstrip() + line + '\n'
            if nota.debug:
                print("title:", title)
                print("keywords:", keywords)
                print("content: (%s)" % content)
            id = nota.add(title=title, keywords=keywords, content=content, privacy=args.privacy)
        elif args.mode == 'interactive' and (args.title == "" or args.content == "" or args.keywords == ""):
            if args.debug:
                print("should handle interactive now")
            ee = nota.editor_entry(title=args.title, keywords=args.keywords, content=args.content, privacy=args.privacy, due=args.due)
            id = nota.add(title=ee["title"], keywords=ee["keywords"], content=ee["content"], privacy=ee["privacy"], due=ee["due"])
        else:
            id = nota.add(title=args.title, keywords=args.keywords, content=args.content, privacy=args.privacy, due=args.due)
        sys.exit(0)
    
    #elif args.edit:
    #    if args.keywords[0] != "":
    #        if args.debug:
    #            print("KEYWORD \"%s\"" % args.keywordsoriginal)
    #        try:
    #            k = args.keywordsoriginal.split('=')
    #        except:
    #            nota.error("must specify e.g. 'nb edit --keyword OLD=NEW'")
    #        if args.debug:
    #            nota.fyi("renaming '%s' to '%s'" % (k[0], k[1]))
    #        nota.rename_keyword(k[0], k[1])
    #    else:
    #        if not id_desired:
    #            nota.error("must provide an ID, e.g. 'nb 1 -e' to edit note with ID=1")
    #        idnew = nota.edit(id_desired)
    #    sys.exit(0)
    
    
    else: # By a process of elimination, we must be trying to find notes.
        due_requested = nota.interpret_time(args.due)
        if id_desired is not None:
            if id_desired[0:1] == '-': # don't get confused by arg flags
                id_desired = None
        if id_desired is not None:
            if isinstance(id_desired, int) and id_desired <= 0:
                ids = nota.get_id_list()
                nids = len(ids)
                if (id_desired + nids - 1) < 0:
                    print("list only contains %d notes" % nids, end="\n")
                    sys.exit(1)
                #print(ids)
                #print(nids)
                id = ids[nids + id_desired - 1][0]
                #print("id:", id)
                found = nota.find(id=int(id), mode=args.mode, strict=args.strict, trash=False)
            else:
                found = nota.find(id=id_desired, mode=args.mode, strict=args.strict, trash=False)
        elif args.keywords[0] != '':
            found = nota.find(keywords=args.keywords, mode=args.mode, strict=args.strict)
        #elif args.id:
        #    print("FIXME: args.id case ... broken, I think (id=%s)" % args.id)
        #    found = nota.find(id=args.id, mode=args.mode, strict=args.strict)
        else:
            found = nota.find(keywords='?'.split(','), mode=args.mode, strict=args.strict)
        count = 0
        nfound = len(found)
        i = -1
        # Single hashes are printed to 7 chars (like on github), but multiple ones are shortened.
        hal = nota.hash_abbreviation_length()
        hash = []
        if nfound < 1:
            print("No notes match this request")
        if args.debug:
            print(hash)
        for f in found:
            i = i + 1
            #print(f)
            try:
                due = f['due']
            except:
                due = None
            #print("len(due): %d" % len(due))
            if due_requested[0]:
                if not due:
                    continue
                if args.debug:
                    print("due_requested: %s" % due_requested[0])
                due = datetime.datetime.strptime(due, '%Y-%m-%d %H:%M:%S.%f')
                if args.debug:
                    print("due value stored in note:", due)
                if due > due_requested[0]:
                    when = (due - due_requested[0]).total_seconds()
                else:
                    when = (due_requested[0]- due).total_seconds()
                if args.debug:
                    print('when:', when)
                if when < 0:
                    continue
            count += 1
            if args.count:
                continue
            #elif args.mode == "json":
            #    print(f['json'])
            elif args.mode== 'markdown':
                ## FIXME: redo this as the interactive UI firms up
                print("**%s**\n" %f ['title'])
                print("%s " %f ['hash'], end='')
                for k in f['keywords']:
                    print("[%s] " % k, end='')
                print("{%s / %s}\n" % (f['date'], f['modified']))
                print(f['content'].lstrip())
            else:
                if args.pretty == "oneline" and nfound > 1:
                    print(color.hash + "%s: " % f['hash'][0:hal] + color.normal, end="")
                    if show_id:
                        print("(%s) " % f['noteId'], end="")
                    print(color.title + "%s" % f['title'] + color.normal + " ", end="")
                    print("[", end="")
                    nk = len(f['keywords'])
                    for i in range(nk):
                        print(color.keyword + f['keywords'][i] + color.normal, end="")
                        if (i < nk-1):
                            print(", ", end="")
                    print("]", end="\n")
                else:
                    print(color.hash + "%s: " % f['hash'][0:7] + color.normal, end="")
                    if show_id:
                        print("(%s) " % f['noteId'], end="")
                    print(color.title + "%s" % f['title'] + color.normal + " ", end="")
                    print("[", end="")
                    nk = len(f['keywords'])
                    for i in range(nk):
                        print(color.keyword + f['keywords'][i] + color.normal, end="")
                        if (i < nk-1):
                            print(", ", end="")
                    print("]", end="\n")
                    #this commented-out block shows how to e.g. show just hour of day.
                    #created = f['date']
                    #dan = datetime.datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
                    #print(datetime.datetime.strftime(dan, "%Y-%m-%d %Hh"))
                    print("  created %s" % f['date'], end=" ")
                    if f['due'] and len(f['due']) > 0:
                        due = datetime.datetime.strptime(f['due'], '%Y-%m-%d %H:%M:%S.%f') # FIXME: make this 'due' DRY (+-20 lines)
                        now = datetime.datetime.now()
                        when = abs(due - now).total_seconds()
                        if due > now:
                            if when < 2 * 3600:
                                print("(due in %d minutes)" % round(when / 60))
                            elif when < 86400:
                                print("(due in %d hours)" % round(when / 3600))
                            else:
                                print("(due in %d days)" % round(when / 3600 / 24))
                        else:
                            if when < 2 * 3600:
                                print("(overdue by %d minutes)" % (when / 60))
                            elif when < 86400:
                                print("(overdue by %d hours)" % (when / 3600))
                            else:
                                print("(overdue by %.1f days)" % (when / 3600 / 24))
                    else:
                        print('')
                    content = f['content'].replace('\\n', '\n')
                    if not args.pretty == "twoline":
                        for contentLine in content.split('\n'):
                            c = contentLine.rstrip('\n')
                            if len(c):
                                print(" ", contentLine.rstrip('\n'))
                        print('')
        if args.count:
            print(count)
        #if args.mode != "json" and not args.count:
        if not args.count:
            t = nota.trash_length()[0]
            if t == 0:
                print("The trash is empty.")
            elif t == 1:
                print("The trash contains 1 note.")
            else:
                print("The trash contains %s notes." % t)
            print("Hint:", end=" ")
            hint = random_hint()
            if use_color:
                print(hint.replace(' "',' \'\033[1m').replace('"', '\033[0m\''))
            else:
                print(hint)
    
