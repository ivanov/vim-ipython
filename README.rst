###########
vim-ipython
###########

A two-way integration between Vim and IPython.

IPython versions 0.11.x, 0.12.x, 0.13.x, 1.x and 2.x

* author: Paul Ivanov (http://pirsquared.org)
* github: http://github.com/ivanov/vim-ipython
* demos: http://pirsquared.org/vim-ipython/
* blogpost: http://pirsquared.org/blog/vim-ipython.html

Using this plugin, you can send lines or whole files for IPython to
execute, and also get back object introspection and word completions in
Vim, like what you get with: ``object?<enter>`` and ``object.<tab>`` in
IPython.

The big change from previous versions of ``ipy.vim`` is that it no longer
requires the old brittle ``ipy_vimserver.py`` instantiation, and since
it uses just vim and python, it is platform independent (i.e. works
even on windows, unlike the previous \*nix only solution). The requirements
are IPython 0.11 or newer with zeromq capabilities, vim compiled with +python.

If you can launch ``ipython qtconsole`` or ``ipython kernel``, and
``:echo has('python')`` returns 1 in vim, you should be good to go.

-----------------
Quickstart Guide:
-----------------
Start ``ipython qtconsole`` [*]_. Source ``ipy.vim`` file, which provides new
IPython command::

  :source ipy.vim
  (or copy it to ~/.vim/ftplugin/python to load automatically)

  :IPython

The ``:IPython`` command allows you to put the full connection string. For
IPython 0.11, it would look like this::

  :IPython --existing --shell=41882 --iopub=43286 --stdin=34987 --hb=36697

and for IPython 0.12 through IPython 2.0 like this::

  :IPython --existing kernel-85997.json

There also exists to convenience commands: ``:IPythonClipboard`` just uses the
``+`` register to get the connection string, whereas ``:IPythonXSelection``
uses the ``*`` register and passes it to ``:IPython``.

**NEW in IPython 2.0**

vim-ipython can now interoperate with non-Python kernels.


**NEW in IPython 0.12**!
Since IPython 0.12, you can simply use::

  :IPython

without arguments to connect to the most recent IPython session (this is the
same as passing just the ``--existing`` flag to ``ipython qtconsole`` and
``ipython console``.

.. [*] Though the demos above use ``qtconsole``, it is not required
    for this workflow, it's just that it was the easiest way to show how to
    make use of the new functionality in 0.11 release. Since IPython 0.12, you
    can use ``ipython kernel`` to create a kernel and get the connection
    string to use for any frontend (including vim-ipython), or use ``ipython
    console`` to create a kernel and immediately connect to it using a
    terminal-based client. You can even connect to an active IPython Notebook
    kernel - just watch for the connection string that gets printed when you
    open the notebook, or use the ``%connect_info`` magic to get the
    connection string.  If you are still using 0.11, you can launch a regular
    kernel using ``python -c "from IPython.zmq.ipkernel import main; main()"``

------------------------
Sending lines to IPython
------------------------
Now type out a line and send it to IPython using ``<Ctrl-S>`` from Command mode::

  import os

You should see a notification message confirming the line was sent, along
with the input number for the line, like so ``In[1]: import os``. If
``<Ctrl-S>`` did **not** work, see the `Known Issues <#known-issues>`_ for a
work-around.

``<Ctrl-S>`` also works from insert mode, but doesn't show notification,
unless ``monitor_subchannel`` is set to ``True`` (see `vim-ipython 'shell'`_,
below)

It also works blockwise in Visual Mode. Select and send these lines using
``<Ctrl-S>``::

  import this,math # secret decoder ring
  a,b,c,d,e,f,g,h,i = range(1,10)
  code =(c,a,d,a,e,i,)
  msg = '...jrer nyy frag sebz Ivz.\nIvz+VClguba=%fyl '+this.s.split()[g]
  decode=lambda x:"\n"+"".join([this.d.get(c,c) for c in x])+"!"
  format=lambda x:'These lines:\n  '+'\n  '.join([l for l in x.splitlines()])
  secret_decoder = lambda a,b: format(a)+decode(msg)%str(b)[:-1]
  '%d'*len(code)%code == str(int(math.pi*1e5))

Then, go to the qtconsole and run this line::

  print secret_decoder(_i,_)

You can also send whole files to IPython's ``%run`` magic using ``<F5>``.

**NEW in IPython 0.12**!
If you're trying to do run code fragments that have leading whitespace, use
``<Alt-S>`` instead - it will dedent a single line, and remove the leading
whitespace of the first line from all lines in a visual mode selection.

-------------------------------
IPython's object? Functionality
-------------------------------

If you're using gvim, mouse-over a variable to see IPython's ``?`` equivalent.
If you're using vim from a terminal, or want to copy something from the
docstring, type ``<leader>d``. ``<leader>`` is usually ``\`` (the backslash
key).  This will open a quickpreview window, which can be closed by hitting
``q`` or ``<escape>``.

--------------------------------------
IPython's tab-completion Functionality
--------------------------------------
vim-ipython activates a 'completefunc' that queries IPython.
A completefunc is activated using ``Ctrl-X Ctrl-U`` in Insert Mode (vim
default). You can combine this functionality with SuperTab to get tab
completion.

-------------------
vim-ipython 'shell'
-------------------

By monitoring km.sub_channel, we can recreate what messages were sent to
IPython, and what IPython sends back in response.

``monitor_subchannel`` is a parameter that sets whether this 'shell' should
updated on every sent command (default: True).

If at any later time you wish to bring this shell up, including if you've set
``monitor_subchannel=False``, hit ``<leader>s``.

**NEW since IPython 0.12**
For local kernels (kernels running on the same machine as vim), `Ctrl-C` in
the vim-ipython 'shell' sends an keyboard interrupt. (Note: this feature may
not work on Windows, please report the issue to ).

-------
Options
-------
You can change these at the top of the ipy.vim::

  reselect = False            # reselect lines after sending from Visual mode
  show_execution_count = True # wait to get numbers for In[43]: feedback?
  monitor_subchannel = True   # update vim-ipython 'shell' on every send?
  run_flags= "-i"             # flags to for IPython's run magic when using <F5>

**Disabling default mappings**
In your own ``.vimrc``, if you don't like the mappings provided by default,
you can define a variable ``let g:ipy_perform_mappings=0`` which will prevent
vim-ipython from defining any of the default mappings.

**NEW since IPython 0.12**
**Making completefunc local to a buffer, or disabling it**
By default, vim-ipython activates the custom completefunc globally.
Sometimes, having a completefunc breaks other plugins' completions. Putting
the line ``let g:ipy_completefunc = 'local'`` in one's vimrc will activate the
IPython-based completion only for current buffer. Setting `g:ipy_completefunc`
to anything other than `'local'` or `'global'` disables it altogether.

**NEW since IPython 0.13**

**Sending ? and ?? now works just like IPython**
This is only supported for single lines that end with ? and ??, which works
just the same as it does in IPython (The ?? variant will show the code, not
just the docstring

**Sending arbitrary signal to IPython kernel**
`:IPythonInterrupt` now supports sending of arbitrary signals. There's a
convenience alias for sending SIGTERM via `:IPythonTerminate`, but you can
also send any signal by just passing an argument to `:IPythonInterrupt`.
Here's an example. First, send this code (or just run it in your kernel)::

    import signal
    def greeting_user(signum, stack):
        import sys
        sys.stdout.flush()
        print "Hello, USER!"
        sys.stdout.flush()
    signal.signal(signal.SIGUSR1, greeting_user)

Now, proceed to connect up using vim-ipython and run `:IPythonInterrupt 10` -
where 10 happens to be signal.SIGUSR1 in the POSIX world. This functionality,
along with the sourcing of profile-dependent code on startup (
``vi `ipython locate profile default`/startup/README`` ), brings the forgotten
world of inter-process communication through signals to your favorite text
editor and REPL combination.


---------------
Known issues:
---------------
- For now, vim-ipython only connects to an ipython session in progress.
- The standard ipython clients (console, qtconsole, notebook) do not currently
  display the result of computation which they did not initialize. This means
  that if you send print statements for execution from within vim, they will
  only be shown inside the vim-ipython shell buffer, but **not** within any of
  the standard clients. This is not a limitation of vim-ipython, but a
  limitation of those built-in clients, see `ipython/ipython#1873
  <https://github.com/ipython/ipython/issues/1873>`_
- The ipdb integration is not yet re-implemented. Pending 
  [IPython PR #3089](https://github.com/ipython/ipython/pull/3089)
- If ``<CTRL-S>`` does not work inside your terminal, but you are able to run
  some of the other commands successfully (``<F5>``, for example), try running
  this command before launching vim in the terminal (add it to your
  ``.bashrc`` if it fixes the issue)::

    stty stop undef # to unmap ctrl-s

- In vim, if you're getting ``ImportError: No module named
  IPython.zmq.blockingkernelmanager`` but are able to import it in regular
  python, **either**

  1. your ``sys.path`` in vim differs from the ``sys.path`` in regular python.
     Try running these two lines, and comparing their output files::

      $ vim -c 'py import vim, sys; vim.current.buffer.append(sys.path)' -c ':wq vim_syspath'
      $ python -c "import sys; f=file('python_syspath','w'); f.write('\n'.join(sys.path)); f.close()"

  **or**

  2. your vim is compiled against a different python than you are launching. See
     if there's a difference between ::

      $ vim -c ':py import os; print os.__file__' -c ':q'
      $ python -c 'import os; print os.__file__'

- For vim inside a terminal, using the arrow keys won't work inside a
  documentation buffer, because the mapping for ``<Esc>`` overlaps with
  ``^[OA`` and so on, and we use ``<Esc>`` as a quick way of closing the
  documentation preview window. If you want go without this quick close
  functionality and want to use the arrow keys instead, look for instructions
  starting with "Known issue: to enable the use of arrow keys..." in the
  ``get_doc_buffer`` function.

- @fholgado's update to ``minibufexpl.vim`` that is up on GitHub will always
  put the cursor in the minibuf after sending a command when
  ``monitor_subchannel`` is set. This is a bug in minibufexpl.vim and the workaround
  is described in vim-ipython issue #7.

- the vim-ipython buffer is set to filetype=python, which provides syntax
  highlighting, but that syntax highlighting will be broken if a stack trace
  is returned which contains one half of a quote delimiter.

- vim-ipython is currently for Python2.X only.

----------------------------
Thanks and Bug Participation
----------------------------
Here's a brief acknowledgment of the folks who have graciously pitched in. If
you've been missed, don't hesitate to contact me, or better yet, submit a
pull request with your attribution.

* @minrk for guiding me through the IPython kernel manager protocol, and
  support of connection_file-based IPython connection (#13), and keeping
  vim-ipython working across IPython API changes.
* @nakamuray and @tcheneau for reporting and providing a fix for when vim is
  compiled without a gui (#1)
* @unpingco for reporting Windows bugs (#3,#4), providing better multiline
  dedenting (#15), and suggesting that a resized vim-ipython shell stays
  resized (#16).
* @simon-b for terminal vim arrow key issue (#5)
* @jorgesca and @kwgoodman for shell update problems (#6)
* @xowlinx and @vladimiroff for Ctrl-S issues in Konsole (#8)
* @zeekay for easily allowing custom mappings (#9)
* @jorgesca for reporting the lack of profile handling capability (#14),
  only open updating 'shell' if it is open (#29)
* @enzbang for removing mapping that's not currently functional (#17)
* @ogrisel  for fixing documentation typo (#19)
* @koepsell for gracefully exiting in case python is not available (#23)
* @mrterry for activating completefunc only after a connection is made (#25),
  Ctrl-C implementation in vim-ipython 'shell' (#28)
* @nonameentername for completion on import statements (#26)
* @dstahlke for setting syntax of doc window to ReST
* @jtratner for docs with quotes (#30)
* @pielgrzym for setting completefunc locally to a buffer (#32)
* @flacjacket for pointing out and providing fix for IPython API change
* @memeplex for fixing the identifier grabbing on e.g. non-PEP8 compliant code
* @pydave for IPythonTerminate (sending SIGTERM using our hack)
* @luispedro for IPythonNew

Similar Projects
----------------
* `vim-slime`_ - Grab some text and "send" it to a GNU Screen / tmux session
  (Jonathan Palardy)
* `screen.vba`_ - Simulate a split shell, using GNU Screen / tmux, that you
  can send commands to (Eric Van Dewoestine)
* `vimux`_ - vim plugin to interact with tmux (Ben Mills)
* `vimux-pyutils`_ - send code to tmux ipython session (Julien Rebetez)
* conque_ - terminal emulator which uses a Vim buffer to display the program
  output (Nico Raffo)
* `ipyqtmacvim`_ - plugin to send commands from MacVim to IPython Qt console
  (Justin Kitzes)
* `tslime_ipython`_ - "cell" execution , with cells defined by marks
* `vipy`_ - used vim-ipython as a starting point and ran with it in a slightly
  different direction. (John David Giese)


.. _vim-slime: https://github.com/jpalardy/vim-slime
.. _screen.vba: https://github.com/ervandew/screen
.. _conque: http://code.google.com/p/conque/
.. _vimux: https://github.com/benmills/vimux
.. _vimux-pyutils: https://github.com/julienr/vimux-pyutils
.. _ipyqtmacvim: https://github.com/jkitzes/ipyqtmacvim/
.. _tslime_ipython: https://github.com/eldridgejm/tslime_ipython
.. _vipy: https://github.com/johndgiese/vipy


Bottom Line
-----------
If you find this project useful, please consider donating money to the
`John Hunter Memorial Fund`_. A giant in our community, John lead by example
and gave us all so much. This is one small way we can give back to his family.

.. _John Hunter Memorial Fund: http://numfocus.org/johnhunter/
