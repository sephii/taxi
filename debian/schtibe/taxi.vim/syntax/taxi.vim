" Vim syntax file
" Language: tks
" Maintainer:   Martyn Smith <martyn@catalyst.net.nz>
" Last Change:  2008 May 26
" Quit when a (custom) syntax file was already loaded
if exists("b:current_syntax")
  finish
endif
syntax match tksWR "^\s*\S\+" nextgroup=tksTime skipwhite
syntax match tksTime "\s[0-9.:-]\+" nextgroup=tksDescription skipwhite contained
syntax region tksDescription start="\S" end="$" skipwhite contained keepend
syn region comment start="#" end="$"
syn region committed start="=" end="$"
syn match date "^\d\d\d\d-\d\d-\d\d"
syn match date "^\d\+/\d\+/\d\d"
syn match date "^\d\+/\d\+/\d\d\d\d"
syn match date "^\d\+\.\d\+\.\d\d\d\d.*"
hi def link date Label
hi def link comment Comment
hi def link tksWR PreProc
hi def link tksTime Type
hi def link tksDescription String
hi def link committed Constant
let b:current_syntax = "tks"
