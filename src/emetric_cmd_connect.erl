%%%-------------------------------------------------------------------
%%% @author Justin Kirby <jkirby@voalte.com>
%%% @copyright (C) 2011 Justin Kirby
%%% @end
%%%
%%% This source file is subject to the New BSD License. You should have received
%%% a copy of the New BSD license with this software. If not, it can be
%%% retrieved from: http://www.opensource.org/licenses/bsd-license.php
%%%-------------------------------------------------------------------

-module(emetric_cmd_connect).

-behaviour(emetric_command).

-export([ command_help/0,
	  deps/0,
	  run/0
	  ]).



command_help() ->
    {"connect","","Connect to node and respond with result"}.


deps() -> [].

run() ->
    %% if there is a cookie, change ourse
    Cookie = list_to_atom(emetric_config:get_global(cookie)),
    Node = list_to_atom(emetric_config:get_global(node)),
    NetKernelParams =
        case emetric_config:get_global(local_node) of
        undefined ->
            ['emetric@localhost',shortnames];
        N ->
            [list_to_atom(N)]
        end,
    ok = ping(NetKernelParams,Node,Cookie).




ping(NetKernelParams,Node,Cookie) ->
    %%escript doesn't start this
    {ok,_Pid} = net_kernel:start(NetKernelParams),

    %% it is possible to have the names out of sync in epmd
    %% need to wait for the names to get worked out
    global:sync(),

    erlang:set_cookie(node(),Cookie),
    pong = net_adm:ping(Node),

    ok.
    
    



    
