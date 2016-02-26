#!/usr/bin/python3.5
import neovim
import pygments
import pygments.lexers
import sys


if len(sys.argv) != 2:
    print('please provide exactly one filename')
    sys.exit()

filename = str(sys.argv[1])
lines    = [line for line in open(filename)]
numlines = len(lines)
maxlen   = len(str(numlines))
mylexer  = pygments.lexers.guess_lexer_for_filename(filename, lines)

for linenum, line in enumerate(lines, start=1):
    for (index, tokentype, value) in mylexer.get_tokens_unprocessed(line):
        if value.rstrip() != '':
            print(("Line {:" + str(maxlen) + "d}: '{}' matches '{}'").format(linenum, tokentype, value.rstrip()))

print("Lexer used: " + mylexer.name)
