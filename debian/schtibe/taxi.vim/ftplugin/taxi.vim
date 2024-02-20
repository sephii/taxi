" Set the omnifunc to be able to complete the aliases via <ctrl-x> <ctrl-o>
set omnifunc=TaxiAliases
set completeopt+=longest
let s:pat = '^\([a-zA-Z0-9_\-?]\+\)\s\+\([0-9:?-]\+\)\s\+\(.*\)$'
" TODO is this a good cache location?
let s:cache_file = $HOME."/.local/share/taxi/taxi_aliases"

autocmd BufNewFile,BufRead *.tks :call TaxiAssmbleAliases()
autocmd BufWritePost *.tks :call s:taxi_balance()
autocmd QuitPre      <buffer> :call s:taxi_balance_close()
autocmd BufWritePre  *.tks :call TaxiFormatFile()
autocmd InsertEnter  <buffer> :call TaxiInsertEnter()

let s:cached_aliases = []
let s:updated_aliases = []
let s:is_closing = 0

" TODO i wonder if all the hassle with adding and removing the element from
" our local cache is worth it, or if we should just replace the entire array
" with the data from the update. On the other hand, if there's an ongoing
" completion, sweeping away the alias list might be weird for the UX 
fun! s:nvim_process_aliases(job_id, data, event)
    call s:parse_updated_aliases(a:data)
endfun


fun! s:vim_process_aliases(channel, msg)
    let aliases = split(a:msg, "\n")
    call s:parse_updated_aliases(aliases)
endfun

" Parse the aliases from the taxi command, save them into a 
" intermediate list for further processing
fun! s:parse_updated_aliases(data)
    for alias in a:data
        if alias != ''
            let parts = split(alias)
            if len(parts) > 2
                let alias = parts[1]
                let text = join(parts[3:], ' ')
                let value = [alias, text]

                call add(s:updated_aliases, value)

            endif
        endif
    endfor
endfun

" Remove the aliases from our list that aren't in the taxi command anymore
fun! s:remove_removed_aliases()
    for alias in s:cached_aliases
        if index(s:updated_aliases, alias) == -1
            let pos = index(s:cached_aliases, alias)
            call remove(s:cached_aliases, pos)
        endif
    endfor
endfun

" Add the new aliases from the taxi command to our list
fun! s:add_new_aliases()
    let aliases = deepcopy(s:cached_aliases)
    for alias in s:updated_aliases
        if index(aliases, alias) == -1
            call add(aliases, alias)
        endif
    endfor

    let s:cached_aliases = aliases
endfun

" Process the aliases after they've been collected from the command
" It's essential that this is called after the taxi alias output is 
" being processed, because in vim the function _add_new_aliases_ returns 
" several times when it's running and outputting
fun! s:process_aliases(...)
    call s:add_new_aliases()
    call s:remove_removed_aliases()
    call s:cache_aliases()
endfun

" Write the aliases to the cache file
fun! s:cache_aliases()
    let cache_aliases = []
    for alias in s:cached_aliases
        call add(cache_aliases, join(alias, "|"))
    endfor
    let directory = fnamemodify(s:cache_file, ":p:h")
    if !isdirectory(directory)
        call mkdir(directory)
    endif
    call writefile(cache_aliases,  s:cache_file)
endfun

" Callback for the background process of updating the aliases for nvim
fun! s:nvim_update_handler(job_id, data, event) dict
    let alias_callbacks = {
                \ 'on_stdout': function('s:nvim_process_aliases'),
                \ 'on_exit': function('s:process_aliases')
                \ }
    " When taxi update is done, run taxi alias
    call jobstart(['taxi', 'alias', 'list', '--no-inactive'], alias_callbacks)
endfun

" Callback for the background process of updating the aliases for vim
fun! s:vim_update_handler(channel, msg)
    let alias_callbacks = {
                \ 'out_cb': function('s:vim_process_aliases'),
                \ 'exit_cb': function('s:process_aliases')
                \ }
    call job_start(['taxi', 'alias', 'list', '--no-inactive'], alias_callbacks)
