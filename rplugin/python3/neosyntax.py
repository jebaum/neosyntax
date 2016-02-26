import neovim
import pygments

@neovim.plugin

class Neosyntax(object):
    def __init__(self, nvim):
        self.nvim = nvim

    @neovim.function('HighlightBuffer')
    def highlight_buffer(self, args):
        self.nvim.command('echom "hello world"')
