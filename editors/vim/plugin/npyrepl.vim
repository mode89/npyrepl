if !has("python3")
    echo "vim has to be compiled with +python3 to run npyrepl plugin"
    finish
endif

if exists('g:npyrepl_plugin_loaded')
    finish
endif

let s:plugin_root_dir = fnamemodify(resolve(expand('<sfile>:p')), ':h')

python3 << EOF
import sys
from os.path import normpath, join
import vim
plugin_root_dir = vim.eval('s:plugin_root_dir')
python_root_dir = normpath(join(plugin_root_dir, '..', 'python'))
sys.path.insert(0, python_root_dir)
import npyrepl_vim
EOF

let g:npyrepl_plugin_loaded = 1

command! -nargs=* NpyreplConnect python3 npyrepl_vim.connect(<f-args>)
command! -nargs=0 NpyreplDisconnect python3 npyrepl_vim.disconnect()

function! npyrepl#Eval(expr)
    python3 npyrepl_vim.eval_code(vim.eval("a:expr"))
endfunction

command! -nargs=1 NpyreplEval call npyrepl#Eval(<q-args>)

function! npyrepl#EvalLines() range
    execute a:firstline . "," . a:lastline .
        \ "python3 npyrepl_vim.eval_lines()"
endfunction

command! -range NpyreplEvalLines <line1>,<line2>call npyrepl#EvalLines()

command! NpyreplEvalBuffer python3 npyrepl_vim.eval_buffer()
command! NpyreplEvalGlobalFunction python3 npyrepl_vim.eval_global_function()

function! npyrepl#Namespace(name=v:null)
    python3 npyrepl_vim.namespace(vim.eval("a:name"))
endfunction

command! -nargs=* NpyreplNamespace call npyrepl#Namespace(<f-args>)
