"""

This file is intended to be imported and used inside vim, though some
functions may have general utility outside of a vim context.

TODO:
    [ ] Metadata (notebook name)
    [ ] Header cells
    [X] Markdown cells
    [X] Code cells
    [X] stdout output
    [ ] pyout text
    [ ] richer outputs
        - images:  (take care to replace the doubly-escaped "\\n"
          import base64
          import tempfile
          output = tempfile.NamedTemporaryFile()
          base64.decode(file('/tmp/crazyidea'), output)
    [X] stderr output
    [X] pyerr (tracebacks)
    [ ] another idea - keep the notebook around in memory, and only update the
        cells that are changed, that way we don't have to worry about
        preserving things that don't end up being displayed (like images, rich
        output, etc)
    [ ] au BufReadCmd *.ipynb to automatically parse notebook files
    
Ask Min/Brian:
    [ ] Trailing \r\n
    [ ] stream type for current.new_output()
    [ ] does traceback need to be split into three, or is multiline ok
    [ ] is it cool to not colorize the traceback?
"""
import io
import tempfile
import base64
import re

import vim

from IPython.nbformat import current

# from http://serverfault.com/questions/71285/in-centos-4-4-how-can-i-strip-escape-sequences-from-a-text-file
strip = re.compile('\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]')
def strip_color_escapes(s):
    return strip.sub('',s)

def resize():
    """
    Expand the current window only if the text it contains is larger that its
    current size.
    """
    if int(vim.eval('winheight(0)')) < len(vim.current.buffer):
        vim.command('resize %d'%len(vim.current.buffer))


def resize_and_switch():
    """
    Keep moving the cells around in a circular buffer

    Right now, this implementation is limited to having only 6 windows open at
    a time, but a more intelligent limit that kept track of each buffer's
    height and pulled in more window as they could be visible would be very
    welcome here. I think that would require keeping somewhere in Python a
    mapping between all of the windows and their height, and comparing the sum
    of the visible ones to that of the current height, letting some windows
    'fall off the edge' when the visible windows' combined height exceeds the
    full terminal height
    """
    if vim.current.window == vim.windows[0]:
        #if not vim.current.buffer == vim.buffers[0]:
        vim.command('split|bprev|py resize()')
        vim.command('wincmd j')
        if len(vim.windows) > 6:
            # go to last window and close it
            vim.command('exe 10 . "wincmd w" | wincmd c | exe 2 . "wincmd w"')

    if vim.current.window == vim.windows[-1]:
        vim.command('split|wincmd j|bnext|py resize()')
        vim.command('wincmd k')
        if len(vim.windows) > 6:
            # go to last window and close it
            vim.command('exe 0 . "wincmd w" | wincmd c | exe 5 . "wincmd w"')
    #vim.command('resize %d'%len(vim.current.buffer))
    resize()

def get_cells(fname):
    with io.open(fname, 'r', encoding='utf-8') as f:
        fmt = 'json' if not fname.endswith('.py') else 'py'
        nb = current.read(f, fmt)
    return nb.worksheets[0].cells

vim_encoding=vim.eval('&encoding') or 'utf-8'
def write_to_buffer(b, s):
    del_line0 = False
    if len(b) == 1 and b[0] == '':
        # every vim buffer has at least one line, and if it's blank, then
        # we'll want to delete it after appending `s` later on
        del_line0 = True
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
    if del_line0:
        del b[0]

pnum = 'prompt_number'
def notebook_to_vimbuffers(fname):
    "read an ipython notebook and spit it out as a bunch of vim buffers" 
    cells = get_cells(fname)
    #dir = tempfile.mkdtemp(prefix=fname)
    #vim.command("cd " + dir)
    for i, c in enumerate(cells):
        if c['cell_type'] == 'code':
            in_number = '' if not hasattr(c, pnum) else c[pnum]
            vim.command("e %03d_In[%s]" % (i, in_number))
            vim.command('set buftype=nofile')
            vim.command('set ft=python')
            write_to_buffer(vim.current.buffer, c['input'])
            handle_outputs(c['outputs'], i, in_number)
        if c['cell_type'] == 'markdown':
            vim.command("e %03d.md" % i) # ++ft=python")
            vim.command('set buftype=nofile')
            vim.command('set ft=markdown')
            write_to_buffer(vim.current.buffer, c['source'])
            vim.current.line
    vim.command('brewind')
    vim.command('au BufEnter * :python resize_and_switch()')


