reselect = False            # reselect lines after sending from Visual mode
show_execution_count = True # wait to get numbers for In[43]: feedback?
monitor_subchannel = True   # update vim-ipython 'shell' on every send?
run_flags= "-i"             # flags to for IPython's run magic when using <F5>
current_line = ''

try:
    from queue import Empty # python3 convention
except ImportError:
    from Queue import Empty

try:
    import vim
except ImportError:
    class NoOp(object):
        def __getattribute__(self, key):
            return lambda *args: '0'
    vim = NoOp()
    print("uh oh, not running inside vim")

import sys

# get around unicode problems when interfacing with vim
vim_encoding=vim.eval('&encoding') or 'utf-8'

try:
    sys.stdout.flush
except AttributeError:
    # IPython complains if stderr and stdout don't have flush
    # this is fixed in newer version of Vim
    class WithFlush(object):
        def __init__(self,noflush):
            self.write=noflush.write
            self.writelines=noflush.writelines
        def flush(self):pass
    sys.stdout = WithFlush(sys.stdout)
    sys.stderr = WithFlush(sys.stderr)

def vim_variable(name, default=None):
    exists = int(vim.eval("exists('%s')" % name))
    return vim.eval(name) if exists else default
 
def vim_regex_escape(x):
    for old, new in (("[", "\\["), ("]", "\\]"), (":", "\\:"), (".", "\."), ("*", "\\*")):
        x = x.replace(old, new)
    return x

# status buffer settings
status_prompt_in = vim_variable('g:ipy_status_in', 'In [%(line)d]: ')
status_prompt_out = vim_variable('g:ipy_status_out', 'Out[%(line)d]: ')

status_prompt_colors = {
    'in_ctermfg': vim_variable('g:ipy_status_in_console_color', 'Green'),
    'in_guifg': vim_variable('g:ipy_status_in_gui_color', 'Green'),
    'out_ctermfg': vim_variable('g:ipy_status_out_console_color', 'Red'),
    'out_guifg': vim_variable('g:ipy_status_out_gui_color', 'Red'),
    'out2_ctermfg': vim_variable('g:ipy_status_out2_console_color', 'Gray'),
    'out2_guifg': vim_variable('g:ipy_status_out2_gui_color', 'Gray'),
}

status_blank_lines = int(vim_variable('g:ipy_status_blank_lines', '1'))


ip = '127.0.0.1'
# this allows us to load vim_ipython multiple times
try:
    km
    kc
    pid
except NameError:
    km = None
    kc = None
    pid = None

_install_instructions = """You *must* install IPython into the Python that
your vim is linked against. If you are seeing this message, this usually means
either (1) installing IPython using the system Python that vim is using, or
(2) recompiling Vim against the Python where you already have IPython
installed. This is only a requirement to allow Vim to speak with an IPython
instance using IPython's own machinery. It does *not* mean that the IPython
instance with which you communicate via vim-ipython needs to be running the
same version of Python.
"""

def new_ipy(s=''):
    """Create a new IPython kernel (optionally with extra arguments)

    XXX: Allow passing of profile information here

    Examples
    --------

        new_ipy()

    """
    from IPython.kernel import KernelManager
    km = KernelManager()
    km.start_kernel()
    return km_from_string(km.connection_file)

