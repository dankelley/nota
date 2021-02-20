#!/usr/bin/python3

from .notaclass import Nota
import argparse
import sys
import json
import os
import re
import textwrap
import datetime
import tempfile
from random import randint, seed
from time import strptime
import subprocess

indent = "  "
showRandomHint = False

def nota():
    hints = [
            'see recent notes "nota -r"',
            'add a note: "nota -a" (opens EDITOR)',
            'add a note: "nota -a -t=title -c=content" (no EDITOR)',
            'add a note: "nota -a -t=title -c=content" -k=keywords"(no EDITOR)',
            'back up database by e.g. "cp ~/Dropbox/nota.db ~/nota-backup.db"',
            'create new book: "nota --create-book Bookname"',
            'create new note hashes: "nota --special rehash"',
            'create PDF of note with hash \'abcd\': "nota --markdown abcd | pandoc -V geometry:margin=1in -o abcd.pdf"',
            'delete note with hash \'ab...\': "nota -d ab"',
            'edit note with hash \'ab...\': "nota -e ab" (opens EDITOR)',
            'export all notes: "nota --export -" (import with \'--import\')',
            'export notes with hash \'ab...\': "nota --export ab"',
            'get help: "nota -h"',
            'import notes: "nota --import file.json" ("file.json" from "--export")',
            'list books: "nota --list-books"',
            'list keywords: "nota --list-keywords"',
            'list notes: "nota"',
            'list notes contained in the trash: "nota --trash"',
            'list notes due today: "nota --due today"',
            'list notes in markdown format: "nota --markdown"',
            'list notes with hash \'ab...\': "nota ab"',
            'list notes with keyword \'foo\': "nota -k foo"',
            'list notes within book: "nota -b Bookname"',
            'list notes without pager: "nota --pager=none"',
            'move note to new book: "nota --change-book hash Newbook"',
            'rename book: "nota --rename-book Old New"',
            'rename keyword: "nota --rename-keyword Old New"',
            'untrash notes with hash \'ab...\': "nota --undelete ab"',
            'extract attachments from note with given hash: "nota --extract hash"',
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
    pager = get_from_dotfile("~/.notarc", "pager", None)

    parser = argparse.ArgumentParser(prog="nota", description="Nota: an organizer for textual notes",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=textwrap.dedent('''\
    There are several ways to use nota. Try 'nota --hints' for some hints, and see
    http://dankelley.github.io/nota/ for more. Some common uses are as follows.

        nota                    # list notes, with first column being hash code
        nota ab                 # list notes with hash starting 'ab'
        nota -k key             # list notes with indicated keyword
        nota -a                 # add a note (opens a text editor)
        nota -a -t=... -c=...   # add a note (without a text editor)
        nota -e ab              # edit note with hash starting 'ab' (opens editor)
        nota -d ab              # delete note with hash starting 'ab'
        nota --export ab > F    # export note(s) to file 'F'
        nota --import F         # import note(s) from file 'F'
        nota --create-book Foo  # create a new book named Foo
        nota -b Foo             # list notes in book named Foo
        nota -r                 # list recent notes

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
        or specify hash, title, keyword, and book colors directly:
            color.hash = "red"
            color.title = "bold"
            color.keyword = "cyan"
            color.book = "blue"
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
    parser.add_argument("-a", "--add", action="store_true", dest="add", default=False, help="add a note; may be given alone, or in combination with --title and possibly also with --content and --keywords")
    parser.add_argument("-b", "--book", type=str, dest="book", default="", help="specify book named 'B'", metavar="B")
    parser.add_argument("-e", "--edit", type=str, default=None, help="edit note with hash 'H'", metavar="H")
    parser.add_argument("-d", "--delete", type=str, default=None, help="move note with hash 'H' to trash", metavar="H")
    parser.add_argument("-u", "--undelete", type=str, default=None, help="remove note with hash 'H' from trash", metavar="H")
    parser.add_argument("-t", "--title", type=str, default="", help="string with note title", metavar="T")
    parser.add_argument("-k", "--keywords", type=str, default="", help="string with comma-separated keywords", metavar="K")
    parser.add_argument("-A", "--attachments", type=str, default="", help="string with comma-separated filenames", metavar="A")
    #parser.add_argument("-K", "--Keywords", type=str, default="", help="string of comma-separated keywords", metavar="K")
    parser.add_argument("-c", "--content", type=str, default="", help="string with note contents", metavar="C")
    parser.add_argument("--extract", action="store_true", dest="extract_attachments", default=False, help="Extract attachments to a temporary directory")
    #parser.add_argument("-r", "--recent", action="store_true", dest="recent_notes", default=False, help="show recent notes")
    parser.add_argument("-r", "--recent", nargs='?', type=int, action="store", const=-2, default=-1, dest="recent_notes", help="show N recent notes (defaults to N=4)", metavar="N")
    parser.add_argument("--create-book", type=str, default="", dest="create_book", help="create a book named 'B'", metavar="B")
    parser.add_argument("--change-book", nargs=2, type=str, default="", dest="change_book", help="move note with hash 'H' to book 'B'", metavar=("H", "B"))
    parser.add_argument("--list-books", action="store_true", dest="list_books", default=False, help="list books")
    parser.add_argument("--list-keywords", action="store_true", dest="list_keywords", default=False, help="list keywords")
    parser.add_argument("--rename-book", type=str, nargs=2, help="rename notebook 'O' as 'N'", metavar=("O","N"))
    parser.add_argument("--rename-keyword", type=str, nargs=2, help="rename keyword 'O' as 'N'", metavar=("O","N"))
    parser.add_argument("--pager", type=str, dest="pager", default=None, help="pager for long output; may be 'more' (the default), 'less', or 'none'. It will be called with arguments '-R -X -F', which make sense for both 'less' and 'more'. If not given with --pager, a value is searched for in ~/.notarc.", metavar="cmd")
    parser.add_argument("--count", action="store_true", dest="count", default=False, help="report only count of found results")
    parser.add_argument("--debug", action="store_true", dest="debug", default=False, help="set debugging on")
    parser.add_argument("--export", type=str, default=None, help="export notes matching hash (use has '-' for all notes)", metavar="hash")
    parser.add_argument("--import", type=str, default=None, dest="do_import", help="import notes from --export output", metavar="file")
    if False: # may add later but don't tell users so, just yet
        parser.add_argument("--privacy", type=int, default=0, help="set privacy level (0=open, 1=closed)", metavar="level")
    parser.add_argument("--file", type=str, help="filename for i/o", metavar="name")
    # Process the dotfile (need for next parser call)
    defaultDatabase = get_from_dotfile("~/.notarc", "database", "~/Dropbox/nota.db")
    # Back to the parser
    parser.add_argument("--color", type=str, default=None, help="specify named scheme or True/False", metavar="c")
    parser.add_argument("--database", type=str, default=defaultDatabase, help="filename for database (defaults to ~/Dropbox/nota.db if not supplied as this argument, and if not specified in the ~/.notarc", metavar="db")
    parser.add_argument("--due", type=str, default="", help="time when item is due", metavar="when")
    parser.add_argument("--empty-trash", action="store_true", dest="empty_trash", default=False, help="empty trash, permanently deleting notes therein")
    parser.add_argument("--hints", action="store_true", dest="hints", default=False, help="get hints")
    parser.add_argument("--markdown", action="store_true", dest="markdown", default=False, help="use markdown format for output")
    parser.add_argument("--special", type=str, default="", help="special actions", metavar="action")
    parser.add_argument("--trash", action="store_true", dest="trash", default=False, help="show contents of trash")
    parser.add_argument("--verbose", type=int, default=None, help="set level of verbosity (0=quiet, 1=default)", metavar="level")
    parser.add_argument("--version", action="store_true", dest="version", default=False, help="get version number")
    args = parser.parse_args()

    # FIXME: probably this commented-out stuff can just be deleted,
    # since I like the look of the present scheme.
    # 1. list book in parentheses after the title
    # 2. list book names with indented notes beneath
    # book_scheme = get_from_dotfile("~/.notarc", "book_scheme", 1)
    #print("book_scheme %s" % book_scheme)

    args.keywordsoriginal = args.keywords
    args.keywords = [key.strip() for key in args.keywords.split(',')]
    args.attachmentsoriginal = args.attachments
    args.attachments = [key.strip() for key in args.attachments.split(',')]
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
            color.book = color_code('blue') + color_code('bold')
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
            color.book = color_code('blue') + color_code('bold')
    else:
        print("The color scheme given in the ~/.notarc file should be a string or logical")
        exit(1)

    if not use_color:
        color.hash = ''
        color.title = ''
        color.keyword = ''
        color.book = ''
        color.normal = ""


    if not args.debug:
        args.debug = debug

    if not args.database:
        args.database = defaultDatabase

    # Use specified pager, with --pager taking precedence
    permit_pager = True
    if args.special and "rehash" == args.special:
        permit_pager = False
    if args.export:
        permit_pager = False
    if args.pager:
        pager = args.pager
    elif not pager:
        pager = "less"
    if not pager in ("less", "more", "none"):
        print("pager must be 'less', 'more' or 'none', not '" + pager + "'")
        exit(1)
    if permit_pager and (not pager == "none") and sys.stdout.isatty():
        sys.stdout = os.popen(pager + ' -R -X -F', 'w')

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

    if args.create_book:
        nota.create_book(args.create_book)
        exit(0)

    if args.list_books:
        ''' List books. '''
        print("Books: ", end="")
        books = nota.list_books()
        nbooks = len(books)
        for i in range(nbooks):
            print(books[i], end="")
            if i < nbooks - 1:
                print(", ", end="")
            else:
                print("")
        exit(0)

    #if args.recent_notes:
    #    print("RECENT NOTES... (not coded yet)", end="")
    #    exit(0)

    if args.change_book:
        (hash, book) = args.change_book
        nota.change_book(hash, book)
        exit(0)

    if args.rename_book:
        (old, new) = args.rename_book
        nota.rename_book(old, new)
        exit(0)

    if args.list_keywords:
        ''' List keywords. '''
        print("Keywords: ", end="")
        keywords = nota.list_keywords()
        nkeywords = len(keywords)
        for i in range(nkeywords):
            #print('"%s"' % keywords[i], end="")
            print('%s' % keywords[i], end="")
            if i < nkeywords - 1:
                print(", ", end="")
            else:
                print("")
        exit(0)

    if args.rename_keyword:
        (old, new) = args.book_rename
        nota.keyword_rename(old, new)
        exit(0)

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

    if args.book:
        b = nota.book_index(args.book)
        if len(b) > 1:
            nota.error("Abbreviation '%s' matches to %d books: %s" % (args.book, len(b), list(b.keys())))
        if not b:
            nota.error("No book named '%s'" % args.book)
        book = list(b.values())[0]
        nota.fyi("--book yields book index %s" % book)
    else:
        book = -1

    if args.delete:
        nota.fyi("should now delete note %s" % args.delete)
        nota.delete(args.delete)
        sys.exit(0)

    if args.undelete:
        nota.fyi("should now undelete note with hash %s" % args.undelete)
        nota.undelete(args.undelete)
        sys.exit(0)

    if args.empty_trash:
        nota.fyi("should now empty the trash")
        nota.empty_trash()
        sys.exit(0)

    if args.edit:
        nota.fyi("should now edit note %s" % args.edit)
        nota.edit(args.edit)
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
                # The 'book' is ignored because different users have different books.
                id = nota.add(title=n["title"], keywords=n['keywords'], content=n["content"], date=n['date'], due=n['due'])
            except:
                nota.error("cannot create note with title '%s'" % n["title"])

    if args.export:
        nota.fyi("should export now; hash=%s" % args.export)
        if args.export == '-':
            args.export = None
        noteIds = nota.find_by_hash(args.export)
        for n in noteIds:
            del n["book"] # not useful in any other context
            del n["noteId"] # not useful in any other context
            print(json.dumps(n))
        sys.exit(0)

    if args.trash:
        nota.fyi("should show trash contents now")
        #print("args.keywords %s" % args.keywords)
        #print("args.keywords[0] '%s'" % args.keywords[0])
        #print("args.hash %s" % args.hash)
        if not '' == args.keywords[0]:
            trashed = nota.find_by_keyword(keywords=args.keywords, book=0)
        else:
            trashed = nota.find_by_hash(hash=args.hash, book=0)
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
            ee = nota.editor_entry(title=args.title, content=args.content, keywords=args.keywords, attachments=args.attachments, due=args.due, book=book)
            nota.add(title=ee["title"], keywords=ee["keywords"], content=ee["content"], book=ee["book"], due=ee["due"],
                    attachments=ee["attachments"])
        else:
            # FIXME: allow book below
            nota.add(title=args.title, keywords=args.keywords, content=args.content, due=args.due, book=book,
                    attachments=args.attachments)
        sys.exit(0)

    # By a process of elimination, we must be trying to find notes.
    due_requested = nota.interpret_time(args.due)
    if id_desired is not None:
        if id_desired[0:1] == '-': # don't get confused by arg flags
            id_desired = None
    trash_count = None
    if id_desired is not None:
        nota.fyi("search notes by hash (book=%s)" % book)
        found = nota.find_by_hash(hash=id_desired, book=book) # -1 means all books but trash
        trash_count = len(nota.find_by_hash(hash=id_desired, book=0))
    elif len(args.keywords[0]) and args.keywords[0] != '?':
        nota.fyi("search notes by keyword (book=%s)" % book)
        found = nota.find_by_keyword(keywords=args.keywords, book=book)
        trash_count = len(nota.find_by_keyword(keywords=args.keywords, book=0))
    elif args.recent_notes:
        if args.recent_notes is -2:
            found = nota.find_recent(nrecent=4)
        elif args.recent_notes is -1:
            found = nota.find_by_hash(hash=args.hash, book=book)
            trash_count = len(nota.find_by_hash(hash=args.hash, book=0))
        else:
            found = nota.find_recent(nrecent=args.recent_notes)
        trash_count = 0
    else:
        nota.fyi("Search notes by hashless method (book=%s)" % book)
        found = nota.find_by_hash(hash=args.hash, book=book)
        trash_count = len(nota.find_by_hash(hash=args.hash, book=0))
    count = 0
    nfound = len(found)
    i = -1
    # Single hashes are printed to 7 chars (like on github), but multiple ones are shortened.
    hal = nota.hash_abbreviation_length()
    hash = []
    if nfound < 1:
        print("No active notes match this request.")
    nota.fyi("hash: %s" % hash)
    books = nota.list_books()
    books_used = []
    have_default = False
    for f in found:
        if f['book'] > 0 and f['book'] != 1 and f['book'] not in books_used:
            books_used.append(f['book'])
        if f['book'] == 1:
            have_default = True
    books_used = sorted(books_used, key=lambda s: books[s].lower())
    if have_default:
        books_used.insert(0, 1)
    for b in books_used:
        if not args.count and not args.due:
            if args.markdown:
                print("Book: %s" % nota.book_name(b), end="\n\n")
            else:
                print(color.book + "Book: %s" % nota.book_name(b) + color.normal, end="\n")
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
            count += 1 # FIXME: bug: 'nota --count' gives a huge number
            if not args.count:
                if nfound > 1:
                    # Several notes, so just summarize.
                    if args.markdown:
                        print("%s" % f['hash'][0:hal], end="\n")
                        if show_id:
                            print("(%s) " % f['noteId'], end="")
                        print("%s\n\n" % f['title'], end="")
                        print("[", end="")
                        nk = len(f['keywords'])
                        for i in range(nk):
                            print("*%s*" % f['keywords'][i], end="")
                            if (i < nk-1):
                                print(", ", end="")
                        print("]", end="\n\n")
                    else:
                        if f['book'] == b:
                            #print("{%s}" % f['book']) # a number
                            print(indent + color.hash + "%s " % f['hash'][0:hal] + color.normal, end="")
                            if show_id:
                                print("(%s) " % f['noteId'], end="")
                            print(color.title + "%s" % f['title'] + color.normal + " ", end="")
                            #print("(" + color.hash + books[f['book']] + color.normal + ") ", end="")
                            print("[", end="")
                            nk = len(f['keywords'])
                            for i in range(nk):
                                print(color.keyword + f['keywords'][i] + color.normal, end="")
                                if (i < nk-1):
                                    print(", ", end="")
                            print("]", end="")
                            print(" %s " % nota.age(f['date']), end="\n")
                else:
                    # Just 1 note, so print in full
                    if args.markdown:
                        print("Hash: `%s`\n\n" % f['hash'][0:7], end="")
                        if show_id:
                            print("(%s) " % f['noteId'], end="")
                        print("%s\n\n" % f['title'], end="")
                        print("Keywords: ", end="")
                        nk = len(f['keywords'])
                        for i in range(nk):
                            print(f['keywords'][i], end="")
                            if (i < nk-1):
                                print(", ", end="")
                        print("", end="\n\n")
                        print("Created: %s" % f['date'], end=" ")
                        if f['due'] and len(f['due']) > 0:
                            print(due_str(f['due']))
                        else:
                            print('')
                        print('')
                        content = f['content'].replace('\\n', '\n')
                        for contentLine in content.split('\n'):
                            c = contentLine.rstrip('\n')
                            if len(c):
                                if args.markdown:
                                    print(contentLine.rstrip('\n'), '\n')
                                else:
                                    print(" ", contentLine.rstrip('\n'), '\n')
                        print('')
                    else:
                        print(indent + color.hash + "%s " % f['hash'][0:7] + color.normal, end="")
                        if show_id:
                            print("(%s) " % f['noteId'], end="")
                        print(color.title + "%s" % f['title'] + color.normal + " ", end="")
                        #if len(books) > 1:
                        #    print("(" + color.book + books[f['book']] + color.normal + ") ", end="")
                        print("[", end="")
                        nk = len(f['keywords'])
                        for i in range(nk):
                            print(color.keyword + f['keywords'][i] + color.normal, end="")
                            if (i < nk-1):
                                print(", ", end="")
                        print("]", end="")
                        #print(" %s" % f['date'], end=" ")
                        print(" %s " % nota.age(f['date']), end="")
                        try:
                            if f['due'] and len(f['due']) > 0:
                                print(due_str(f['due']))
                            else:
                                print('')
                        except:
                            print('')
                        content = f['content'].replace('\\n', '\n')
                        for contentLine in content.split('\n'):
                            c = contentLine.rstrip('\n')
                            if len(c):
                                if args.markdown:
                                    print(contentLine.rstrip('\n'))
                                else:
                                    print(" ", contentLine.rstrip('\n'))
                        #print('')
                    #print("id=%d"%f['noteId'])
                    #print("attachmentIds:")
                    attachmentIds = nota.get_attachment_list(noteId=f['noteId'])
                    if len(attachmentIds) > 0:
                        if args.extract_attachments:
                            print("  Attachments: ")
                        else:
                            print("  Attachments (use --extract argument to extract these): ")
                    for attachmentId in attachmentIds:
                        #print(attachmentId[0])
                        filename = nota.get_attachment_filename(attachmentId=attachmentId[0])[0]
                        #print("attachmentId %d" % attachmentId[0])
                        #echo "SELECT contents FROM attachment WHERE attachmentId=3;" | sqlite3 ~/Dropbox/nota.db
                        if args.extract_attachments:
                            #tmp = tempfile.NamedTemporaryFile(mode="wb", prefix="nota_", suffix="_"+str(filename[0]))
                            contents = nota.get_attachment_contents(attachmentId=attachmentId[0])
                            tmpname = str(f['hash'][0:7]) + "_" + os.path.basename(str(filename[0]))
                            try:
                                tmpfile = open(tmpname, "wb")
                                tmpfile.write(str(contents[0]))
                                tmpfile.close()
                            except:
                                print("cannot store attachment in local directory")
                            print("   '%s'\n        saved as '%s' in present directory" % (str(filename[0]), tmpname))
                        else:
                            print("   %s" % filename)
    if args.count:
        print(count)
    if not args.count and args.verbose > 0 and not args.markdown:
        t = nota.trash_length()[0] # FIXME: should just return the [0]
        t = trash_count
        if t == 0:
            if nfound == 0:
                print("The trash has no notes matching this search.")
        elif t == 1:
            print("The trash has 1 note matching ths search.")
        else:
            print("The trash has %s notes matching this search." % t)
        if showRandomHint:
            print("Hint:", end=" ")
            hint = random_hint()
            if args.markdown:
                print(hint.replace(' "', ' `').replace('"', '`'))
            elif use_color:
                print(hint.replace(' "',' \'\033[1m').replace('"', '\033[0m\''))
            else:
                print(hint)

