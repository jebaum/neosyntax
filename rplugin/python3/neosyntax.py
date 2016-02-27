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
        #   precompute entire buffer before doing any add calls, then do them all at once
        #   use cursorholdi instead of textchangedi
        #   still use textchangedi, but also use a timer, and if the highlight is less than X seconds old, don't recompute, just return
        #   in insert mode, only recompute highlight groups on the line, or couple of lines surrounding the cursor
        #   get the viewport of the current window, render that region only or first before the rest of the buffer
        mylexer = pygments.lexers.PythonLexer()
        buf     = self.nvim.buffers[0] # TODO can't hardcode this
        # TODO - can I be more intelligent than doing the whole buffer every time? just the area around a change?
        fullbuf = [line for line in buf] # TODO is this necessary / efficient?

        #  buf.clear_highlight(src_id=1, line_start=0, line_end=-1, async=True)
        addid = 1 if self.srcset else 2
        rmid  = 2 if self.srcset else 1
        self.srcset = not self.srcset
        for linenum, line in enumerate(fullbuf, start=0):
            for (index, tokentype, value) in mylexer.get_tokens_unprocessed(line):
                cols = len(value)
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

                # and another TODO is to map pygments tokens to vim highlight groups, so i don't have to write these all out
                if tokentype == pygments.token.Name.Builtin:
                    buf.add_highlight("Function", line=linenum, col_start=index, col_end=index+cols, src_id=addid, async=True)
                if tokentype == pygments.token.Name.Builtin.Pseudo:
                    buf.add_highlight("Boolean", line=linenum, col_start=index, col_end=index+cols, src_id=addid, async=True)
                elif tokentype == pygments.token.Comment.Single or tokentype == pygments.token.Comment.Hashbang:
                    buf.add_highlight("Comment", line=linenum, col_start=index, col_end=index+cols, src_id=addid, async=True)
                elif tokentype == pygments.token.Keyword.Namespace:
                    buf.add_highlight("Include", line=linenum, col_start=index, col_end=index+cols, src_id=addid, async=True)
                elif tokentype == pygments.token.Literal.Number.Integer:
                    buf.add_highlight("Number", line=linenum, col_start=index, col_end=index+cols, src_id=addid, async=True)
                elif tokentype == pygments.token.Literal.String.Single or tokentype == pygments.token.Literal.String.Double:
                    buf.add_highlight("String", line=linenum, col_start=index, col_end=index+cols, src_id=addid, async=True)
                elif tokentype == pygments.token.Keyword or tokentype == pygments.token.Operator.Word:
                    buf.add_highlight("Conditional", line=linenum, col_start=index, col_end=index+cols, src_id=addid, async=True)

        buf.clear_highlight(src_id=rmid, line_start=0, line_end=len(fullbuf), async=True)