def km_from_string(s=''):
    """create kernel manager from IPKernelApp string
    such as '--shell=47378 --iopub=39859 --stdin=36778 --hb=52668' for IPython 0.11
    or just 'kernel-12345.json' for IPython 0.12
    """
    try:
        import IPython
    except ImportError:
        raise ImportError("Could not find IPython. " + _install_instructions)
    from IPython.config.loader import KeyValueConfigLoader
    try:
        from IPython.kernel import (
            KernelManager,
            find_connection_file,
        )
    except ImportError:
        #  IPython < 1.0
        from IPython.zmq.blockingkernelmanager import BlockingKernelManager as KernelManager
        from IPython.zmq.kernelapp import kernel_aliases
        try:
            from IPython.lib.kernel import find_connection_file
        except ImportError:
            # < 0.12, no find_connection_file
            pass
        
    global km, kc, send

    s = s.replace('--existing', '')
    if 'connection_file' in KernelManager.class_trait_names():
        # 0.12 uses files instead of a collection of ports
        # include default IPython search path
        # filefind also allows for absolute paths, in which case the search
        # is ignored
        try:
            # XXX: the following approach will be brittle, depending on what
            # connection strings will end up looking like in the future, and
            # whether or not they are allowed to have spaces. I'll have to sync
            # up with the IPython team to address these issues -pi
            if '--profile' in s:
                k,p = s.split('--profile')
                k = k.lstrip().rstrip() # kernel part of the string
                p = p.lstrip().rstrip() # profile part of the string
                fullpath = find_connection_file(k,p)
            else:
                fullpath = find_connection_file(s.lstrip().rstrip())
        except IOError as e:
            echo(":IPython " + s + " failed", "Info")
            echo("^-- failed '" + s + "' not found", "Error")
            return
        km = KernelManager(connection_file = fullpath)
        km.load_connection_file()
    else:
        if s == '':
            echo(":IPython 0.11 requires the full connection string")
            return
        loader = KeyValueConfigLoader(s.split(), aliases=kernel_aliases)
        cfg = loader.load_config()['KernelApp']
        try:
            km = KernelManager(
                shell_address=(ip, cfg['shell_port']),
                sub_address=(ip, cfg['iopub_port']),
                stdin_address=(ip, cfg['stdin_port']),
                hb_address=(ip, cfg['hb_port']))
        except KeyError as e:
            echo(":IPython " +s + " failed", "Info")
            echo("^-- failed --"+e.message.replace('_port','')+" not specified", "Error")
            return

    try:
        kc = km.client()
    except AttributeError:
        # 0.13
        kc = km
    kc.start_channels()
    send = kc.shell_channel.execute

    #XXX: backwards compatibility for IPython < 0.13
    import inspect
    sc = kc.shell_channel
    num_oinfo_args = len(inspect.getargspec(sc.object_info).args)
    if num_oinfo_args == 2:
        # patch the object_info method which used to only take one argument
        klass = sc.__class__
        klass._oinfo_orig = klass.object_info
        klass.object_info = lambda s,x,y: s._oinfo_orig(x)
    
    #XXX: backwards compatibility for IPython < 1.0
    if not hasattr(kc, 'iopub_channel'):
        kc.iopub_channel = kc.sub_channel

    # now that we're connect to an ipython kernel, activate completion
    # machinery, but do so only for the local buffer if the user added the
    # following line the vimrc:
    #   let g:ipy_completefunc = 'local'
    vim.command("""
        if g:ipy_completefunc == 'global'
            set completefunc=CompleteIPython
        elseif g:ipy_completefunc == 'local'
            setl completefunc=CompleteIPython
        endif
        """)
    # also activate GUI doc balloons if in gvim
    vim.command("""
        if has('balloon_eval')
            set bexpr=IPythonBalloonExpr()
        endif
        """)
    set_pid()
    return km

def echo(arg,style="Question"):
    try:
        vim.command("echohl %s" % style)
        vim.command("echom \"%s\"" % arg.replace('\"','\\\"'))
        vim.command("echohl None")
    except vim.error:
        print("-- %s" % arg)

def disconnect():
    "disconnect kernel manager"
    # XXX: make a prompt here if this km owns the kernel
    pass

def get_doc(word, level=0):
    if kc is None:
        return ["Not connected to IPython, cannot query: %s" % word]
    msg_id = kc.shell_channel.object_info(word, level)
    doc = get_doc_msg(msg_id)
    # get around unicode problems when interfacing with vim
    return [d.encode(vim_encoding) for d in doc]

import re
# from http://serverfault.com/questions/71285/in-centos-4-4-how-can-i-strip-escape-sequences-from-a-text-file
strip = re.compile('\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]')
def strip_color_escapes(s):
    return strip.sub('',s)

