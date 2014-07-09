
# TODO

This is a list of things I'm planning to work on with vim-ipython

[ ] opening docs while shell buffer is open somehow scroll-locks things, and
    does not compute the proper length

[x] split up vim-specific things from python-specific things 
    (make it easier to become py3k compliant) 

[x] py3k support

[ ] vim ipython magic has no documentation that gets installed (fix this)

[ ] support for non-python kernels (IJulia, IHaskell kernel)

[ ] provide g:ipy variables to set the initial state of python vars 
    e.g. monitor_subchannel

[ ] put debugging support back in
    - http://jacobandreas.github.io/writing/tools/vim-ipython-stack-trace.html
    - example: https://github.com/jacobandreas/vim-ipython

[ ] notebook io branch merged
    ping about this once it lands:
    http://spaceli.wordpress.com/2013/10/04/add-vim-key-bindings-for-ipython-1-0-0/

[x] make it possible to run :IPython command multiple times
    Traceback (most recent call last):
      File "<string>", line 1, in <module>
      File "<string>", line 116, in km_from_string
      File "/home/pi/code/ipython/IPython/kernel/connect.py", line 205, in find_connection_file
        app = IPApp.instance()
      File "/home/pi/code/ipython/IPython/config/configurable.py", line 367, in instance
        '%s are being created.' % cls.__name__
    IPython.config.configurable.MultipleInstanceError: Multiple incompatible subclass instances of BaseIPythonApplication are being created.
    
    - This was actually an IPython limitation. Works fine in IPython rel-2.1.0


[ ] support profiledir
