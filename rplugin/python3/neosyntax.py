import neovim
# TODO figure out the python way to do these imports, this is probably wrong
import pygments
import pygments.lexers
import pygments.token

@neovim.plugin

class Neosyntax(object):
    def __init__(self, nvim):
        self.nvim = nvim

    @neovim.function('HighlightBuffer', sync=False)
    def highlight_buffer(self, args):
        mylexer = pygments.lexers.PythonLexer()
        buf     = self.nvim.buffers[0] # TODO can't hardcode this
        fullbuf = [line for line in buf] # TODO is this necessary / efficient?

        # TODO need to subscribe to appropriate events (TextChanged[I]?) to run this function as needed
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

                # another TODO is to figure out what exactly a src_id is, and whether I need to use it
                if tokentype == pygments.token.Name.Builtin:
                    buf.add_highlight("Function", line=linenum, col_start=index, col_end=index+cols, src_id=1, async=True)
                elif tokentype == pygments.token.Comment.Single or tokentype == pygments.token.Comment.Hashbang:
                    buf.add_highlight("Comment", line=linenum, col_start=index, col_end=index+cols, src_id=1, async=True)
                elif tokentype == pygments.token.Keyword.Namespace:
                    buf.add_highlight("Include", line=linenum, col_start=index, col_end=index+cols, src_id=4, async=True)
                elif tokentype == pygments.token.Literal.Number.Integer:
                    buf.add_highlight("Number", line=linenum, col_start=index, col_end=index+cols, src_id=5, async=True)
                elif tokentype == pygments.token.Literal.String.Single:
                    buf.add_highlight("String", line=linenum, col_start=index, col_end=index+cols, src_id=6, async=True)
                elif tokentype == pygments.token.Keyword or tokentype == pygments.token.Operator.Word:
                    buf.add_highlight("Operator", line=linenum, col_start=index, col_end=index+cols, src_id=7, async=True)