def get_doc_msg(msg_id):
    n = 13 # longest field name (empirically)
    b=[]
    try:
        content = get_child_msg(msg_id)['content']
    except Empty:
        # timeout occurred
        return ["no reply from IPython kernel"]

    if not content['found']:
        return b

    for field in ['type_name','base_class','string_form','namespace',
            'file','length','definition','source','docstring']:
        c = content.get(field,None)
        if c:
            if field in ['definition']:
                c = strip_color_escapes(c).rstrip()
            s = field.replace('_',' ').title()+':'
            s = s.ljust(n)
            if c.find('\n')==-1:
                b.append(s+c)
            else:
                b.append(s)
                b.extend(c.splitlines())
    return b

def get_doc_buffer(level=0):
    # empty string in case vim.eval return None
    vim.command("let isk_save = &isk") # save iskeyword list
    vim.command("let &isk = '@,48-57,_,192-255,.'")
    word = vim.eval('expand("<cword>")') or ''
    vim.command("let &isk = isk_save") # restore iskeyword list
    doc = get_doc(word, level)
    if len(doc) ==0:
        echo(repr(word)+" not found","Error")
        return
    # documentation buffer name is same as the query made to ipython
    vim.command('new '+word)
    vim.command('setlocal modifiable noro')
    # doc window quick quit keys: 'q' and 'escape'
    vim.command('nnoremap <buffer> q :q<CR>')
    # Known issue: to enable the use of arrow keys inside the terminal when
    # viewing the documentation, comment out the next line
    vim.command('nnoremap <buffer> <Esc> :q<CR>')
    # and uncomment this line (which will work if you have a timoutlen set)
    #vim.command('nnoremap <buffer> <Esc><Esc> :q<CR>')
    b = vim.current.buffer
    b[:] = None
    b[:] = doc
    vim.command('setlocal nomodified bufhidden=wipe')
    #vim.command('setlocal previewwindow nomodifiable nomodified ro')
    #vim.command('set previewheight=%d'%len(b))# go to previous window
    vim.command('resize %d'%len(b))
    #vim.command('pcl')
    #vim.command('pedit doc')
    #vim.command('normal! ') # go to previous window
    if level == 0:
        # use the ReST formatting that ships with stock vim
        vim.command('setlocal syntax=rst')
    else:
        # use Python syntax highlighting
        vim.command('setlocal syntax=python')

def ipy_complete(base, current_line, pos):
    msg_id = kc.shell_channel.complete(base, current_line, pos)
    try:
        m = get_child_msg(msg_id)
        matches = m['content']['matches']
        matches.insert(0,base) # the "no completion" version
        # we need to be careful with unicode, because we can have unicode
        # completions for filenames (for the %run magic, for example). So the next
        # line will fail on those:
        #completions= [str(u) for u in matches]
        # because str() won't work for non-ascii characters
        # and we also have problems with unicode in vim, hence the following:
        return matches
    except Empty:
        echo("no reply from IPython kernel")
        return ['']

def vim_ipython_is_open():
    """
    Helper function to let us know if the vim-ipython shell is currently
    visible
    """
    for w in vim.windows:
        if w.buffer.name is not None and w.buffer.name.endswith("vim-ipython"):
            return True
    return False

