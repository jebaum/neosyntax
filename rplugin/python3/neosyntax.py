import neovim
# TODO figure out the python way to do these imports, this is probably wrong
import pygments
import pygments.lexers
import pygments.token

@neovim.plugin

class Neosyntax(object):
    def __init__(self, nvim):
        self.nvim    = nvim
        #   swap src_ids. from brefdl: allocate two ids, and swap, adding before clearing, so things that don't change won't appear to flicker
        self.srcset  = True
        self.pygmap  = {}
        t = pygments.token
        self.pygmap[t.Name.Builtin] = "Function"
        self.pygmap[t.Name.Builtin.Pseudo] = "Boolean"
        self.pygmap[t.Comment.Sinle] = "Comment"
        self.pygmap[t.Comment.Hashbang] = "Comment"
        self.pygmap[t.Keyword.Namespace] = "Include"
        self.pygmap[t.Literal.Number.Integer] = "Number"
        self.pygmap[t.Literal.String.Single] = "String"
        self.pygmap[t.Literal.String.Double] = "String"
        self.pygmap[t.Keyword] = "Conditional"
        self.pygmap[t.Operator.Word] = "Conditional"

    @neovim.autocmd('BufEnter', pattern='nvim.py', eval='expand("<afile>")', sync=False)
    def autocmd_handler1(self, filename):
        self.highlight_buffer(None)

    @neovim.autocmd('TextChanged', pattern='nvim.py', eval='expand("<afile>")', sync=False)
    def autocmd_handler2(self, filename):
        self.highlight_buffer(None)

    @neovim.autocmd('TextChangedI', pattern='nvim.py', eval='expand("<afile>")', sync=False)
    def autocmd_handler3(self, filename):
        # TODO I was hoping that performance with syntax highlighting being done by this autocmd
        # would be comparable to plain old :syntax off and without this plugin
        # I think it is better, although I'll have to find a way to test that empirically
        # But, it still isn't as good as I hoped. Some flickering is still present
        # This may be a limitation of the tui and its ability to process remote api calls
        # Maybe this will work better in the eventual gui?
        # If nothing else, this function gives the option to have syntax highlighting turned off during
        # insert mode, then handled once you leave insert mode. Just have to remove the TextChangedI autocmd
        # and keep the TextChanged one (no I).
        # This is less than ideal for lots of situations, but is better than nothing
        self.highlight_buffer(None)

    @neovim.function('UnHighlightBuffer', sync=False)
    def unhighlight_buffer(self, args):
        buf     = self.nvim.buffers[0] # TODO can't hardcode this
        buf.clear_highlight(src_id=0, line_start=0, line_end=1000, async=True)
        buf.clear_highlight(src_id=1, line_start=0, line_end=1000, async=True)


    @neovim.function('HighlightBuffer', sync=False)
    def highlight_buffer(self, args):
        # XXX some ideas to help with flickering:
        #   use cursorholdi instead of textchangedi
        #   still use textchangedi, but also use a timer, and if the highlight is less than X seconds old, don't recompute, just return
        #   in insert mode, only recompute highlight groups on the line, or couple of lines surrounding the cursor
        #   get the viewport of the current window, render that region only or first before the rest of the buffer
        mylexer = pygments.lexers.PythonLexer()
        buf     = self.nvim.buffers[0] # TODO can't hardcode this
        # TODO - can I be more intelligent than doing the whole buffer every time? just the area around a change?
        fullbuf = [line for line in buf] # TODO is this necessary / efficient?

        addid = 1 if self.srcset else 2
        rmid  = 2 if self.srcset else 1
        self.srcset = not self.srcset
        arglist = []
        for linenum, line in enumerate(fullbuf, start=0):
            # TODO this is not only inefficient, it highlights things in correctly if they require multiple lines of context to identify
            # need to figure out a way to send entire file to get_tokens_unprocessed() at once, while maintaining knowledge about line numbers
            for (index, tokentype, value) in mylexer.get_tokens_unprocessed(line):
                # XXX issue with highlight groups
                # if `:syntax off` is set from vimrc, which is the entire goal of this plugin
                # then a lot (maybe all) of the language specific highlight groups will never be loaded
                # e.g., the "Comment" highlight group will probably exist (assuming the colorscheme
                # defines it), but "pythonComment" will not.
                # This isn't great, because I want to maintain the ability of users to modify individual
                # language highlight groups if they feel like it
                # I am not going to worry about this just yet, but I will need to find a way to address this eventually
                # For now, my solution is to just not use those language specific groups while I get the basics working
                # Also, it would be really swell if I didn't have to write this code for every single languages someone
                # might edit in vim. Actually, that's really the only way to do it.
                # I need to make the core functionality as generic as possible, while having an easy way to override settings
                # for a specific language if the generic way just won't work in all edge cases
                # This should be possible both within this python code, and from vimscript

                # compute all the add_highlight calls to be made
                if tokentype in self.pygmap:
                    arglist.append({'hl_group': self.pygmap[tokentype], 'line': linenum, 'col_start': index, 'col_end': index+len(value), 'src_id': addid, 'async': True})

        # make the calls
        for arg in arglist:
            buf.add_highlight(**arg)

        # clear old highlighting
        buf.clear_highlight(src_id=rmid, line_start=0, line_end=len(fullbuf), async=True)
