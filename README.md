# Neosyntax
Neovim remote plugin to do syntax highlighting in a separate process using pygments

### Current development procedure
I have a file called `nvim.py` that I'm using as a test python file to see how the highlighting works.

Start up a tmux session, which by default should have its pane identifier be "0:1.1", assuming no other tmux windows are open (this may also vary with your tmux config).

Inside this window, run
`while true; do NVIM_LISTEN_ADDRESS=/tmp/nvim nvim nvim.py; done`

Add these autocommands to your `init.vim`:

```
augroup Neosyntax
    autocmd!
    autocmd VimLeavePre * UpdateRemotePlugins
    autocmd BufEnter nvim.py syntax off | HighlightBuffer
    autocmd BufWritePost neosyntax.py call system("tmux send-keys -t '0:1.1' 'ZQ'")
augroup END
```
Open up `neosyntax.py` from this plugin, and whenever you write to it, the neovim instance with the `nvim.py` test file open should run `:UpdateRemotePlugins`, quit, reopen, and then run `:HighlightBuffer`, which currently is the command that will highlight the file using pygments. This allows for very quick and easy debugging.

`connect.sh` will open up an `ipython3` console that automatically loads pygments and connects to a neovim instance listening to a socket at `/tmp/nvim`. This is useful for quickly testing out the API.

`printtokens.py` takes one filename as an argument, and will print out the tokens found in the file.