def update_subchannel_msgs(debug=False, force=False):
    """
    Grab any pending messages and place them inside the vim-ipython shell.
    This function will do nothing if the vim-ipython shell is not visible,
    unless force=True argument is passed.
    """
    if kc is None or (not vim_ipython_is_open() and not force):
        return False
    msgs = kc.iopub_channel.get_msgs()
    b = vim.current.buffer
    startedin_vimipython = vim.eval('@%')=='vim-ipython'
    if not startedin_vimipython:
        # switch to preview window
        vim.command(
            "try"
            "|silent! wincmd P"
            "|catch /^Vim\%((\a\+)\)\=:E441/"
            "|silent pedit +set\ ma vim-ipython"
            "|silent! wincmd P"
            "|endtry")
        # if the current window is called 'vim-ipython'
        if vim.eval('@%')=='vim-ipython':
            # set the preview window height to the current height
            vim.command("set pvh=" + vim.eval('winheight(0)'))
        else:
            # close preview window, it was something other than 'vim-ipython'
            vim.command("pcl")
            vim.command("silent pedit +set\ ma vim-ipython")
            vim.command("wincmd P") #switch to preview window
            # subchannel window quick quit key 'q'
            vim.command('nnoremap <buffer> q :q<CR>')
            vim.command("set bufhidden=hide buftype=nofile ft=python")
            vim.command("setlocal nobuflisted") # don't come up in buffer lists
            vim.command("setlocal nonumber") # no line numbers, we have in/out nums
            vim.command("setlocal noswapfile") # no swap file (so no complaints cross-instance)
            # make shift-enter and control-enter in insert mode behave same as in ipython notebook
            # shift-enter send the current line, control-enter send the line
            # but keeps it around for further editing.
            vim.command("inoremap <buffer> <s-Enter> <esc>dd:python run_command('''<C-r>\"''')<CR>i")
            # pkddA: paste, go up one line which is blank after run_command,
            # delete it, and then back to insert mode
            vim.command("inoremap <buffer> <c-Enter> <esc>dd:python run_command('''<C-r>\"''')<CR>pkddA")
            # ctrl-C gets sent to the IPython process as a signal on POSIX
            vim.command("noremap <buffer>  :IPythonInterrupt<cr>")

    #syntax highlighting for python prompt
    # QtConsole In[] is blue, but I prefer the oldschool green
    # since it makes the vim-ipython 'shell' look like the holidays!
    colors = status_prompt_colors
    vim.command("hi IPyPromptIn ctermfg=%s guifg=%s" % (colors['in_ctermfg'], colors['in_guifg']))
    vim.command("hi IPyPromptOut ctermfg=%s guifg=%s" % (colors['out_ctermfg'], colors['out_guifg']))
    vim.command("hi IPyPromptOut2 ctermfg=%s guifg=%s" % (colors['out2_ctermfg'], colors['out2_guifg']))
    in_expression = vim_regex_escape(status_prompt_in % {'line': 999}).replace('999', '[ 0-9]*')
    vim.command("syn match IPyPromptIn /^%s/" % in_expression)
    out_expression = vim_regex_escape(status_prompt_out % {'line': 999}).replace('999', '[ 0-9]*')
    vim.command("syn match IPyPromptOut /^%s/" % out_expression)
    vim.command("syn match IPyPromptOut2 /^\\.\\.\\.* /")
    b = vim.current.buffer
    update_occured = False
    for m in msgs:
        s = ''
        if 'msg_type' not in m['header']:
            # debug information
            #echo('skipping a message on sub_channel','WarningMsg')
            #echo(str(m))
            continue
        header = m['header']['msg_type']
        if header == 'status':
            continue
        elif header == 'stream':
            # TODO: alllow for distinguishing between stdout and stderr (using
            # custom syntax markers in the vim-ipython buffer perhaps), or by
            # also echoing the message to the status bar
            s = strip_color_escapes(m['content']['data'])
        elif header == 'pyout':
            s = status_prompt_out % {'line': m['content']['execution_count']}
            s += m['content']['data']['text/plain']
        elif header == 'display_data':
            # TODO: handle other display data types (HMTL? images?)
            s += m['content']['data']['text/plain']
        elif header == 'pyin':
            # TODO: the next line allows us to resend a line to ipython if
            # %doctest_mode is on. In the future, IPython will send the
            # execution_count on subchannel, so this will need to be updated
            # once that happens
            line_number = m['content'].get('execution_count', 0)
            prompt = status_prompt_in % {'line': line_number}
            s = prompt
            # add a continuation line (with trailing spaces if the prompt has them)
            dots = '.' * len(prompt.rstrip())
            dots += prompt[len(prompt.rstrip()):]
            s += m['content']['code'].rstrip().replace('\n', '\n' + dots)
        elif header == 'pyerr':
            c = m['content']
            s = "\n".join(map(strip_color_escapes,c['traceback']))
            s += c['ename'] + ":" + c['evalue']

        if s.find('\n') == -1:
            # somewhat ugly unicode workaround from 
            # http://vim.1045645.n5.nabble.com/Limitations-of-vim-python-interface-with-respect-to-character-encodings-td1223881.html
            if isinstance(s,unicode):
                s=s.encode(vim_encoding)
            b.append(s)
        else:
            try:
                b.append(s.splitlines())
            except:
                b.append([l.encode(vim_encoding) for l in s.splitlines()])
        update_occured = True
    # make a newline so we can just start typing there
    if status_blank_lines:
        if b[-1] != '':
            b.append([''])
    if update_occured or force:
        vim.command('normal! G') # go to the end of the file
    if not startedin_vimipython:
        vim.command('normal! p') # go back to where you were
    return update_occured
    
