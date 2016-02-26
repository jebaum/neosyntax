#!/usr/bin/python3.5
import neovim
import pygments
import pygments.lexers

nvim = neovim.attach('socket', path='/tmp/nvim')
buf = nvim.buffers[0]

mylexer = pygments.lexers.PythonLexer()
fulbuf = [line.decode("utf-8") for line in buf]

for linenum, line in enumerate(fulbuf, start=0):
    for (index, tokentype, value) in mylexer.get_tokens_unprocessed(line):
        cols = len(value)
        print(tokentype, value, cols)
