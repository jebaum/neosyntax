#!/usr/bin/python3.5
import neovim
import pygments
import pygments.lexers
import pygments.token

nvim = neovim.attach('socket', path='/tmp/nvim')