def get_child_msg(msg_id):
    # XXX: message handling should be split into its own process in the future
    while True:
        # get_msg will raise with Empty exception if no messages arrive in 1 second
        m = kc.shell_channel.get_msg(timeout=1)
        if m['parent_header']['msg_id'] == msg_id:
            break
        else:
            #got a message, but not the one we were looking for
            echo('skipping a message on shell_channel','WarningMsg')
    return m
            
def print_prompt(prompt,msg_id=None):
    """Print In[] or In[42] style messages"""
    global show_execution_count
    if show_execution_count and msg_id:
        # wait to get message back from kernel
        try:
            child = get_child_msg(msg_id)
            count = child['content']['execution_count']
            echo("In[%d]: %s" %(count,prompt))
        except Empty:
            echo("In[]: %s (no reply from IPython kernel)" % prompt)
    else:
        echo("In[]: %s" % prompt)

def with_subchannel(f,*args):
    "conditionally monitor subchannel"
    def f_with_update(*args):
        try:
            f(*args)
            if monitor_subchannel:
                update_subchannel_msgs(force=True)
        except AttributeError: #if kc is None
            echo("not connected to IPython", 'Error')
    return f_with_update

@with_subchannel
def run_this_file():
    msg_id = send('%%run %s %s' % (run_flags, repr(vim.current.buffer.name),))
    print_prompt("In[]: %%run %s %s" % (run_flags, repr(vim.current.buffer.name)),msg_id)

@with_subchannel
def run_this_line(dedent=False):
    line = vim.current.line
    if dedent:
        line = line.lstrip()
    if line.rstrip().endswith('?'):
        # intercept question mark queries -- move to the word just before the
        # question mark and call the get_doc_buffer on it
        w = vim.current.window
        original_pos =  w.cursor
        new_pos = (original_pos[0], vim.current.line.index('?')-1)
        w.cursor = new_pos
        if line.rstrip().endswith('??'):
            # double question mark should display source
            # XXX: it's not clear what level=2 is for, level=1 is sufficient
            # to get the code -- follow up with IPython team on this
            get_doc_buffer(1)
        else:
            get_doc_buffer()
        # leave insert mode, so we're in command mode
        vim.command('stopi')
        w.cursor = original_pos
        return
    msg_id = send(line)
    print_prompt(line, msg_id)

@with_subchannel
def run_command(cmd):
    msg_id = send(cmd)
    print_prompt(cmd, msg_id)

@with_subchannel
def run_these_lines(dedent=False):
    r = vim.current.range
    if dedent:
        lines = list(vim.current.buffer[r.start:r.end+1])
        nonempty_lines = [x for x in lines if x.strip()]
        if not nonempty_lines:
            return
        first_nonempty = nonempty_lines[0]
        leading = len(first_nonempty) - len(first_nonempty.lstrip())
        lines = "\n".join(x[leading:] for x in lines)
    else:
        lines = "\n".join(vim.current.buffer[r.start:r.end+1])
    msg_id = send(lines)
    #alternative way of doing this in more recent versions of ipython
    #but %paste only works on the local machine
    #vim.command("\"*yy")
    #send("'%paste')")
    #reselect the previously highlighted block
    vim.command("normal! gv")
    if not reselect:
        vim.command("normal! ")

    #vim lines start with 1
    #print("lines %d-%d sent to ipython"% (r.start+1,r.end+1))
    prompt = "lines %d-%d "% (r.start+1,r.end+1)
    print_prompt(prompt,msg_id)


