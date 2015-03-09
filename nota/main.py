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
            'add a note: "nota -a" (opens EDITOR)', 
            'add a note: "nota -a -t=title -c=content" (no EDITOR)', 
            'add a note: "nota -a -t=title -c=content" -k=keywords"(no EDITOR)', 
            'back up database by e.g. "cp ~/Dropbox/nota.db ~/nota-backup.db"',
            'create new note hashes: "nota --developer=rehash"',
            'delete note with hash \'ab...\': "nota -d ab"',
            'edit note with hash \'ab...\': "nota -e ab" (opens EDITOR)',
            'export all notes: "nota --export -" (import with \'--import\')',
            'export notes with hash \'ab...\': "nota --export ab"',
            'import notes: "nota --import file.json" ("file.json" from "--export")',
            'list all notes: "nota"',
            'list notes contained in the trash: "nota --trash"',
            'list notes due today: "nota --due today"',
            'list notes in markdown format: "nota --markdown"',
            'list note with hash \'ab...\': "nota ab"',
            'list notes with keyword \'foo\': "nota -k foo"',
            'untrash notes with hash \'ab...\': "nota --undelete ab"',
            'visit http://dankelley.github.io/nota/documentation.html to learn more']

    def color_code(c, default="\033[0m"):
        '''
        Look up a color by name, returning the escape code for that color. Only
        certain colors are recognized, and black (\033[0m) is returned if 'c'
        is not recognized.
        '''
        c = c.replace("'", "").replace('"', "")
        #if c[0:1] == '\\':
        #    return(c)
        lookup = {"bold":'\033[1m', "dim":'\033[2m', "underlined":'\033[4m',
                "blink":'\033[5m', "reverse":'\033[7m', "black":'\033[0m',
                "red":'\033[31m', "green":'\033[32m', "yellow":'\033[33m',
                "blue":'\033[34m', "magenta":'\033[35m', "cyan":'\033[36m',
                "lightgray":'\033[37m', "darkgray":'\033[90m',
                "lightred":'\033[91m', "lightgreen":'\033[92m',
                "lightyellow":'\033[93m', "lightblue":'\033[94m',
                "lightmagenta":'\033[95m', "lightcyan":'\033[96m'}
        try:
            rval = lookup[c]
        except:
            rval = default
        return(rval)

 
    def due_str(due):
        due = datetime.datetime.strptime(due, '%Y-%m-%d %H:%M:%S.%f')
        now = datetime.datetime.now()
        when = abs(due - now).total_seconds()
        if due > now:
            if when < 2 * 3600:
                return("(due in %d minutes)" % round(when / 60))
            elif when < 86400:
                return("(due in %d hours)" % round(when / 3600))
            else:
                return("(due in %d days)" % round(when / 3600 / 24))
        else:
            if when < 2 * 3600:
                return("(overdue by %d minutes)" % (when / 60))
            elif when < 86400:
                return("(overdue by %d hours)" % (when / 3600))
            else:
                return("(overdue by %.1f days)" % (when / 3600 / 24))
 
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
    verbose = int(get_from_dotfile("~/.notarc", "verbose", -999))
   
    parser = argparse.ArgumentParser(prog="nota", description="Nota: an organizer for textual notes",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=textwrap.dedent('''\
    There are several ways to use nota.  Try 'nota -h' for some hints.  The most
    common uses are as follows.
    
        nota                  # list notes, with first column being hash code
        nota ab               # list notes with hash starting 'ab'
        nota -k key           # list notes with indicated keyword
        nota -a               # add a note (opens a text editor)
        nota -a -t=... -c=... # add a note (without a text editor)
        nota -e ab            # edit note with hash starting 'ab' (opens editor)
        nota -d ab            # delete note with hash starting 'ab'
        nota --export ab > F  # export note(s) to file 'F'
        nota --import F       # import note(s) from file 'F'

    The ~/.notarc file may be used for customization, and may contain e.g. the
    following:
    
        Specify database name
            db = \"~/Dropbox/nota.db\"
        Turn on debugging mode
            debug = True
        Set verbose level to 0 to turn off trash/hint reports
            verbose = 0
        Show internal database ID numbers for development tests
            show_id = False
        Use color in displays
            color = True
        or set up a color theme, using one of
            color = "bubblegum" # red hash, cyan keywords
            color = "forest" # green hash, straw keywords
            color = "run" # red hash, underlined keywords
            color = "default" # same as "bubblegum"
        or specify hash, title, and keyword colors directly:
            color.hash = "red"
            color.title = "bold"
            color.keyword = "cyan"
        where the black variants are: "bold", "dim", "underlined", "blink",
        "reverse" and "normal" and the available colors are: "black", "red",
        "green", "yellow", "blue", "magenta", "cyan", "lightgray", "darkgray",
        "lightred", "lightgreen", "lightyellow", "lightblue", "lightmagenta",
        and "lightcyan".

    Advanced usage:
        
        Recreate hashes (to remove duplicate hashes, which are unlikely)
            nota --special=rehash
    

        '''))
    
    parser.add_argument("hash", nargs="?", default="", help="abbreviated hash to search for", metavar="hash")
    parser.add_argument("-a", "--add", action="store_true", dest="add", default=False, help="add a note")
    parser.add_argument("-e", "--edit", type=str, default=None, help="edit note with abbreviated hash 'h'", metavar="h")
    parser.add_argument("-d", "--delete", type=str, default=None, help="move note abbreviated hash 'h' to trash", metavar="h")
    parser.add_argument("-u", "--undelete", type=str, default=None, help="remove note with abbreviated hash 'h' from trash", metavar="h")
    parser.add_argument("-t", "--title", type=str, default="", help="a short title", metavar="t")
    parser.add_argument("-k", "--keywords", type=str, default="", help="string of comma-separated keywords", metavar="k")
    #parser.add_argument("-K", "--Keywords", type=str, default="", help="string of comma-separated keywords", metavar="K")
    parser.add_argument("-c", "--content", type=str, default="", help="string to be used for content", metavar="c")
    parser.add_argument("--count", action="store_true", dest="count", default=False, help="report only count of found results")
    parser.add_argument("--debug", action="store_true", dest="debug", default=False, help="set debugging on")
    parser.add_argument("--export", type=str, default=None, help="export notes matching hash (use has '-' for all notes)", metavar="hash")
    parser.add_argument("--import", type=str, default=None, dest="do_import", help="import notes from file created by --export", metavar="file")
    if False: # may add later but don't tell users so
        parser.add_argument("--privacy", type=int, default=0, help="set privacy level (0=open, 1=closed)", metavar="level")
    parser.add_argument("--file", type=str, help="filename for i/o", metavar="name")
    # Process the dotfile (need for next parser call)
    defaultDatabase = get_from_dotfile("~/.notarc", "database", "~/Dropbox/nota.db")
    # Back to the parser
    parser.add_argument("--color", type=str, default=None, help="specify named scheme or True/False", metavar="c")
    parser.add_argument("--database", type=str, default=defaultDatabase, help="filename for database", metavar="db")
    parser.add_argument("--due", type=str, default="", help="time when item is due", metavar="when")
    parser.add_argument("--emptytrash", action="store_true", dest="emptytrash", default=False, help="empty trash, permanently deleting notes therein")
    parser.add_argument("--hints", action="store_true", dest="hints", default=False, help="get hints")
    parser.add_argument("--markdown", action="store_true", dest="markdown", default=False, help="use markdown format for output")
    parser.add_argument("--special", type=str, default="", help="special actions", metavar="action")
    parser.add_argument("--trash", action="store_true", dest="trash", default=False, help="show contents of trash")
    parser.add_argument("--verbose", type=int, default=None, help="set level of verbosity (0=quiet, 1=default)", metavar="level")
    parser.add_argument("--version", action="store_true", dest="version", default=False, help="get version number")
    args = parser.parse_args()
    
    args.keywordsoriginal = args.keywords
    args.keywords = [key.lstrip().rstrip() for key in args.keywords.split(',')]
    #args.Keywordsoriginal = args.Keywords
    #args.Keywords = [Key.lstrip().rstrip() for Key in args.Keywords.split(',')]

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
        if color_scheme == "forest":
            color.hash = color_code('green')
            color.title = color_code('bold')
            color.keyword = color_code('yellow')
        elif color_scheme == "run":
            color.hash = color_code('red')
            color.title = color_code('bold')
            color.keyword = color_code('underlined')
        elif color_scheme == "bubblegum":
            color.hash = color_code('red')
            color.title = color_code('bold')
            color.keyword = color_code('magenta')
        elif color_scheme == "default":
            color.hash = color_code('red')
            color.title = color_code('bold')
            color.keyword = color_code('magenta')
        else:
            print("Unknown color scheme '%s'; using 'default' instead." % color_scheme)
            color.hash = color_code('red')
            color.title = color_code('bold')
            color.keyword = color_code('magenta')
        use_color = True
    elif isinstance(color_scheme, bool):
        use_color = color_scheme
        if use_color:
            # color.hash = '\033[' + get_from_dotfile("~/.notarc", "color.hash", '31m')
            # color.title = '\033[' + get_from_dotfile("~/.notarc", "color.title", '1m')
            # color.keyword = '\033[' + get_from_dotfile("~/.notarc", "color.keyword", '35m')
            color.hash = color_code(get_from_dotfile("~/.notarc", "color.hash", 'red'))
            color.title = color_code(get_from_dotfile("~/.notarc", "color.title", 'bold'))
            color.keyword = color_code(get_from_dotfile("~/.notarc", "color.keyword", 'magenta'))
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
    if args.verbose is None:
        if verbose < 0:
            args.verbose = 1
        else:
            args.verbose = verbose
    #print("args.verbose: %s" % args.verbose)
    
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
    #if not args.pretty:
    #    args.pretty = get_from_dotfile("~/.notarc", "pretty", "oneline")
    
    if args.special:
        if args.special == "rehash":
            nota.fyi("should rehash now")
            nota.rehash()
            sys.exit(0)
        else:
            nota.error("unknown action '%s'" % args.special)
    
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
            try:
                id = nota.add(title=n["title"], keywords=n['keywords'], content=n["content"], date=n['date'], due=n['due'])
            except:
                nota.error("cannot create note with title '%s'" % n["title"])

    if args.export:
        nota.fyi("should export now; hash=%s" % args.export)
        if args.export == '-':
            args.export = None
        noteIds = nota.find_by_hash(args.export)
        for n in noteIds:
            print(json.dumps(n))
        sys.exit(0)
     
    if args.trash:
        nota.fyi("should show trash contents now")
        #print("args.keywords %s" % args.keywords)
        #print("args.keywords[0] '%s'" % args.keywords[0])
        #print("args.hash %s" % args.hash)
        if not '' == args.keywords[0]:
            trashed = nota.find_by_keyword(keywords=args.keywords, in_trash=True)
        else:
            trashed = nota.find_by_hash(hash=args.hash, in_trash=True)
        hal = nota.hash_abbreviation_length()
        for t in trashed:
            print(color.hash + "%s: " % t['hash'][0:hal] + color.normal, end="")
            if show_id:
                print("(%s) " % t['noteId'], end="")
            print(color.title + "%s" % t['title'] + color.normal + " ", end="")
            print("[", end="")
            nk = len(t['keywords'])
            for i in range(nk):
                print(color.keyword + t['keywords'][i] + color.normal, end="")
                if (i < nk-1):
                    print(", ", end="")
            print("]", end="\n")
        sys.exit(0)

    
    if args.add:
        if args.hash:
            nota.error("cannot specify a hash-code if the -a argument is given")
        # If no title is given, need to use the editor.
        if args.title == "":
            nota.fyi("should handle interactive now")
            ee = nota.editor_entry(title=args.title, keywords=args.keywords, content=args.content, due=args.due)
                    #privacy=args.privacy, due=args.due)
            id = nota.add(title=ee["title"], keywords=ee["keywords"], content=ee["content"], due=ee["due"])
                    #privacy=ee["privacy"], due=ee["due"])
        else:
            id = nota.add(title=args.title, keywords=args.keywords, content=args.content, due=args.due)
                    #privacy=args.privacy, due=args.due)
        sys.exit(0)

    # By a process of elimination, we must be trying to find notes.
    due_requested = nota.interpret_time(args.due)
    if id_desired is not None:
        if id_desired[0:1] == '-': # don't get confused by arg flags
            id_desired = None
    trash_count = None
    if id_desired is not None:
        nota.fyi("search notes by hash")
        found = nota.find_by_hash(hash=id_desired, in_trash=False)
        trash_count = len(nota.find_by_hash(hash=id_desired, in_trash=True))
    elif len(args.keywords[0]) and args.keywords[0] != '?':
        nota.fyi("search notes by keyword")
        found = nota.find_by_keyword(keywords=args.keywords, in_trash=False)
        trash_count = len(nota.find_by_keyword(keywords=args.keywords, in_trash=True))
    # elif len(args.Keywords[0]) and args.Keywords[0] != '?':
    #     nota.fyi("search notes by keyword (with strict match)")
    #     found = nota.find_by_keyword(keywords=args.keywords, strict_match=True, in_trash=False)
    #     trash_count = len(nota.find_by_keyword(keywords=args.keywords, strict_match=True, in_trash=True))
    else:
        nota.fyi("Search notes by hash.")
        found = nota.find_by_hash(hash=None, in_trash=False)
        trash_count = len(nota.find_by_hash(hash=None, in_trash=True))
    count = 0
    nfound = len(found)
    i = -1
    # Single hashes are printed to 7 chars (like on github), but multiple ones are shortened.
    hal = nota.hash_abbreviation_length()
    hash = []
    if nfound < 1:
        print("No active notes match this request.")
    if args.debug:
        print(hash)
    for f in found:
        i = i + 1
        #print(f)
        try:
            due = f['due']
        except:
            due = None
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
        else:
            if nfound > 1:
                if args.markdown:
                    print("%s: " % f['hash'][0:hal], end="")
                    if show_id:
                        print("(%s) " % f['noteId'], end="")
                    print("**%s** " % f['title'], end="")
                    print("[", end="")
                    nk = len(f['keywords'])
                    for i in range(nk):
                        print("*%s*" % f['keywords'][i], end="")
                        if (i < nk-1):
                            print(", ", end="")
                    print("]", end="\n\n")
                else:
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
                if args.markdown:
                    print("%s: " % f['hash'][0:7], end="")
                    if show_id:
                        print("(%s) " % f['noteId'], end="")
                    print("**%s** " % f['title'], end="")
                    print("[", end="")
                    nk = len(f['keywords'])
                    for i in range(nk):
                        print(f['keywords'][i], end="")
                        if (i < nk-1):
                            print(", ", end="")
                    print("]", end="\n\n")
                    print("  created %s" % f['date'], end=" ")
                    if f['due'] and len(f['due']) > 0:
                        print(due_str(f['due']))
                    else:
                        print('')
                    print('')
                    content = f['content'].replace('\\n', '\n')
                    for contentLine in content.split('\n'):
                        c = contentLine.rstrip('\n')
                        if len(c):
                            print(" ", contentLine.rstrip('\n'), '\n')
                    print('')
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
                    print("  created %s" % f['date'], end=" ")
                    if f['due'] and len(f['due']) > 0:
                        print(due_str(f['due']))
                    else:
                        print('')
                    content = f['content'].replace('\\n', '\n')
                    for contentLine in content.split('\n'):
                        c = contentLine.rstrip('\n')
                        if len(c):
                            print(" ", contentLine.rstrip('\n'))
                    #print('')
    if args.count:
        print(count)
    if not args.count and args.verbose > 0:
        t = nota.trash_length()[0] # FIXME: should just return the [0]
        t = trash_count
        if t == 0:
            print("The trash has no notes matching this search.")
        elif t == 1:
            print("The trash has 1 note matching ths search.")
        else:
            print("The trash has %s notes matching this search." % t)
        if args.markdown:
            print("\n")
        print("Hint:", end=" ")
        hint = random_hint()
        if args.markdown:
            print(hint.replace(' "', ' `').replace('"', '`'))
        elif use_color:
            print(hint.replace(' "',' \'\033[1m').replace('"', '\033[0m\''))
        else:
            print(hint)
    
