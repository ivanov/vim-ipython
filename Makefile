test: 
	vim -N -c 'Vader! test/*'\
		-c 'if !exists("g:loaded_vader")'\
		-c 'echo "ERROR:  vim-ipython needs Vader to run the test suite\n\n"'\
		-c 'echo "Vader installtion instructions:\n"'\
		-c 'echo "\n    https://github.com/junegunn/vader.vim#installation  "'\
		-c 'echo "\nIf you are using Pathogen:\n\n"'\
		-c 'echo "    git clone https://github.com/junegunn/vader.vim.git ~/.vim/bundle/vader.vim"'\
		-c 'exit endif'

.PHONY: test