endfun

" Read the aliases from the cache file
fun! s:taxi_read_aliases()
    if filereadable(s:cache_file)
        let s:cached_aliases = []
        let cached_aliases = readfile(s:cache_file)
        for alias in cached_aliases
            let parts = split(alias, "|")
            if len(parts) > 1
                call add(s:cached_aliases, [parts[0], parts[1]])
            endif
        endfor
    endif
endfun

" Assemble the aliases
" On one hand this reads the cache file for speed, on the other hand
" it calls a background process which updates the aliases from zebra
fun! TaxiAssmbleAliases()
    call s:taxi_read_aliases()
    " Run the taxi update
    if has('nvim')
        let s:update_callbacks = {
                    \    'on_exit': function('s:nvim_update_handler')
                    \ }

        call jobstart(['taxi', 'update'], s:update_callbacks)
    else
        let s:update_callbacks = {
                    \    'exit_cb': function('s:vim_update_handler')
                    \ }

        call job_start(['taxi', 'update'], s:update_callbacks)
    endif
endfun


fun! TaxiAliases(findstart, base)
    " Complete string under the cursor to the aliases available in taxi
    if a:findstart
        let line = getline('.')
        let start = col('.') - 1
        while start > 0 && line[start - 1 ] =~ '\w'
            let start -= 1
        endwhile
        return start
    else
        let res = []
        for alias in s:cached_aliases
            if alias[0] =~ '^' . a:base
                call add(res, { 'word': alias[0], 'menu': alias[1] })
            endif
        endfor
        return res
    endif
endfun


fun! s:taxi_balance()
    " Create a scratch window below that contains the total line
    " of the taxi balance output
    if s:is_closing
        return
    endif

    let winnr = bufwinnr('^_taxibalance$')
    if ( winnr >  0 )
        execute winnr . 'wincmd w'
        execute 'normal ggdG'
    else
        setl splitbelow
        7new _taxibalance
        setlocal buftype=nofile bufhidden=wipe nobuflisted noswapfile nowrap
    endif

    let result = "Could not read the balance"
    let balance = systemlist('taxi zebra balance')

    call append(0, balance)
    wincmd k
endfun

fun! s:taxi_balance_close()
    let s:is_closing = 1
    " Close the balance scratch window
    let winnr = bufwinnr('^_taxibalance$')
    if ( winnr >  0 )
        execute winnr . 'wincmd w'
        execute 'wincmd q'
    endif
endfun


fun! s:str_pad(str, len)
    " Right pad a string with zeroes
    " Left pad it when it starts with -
    let indent = repeat(' ', 4)
    let str_len = len(a:str)
    let diff = a:len - str_len
    let space = repeat(' ', diff)

    if a:str[0] == "-"
        return space . a:str . indent
    else
        return a:str . space . indent
    endif
endfun

fun! s:taxi_format_line(lnum, col_sizes)
    " Format a line in taxi
    let line = getline(a:lnum)
    let parts = matchlist(line, s:pat)
    let alias = s:str_pad(parts[1], a:col_sizes[0])
    let time  = s:str_pad(parts[2], a:col_sizes[1])

    call setline(a:lnum, alias . time . parts[3])
endfun

fun! TaxiFormatFile()
    " Format the taxi file
    let data_lines = []
    let col_sizes = [0, 0, 0]
    for line_nr in range(1, line('$'))
        let line = getline(line_nr)
        let parts = matchlist(line, s:pat)
        if len(parts) > 0
            call add(data_lines, line_nr)
            for i in range(1, len(parts) - 1)
                let idx = i - 1
                if len(parts[i]) > 0
                    let col_sizes[idx] = max([col_sizes[idx], len(parts[i])])
                endif
            endfor
        endif
    endfor

    for line in data_lines
        call s:taxi_format_line(line, col_sizes)
    endfor
endfun

fun! TaxiInsertEnter()
    if col('.') == 1
        call feedkeys("\<c-x>\<c-o>", 'n')
    endif
endfun

" Call the function at least once when the script is loaded
call TaxiAssmbleAliases()
