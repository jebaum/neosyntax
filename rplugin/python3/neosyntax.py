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

    @neovim.autocmd('BufEnter', pattern='*', eval='expand("<abuf>")', sync=False)
    def autocmd_handler1(self, bufnr): # TODO how to pass in multiple arguments?
        self.highlight_buffer(int(bufnr))

    @neovim.autocmd('TextChanged', pattern='*', eval='expand("<abuf>")', sync=False)
    def autocmd_handler2(self, bufnr):
        self.highlight_buffer(int(bufnr))

    @neovim.autocmd('TextChangedI', pattern='*', eval='expand("<abuf>")', sync=False)
    def autocmd_handler3(self, bufnr):
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
        self.highlight_buffer(int(bufnr))

    @neovim.function('UnHighlightBuffer', sync=False)
    def unhighlight_buffer(self, bufnr):
        bufnr = int(bufnr)
        for b in self.nvim.buffers:
            if b.number == bufnr: # TODO what if it isn't found?
                buf = b
                break
        end = len([line for line in buf])
        buf.clear_highlight(src_id=1, line_start=0, line_end=end, async=True)
        buf.clear_highlight(src_id=2, line_start=0, line_end=end, async=True)


    @neovim.function('HighlightBuffer', sync=False)
    def highlight_buffer(self, bufnr):
        # XXX some ideas to help with flickering:
        #   use cursorholdi instead of textchangedi
        #   still use textchangedi, but also use a timer, and if the highlight is less than X seconds old, don't recompute, just return
        #   in insert mode, only recompute highlight groups on the line, or couple of lines surrounding the cursor
        #   get the viewport of the current window, render that region only or first before the rest of the buffer
        # also, should cache a map of buffer -> lexer so this doesn't have to be done every time

        for b in self.nvim.buffers:
            if b.number == bufnr: # TODO what if it isn't found?
                buf = b
                break
        # TODO - can I be more intelligent than doing the whole buffer every time? just the area around a change?

        fullbuf = "\n".join([line for line in buf]) # TODO can i cache this somehow?
        self.msg(fullbuf)
        mylexer = pygments.lexers.guess_lexer(fullbuf) # TODO cache this

        # TODO these numbers need to be per buffer
        addid = 1 if self.srcset else 2
        rmid  = 2 if self.srcset else 1
        self.srcset = not self.srcset

        arglist = []
        linenum = 0
        lastnewlineindex = -1
        for (index, tokentype, value) in mylexer.get_tokens_unprocessed(fullbuf):
            self.msg("line: " + str(linenum))
            self.msg("idx : " + str(index))
            self.msg("lni : " + str(lastnewlineindex))
            self.msg("tok : " + str(tokentype))
            self.msg("val : " + str(value))
            self.msg("--------")
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

            # entire file is sent to pygments in a single big list, so column indexes are relative to the entire file, not per line
            # keep track of the last index where a newline was found
            # the index for the 0th column for the next line will be 1 after the lastnewlineindex
            # at the same time, also track line numbers

            # TODO newlines are their own tokens in python, but not in bash, and probably other languages
            # I assume any language where newlines don't have semantic meaning won't have them as tokens
            # need to find a better way to keep track of line numbers
            # shit.
            # so i can either override each lexer that doesn't have newlines as tokens, see here:
                # http://pygments.org/docs/lexerdevelopment/#modifying-token-streams
            # or, note down the byte index of newlines in the fullbuf stream and work with that
            # first method might be marginally faster, but is so ugly it makes me want to cry
            # probably will go with second method.
            if value == '\n':
                linenum += 1
                lastnewlineindex = index
                #  self.msg('found newline')
            elif tokentype in self.pygmap:
                colstart = index - (lastnewlineindex + 1)
                # precompute all the add_highlight calls to be made
                arglist.append({'hl_group': self.pygmap[tokentype], 'line': linenum, 'col_start': colstart, 'col_end': colstart+len(value), 'src_id': addid, 'async': True})

        # done computing, make the calls
        for arg in arglist:
            buf.add_highlight(**arg)

        # clear old highlighting
        buf.clear_highlight(src_id=rmid, line_start=0, line_end=len(fullbuf), async=True)