def set_pid():
    """
    Explicitly ask the ipython kernel for its pid
    """
    global pid
    lines = '\n'.join(['import os', '_pid = os.getpid()'])
    msg_id = send(lines, silent=True, user_variables=['_pid'])

    # wait to get message back from kernel
    try:
        child = get_child_msg(msg_id)
    except Empty:
        echo("no reply from IPython kernel")
        return
    try:
        pid = int(child['content']['user_variables']['_pid'])
    except TypeError: # change in IPython 1.0.dev moved this out
        pid = int(child['content']['user_variables']['_pid']['data']['text/plain'])
    except KeyError: # change in IPython 1.0.dev moved this out
        echo("Could not get PID information, kernel not running Python?")
    return pid


def terminate_kernel_hack():
    "Send SIGTERM to our the IPython kernel"
    import signal
    interrupt_kernel_hack(signal.SIGTERM)

def interrupt_kernel_hack(signal_to_send=None):
    """
    Sends the interrupt signal to the remote kernel.  This side steps the
    (non-functional) ipython interrupt mechanisms.
    Only works on posix.
    """
    global pid
    import signal
    import os
    if pid is None:
        # Avoid errors if we couldn't get pid originally,
        # by trying to obtain it now
        pid = set_pid()

        if pid is None:
            echo("cannot get kernel PID, Ctrl-C will not be supported")
            return
    if not signal_to_send:
        signal_to_send = signal.SIGINT

    echo("KeyboardInterrupt (sent to ipython: pid " +
        "%i with signal %s)" % (pid, signal_to_send),"Operator")
    try:
        os.kill(pid, int(signal_to_send))
    except OSError:
        echo("unable to kill pid %d" % pid)
        pid = None

def dedent_run_this_line():
    run_this_line(True)

def dedent_run_these_lines():
    run_these_lines(True)
    
#def set_this_line():
#    # not sure if there's a way to do this, since we have multiple clients
#    send("get_ipython().shell.set_next_input(\'%s\')" % vim.current.line.replace("\'","\\\'"))
#    #print("line \'%s\' set at ipython prompt"% vim.current.line)
#    echo("line \'%s\' set at ipython prompt"% vim.current.line,'Statement')


def toggle_reselect():
    global reselect
    reselect=not reselect
    print("F9 will%sreselect lines after sending to ipython" %
            (reselect and " " or " not "))

#def set_breakpoint():
#    send("__IP.InteractiveTB.pdb.set_break('%s',%d)" % (vim.current.buffer.name,
#                                                        vim.current.window.cursor[0]))
#    print("set breakpoint in %s:%d"% (vim.current.buffer.name, 
#                                      vim.current.window.cursor[0]))
#    
#def clear_breakpoint():
#    send("__IP.InteractiveTB.pdb.clear_break('%s',%d)" % (vim.current.buffer.name,
#                                                          vim.current.window.cursor[0]))
#    print("clearing breakpoint in %s:%d" % (vim.current.buffer.name,
#                                            vim.current.window.cursor[0]))
#
#def clear_all_breakpoints():
#    send("__IP.InteractiveTB.pdb.clear_all_breaks()");
#    print("clearing all breakpoints")
#
#def run_this_file_pdb():
#    send(' __IP.InteractiveTB.pdb.run(\'execfile("%s")\')' % (vim.current.buffer.name,))
#    #send('run -d %s' % (vim.current.buffer.name,))
#    echo("In[]: run -d %s (using pdb)" % vim.current.buffer.name)

