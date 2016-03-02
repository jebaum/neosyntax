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
        self.pygmap[t.Comment.Hashbang] = "Comment"
        self.pygmap[t.Comment.Single] = "Comment"
        self.pygmap[t.Comment] = "Comment" # older versions of pygments don't have Single and Hashbang?
        self.pygmap[t.Keyword.Namespace] = "Include"
        self.pygmap[t.Keyword] = "Conditional"
        self.pygmap[t.Literal.Number.Integer] = "Number"
        self.pygmap[t.Literal.String.Double] = "String"
        self.pygmap[t.Literal.String.Single] = "String"
        self.pygmap[t.Literal.String] = "String" # same comment as above
        self.pygmap[t.Name.Builtin.Pseudo] = "Boolean"
        self.pygmap[t.Name.Builtin] = "Function"
        self.pygmap[t.Name.Decorator] = "PreProc"
        self.pygmap[t.Operator.Word] = "Conditional"

    def msg(self, m):
        self.nvim.command("echom '" + str(m) + "'")

    @neovim.autocmd('BufEnter', pattern='nvim.py', eval='expand("<afile>")', sync=False)
    def autocmd_handler1(self, filename):
        self.highlight_buffer(None)

    @neovim.autocmd('TextChanged', pattern='nvim.py', eval='expand("<afile>")', sync=False)
    def autocmd_handler2(self, filename):
        self.highlight_buffer(None)

    @neovim.autocmd('TextChangedI', pattern='nvim.py', eval='expand("<afile>")', sync=False)
    def autocmd_handler3(self, filename):
        # TODO do special thing here if the user is currently typing inside a string or comment
        # to extend that highlight group a bunch of columns ahead
        # not sure where the best place to implement that will be

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

        # TODO figure out a way to queue these calls somehow? with the swapping src_id strategy,
        # flicker is gone when typing fast in insert mode, but typing too fast can still cause a
        # call backlog that can either crash the python host or just appear as lots of lag to the user

        # a timer? when this is called, start a timer that counts down from X seconds
        # throw away and subsequent calls that come in before the tmier is up

        # maybe highlight_buffer should take lines as an argument to facilitate the viewport shit?
        self.highlight_buffer(None)

    @neovim.function('UnHighlightBuffer', sync=False)
    def unhighlight_buffer(self, args):
        buf     = self.nvim.buffers[0] # TODO can't hardcode this
        end     = len([line for line in buf])
        buf.clear_highlight(src_id=1, line_start=0, line_end=end, async=True)
        buf.clear_highlight(src_id=2, line_start=0, line_end=end, async=True)


    @neovim.function('HighlightBuffer', sync=False)
    def highlight_buffer(self, args):
        # XXX some ideas to help with flickering:
        #   use cursorholdi instead of textchangedi
        #   still use textchangedi, but also use a timer, and if the highlight is less than X seconds old, don't recompute, just return
        #   in insert mode, only recompute highlight groups on the line, or couple of lines surrounding the cursor
        #   get the viewport of the current window, render that region only or first before the rest of the buffer
        mylexer = pygments.lexers.PythonLexer() # TODO  can't hardcode this, need to guess the correct lexer based on buffer name and contents
                                                # also, should cache a map of buffer -> lexer so this doesn't have to be done every time
        buf     = self.nvim.buffers[0] # TODO can't hardcode this either
        # TODO - can I be more intelligent than doing the whole buffer every time? just the area around a change?

        fullbuf = "\n".join([line for line in buf]) # TODO can i cache this somehow?

        addid = 1 if self.srcset else 2
        rmid  = 2 if self.srcset else 1
        self.srcset = not self.srcset
        arglist = []
        linenum = 0
        lastnewlineindex = -1
        for (index, tokentype, value) in mylexer.get_tokens_unprocessed(fullbuf):
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
            #  self.nvim.command("echom '" + + "'")
            #  if tokentype == pygments.token.Comment.Single and linenum == 7:
                #  self.nvim.command("echom '" + str(value) + "'")
                #  self.nvim.command("echom '" + str(index) + "'")
                #  self.nvim.command("echom '" + str(colstart) + "'")
                #  self.nvim.command("echom '" + str(lastnewlineindex) + "'")
                #  self.nvim.command("echom '" + str(linenum) + "'")
                #  self.nvim.command("echom '" + str(len(value)) + "'")

            # entire file is sent to pygments in a single big list, so column indexes are relative to the entire file, not per line
            # keep track of the last index where a newline was found
            # the index for the 0th column for the next line will be 1 after the lastnewlineindex
            # at the same time, also track line numbers
            if value == '\n':
                linenum += 1
                lastnewlineindex = index
            elif tokentype in self.pygmap:
                colstart = index - (lastnewlineindex + 1)
                arglist.append({'hl_group': self.pygmap[tokentype], 'line': linenum, 'col_start': colstart, 'col_end': colstart+len(value), 'src_id': addid, 'async': True})

        # make the calls
        for arg in arglist:
            buf.add_highlight(**arg)

        # clear old highlighting
        buf.clear_highlight(src_id=rmid, line_start=0, line_end=len(fullbuf), async=True)
