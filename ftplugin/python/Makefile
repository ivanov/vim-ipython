test:
	vim -c 'py from vim_ipython_notebook import *; notebook_to_vimbuffers("tmp.ipynb");' -c"sunhide 6"

diff: 
	vim -c 'py import vim_ipython_notebook as v; resize=v.resize; v.notebook_to_vimbuffers("tmp.ipynb"); v.write_notebook("new.ipynb")' -c':q!'
	vimdiff new.ipynb tmp.ipynb