def handle_outputs(outputs, i, in_number):
    if len(outputs) == 0:
        return
    for o in outputs:
        if o['output_type'] == 'pyerr':
            vim.command("e %03d_%s_%s" % (i, 'pyerr', o.ename))
            vim.command('set buftype=nofile')
            escapes_removed = strip_color_escapes("\n".join(o.traceback))
            write_to_buffer(vim.current.buffer, escapes_removed)

        if o['output_type'] == 'stream':
            type = o.stream
            vim.command("open %03d_%s[%s]" % (i, type, in_number))
            write_to_buffer(vim.current.buffer, o['text'])
            # XXX: known limitation, multiple outs overwrite each other
            vim.command('set buftype=nofile')

        if o['output_type'] == 'pyout':
            type = 'Out'
            out_or_display(o, i, type, in_number)

        if o['output_type'] == 'display_data':
            type= 'display'
            out_or_display(o, i, type, in_number)

def out_or_display(o, i, type, in_number):
            vim.command("open %03d_%s[%s]" % (i, type, in_number))
            if hasattr(o, 'text'):
                write_to_buffer(vim.current.buffer, o['text'])
            for img_type in ['png', 'jpg']:
                if hasattr(o, img_type):
                    handle_image(vim.current.buffer.name, o[img_type])
            vim.command('set buftype=nofile')

def handle_image(bufname, img_source):
    output = tempfile.NamedTemporaryFile(delete=False)
    input = tempfile.NamedTemporaryFile(prefix=bufname)
    input.file.write(img_source)
    base64.decode(file('/tmp/crazyidea'), output.file)
    vim.command("autocmd BufEnter %s :!qiv %s" % (bufname, output.name))

def write_notebook(filename):
    cells = cells_from_buffers(vim.buffers)
    nb = current.new_notebook(worksheets=[current.new_worksheet()])
    nb.worksheets[0].cells.extend(cells)
    with file(filename, 'w') as f:
        current.write(nb, f, 'json')

def cells_from_buffers(buffers):
    cells = []
    for b in buffers:
        if 'md' in b.name:
            cell = current.new_text_cell('markdown', source="\n".join(b[:]))
            cells.append(cell)
        if 'In' in b.name:
            in_number = b.name[b.name.rindex('[')+1:-1]
            try:
                in_number = int(in_number)
            except ValueError:
                in_number = None
            cell = current.new_code_cell("\n".join(b[:]),
                    prompt_number=in_number)
            cells.append(cell)
        # XXX: Fragile: the sub_cell machinary relies on 'cell' being defined
        # and works so long as the order of buffers preserves the appropriate
        # code cell being immediately adjacent to any of its outputs and
        # errors (This *WILL* be tricky once we allow for re-ordering of
        # cells, but we have to start somewhere)
        if 'pyerr' in b.name:
            # the last line of the traceback is the evalue
            evalue = b[-1][b[-1].index(': ')+2:]
            ename = b.name[b.name.index('pyerr') +len('pyerr') +1:]
            sub_cell = current.new_output('pyerr',
                    traceback=b[:], ename=ename, evalue=evalue)
            cell.outputs.append(sub_cell)
        if 'std' in b.name:
            stream = b.name[b.name.index('std'):b.name.rindex('[')]
            sub_cell = current.new_output('stream', "\n".join(b[:]),
                    prompt_number=in_number)
            # XXX: this is an IPython bug - can't specify stream type to
            # new_output_cell
            sub_cell['stream'] = stream
            cell.outputs.append(sub_cell)
        if 'Out' in b.name:
            sub_cell = current.new_output('pyout', "\n".join(b[:]),
                    prompt_number=in_number)
            cell.outputs.append(sub_cell)
            pass
    return cells
