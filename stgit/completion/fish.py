# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from stgit import argparse
import stgit.commands
import stgit.config

_file_args = ['files', 'dir', 'repo']
_has_fish_func_args = [
    'stg_branches',
    'all_branches',
    'applied_patches',
    'unapplied_patches',
    'hidden_patches',
    'other_applied_patches',
    'commit',
    'conflicting_files',
    'dirty_files',
    'unknown_files',
    'known_files',
    'mail_aliases',
]


def _get_file_completion_flag(args):
    if any(file_arg in args for file_arg in _file_args):
        return '-r'
    else:
        return '-f'


def _completions_from_args(args):
    completions = []
    for arg in args:
        if isinstance(arg, argparse.patch_range):
            for endpoint in arg:
                if endpoint in _has_fish_func_args:
                    completions.append('(__fish_stg_%s)' % endpoint)
        elif isinstance(arg, argparse.strings):
            completions.extend(arg)
        elif arg in _file_args:
            pass
        elif arg in _has_fish_func_args:
            completions.append('(__fish_stg_%s)' % arg)
        else:
            raise AssertionError('unknown arg kind: %s' % arg)
    return ' '.join(completions)


def write_fish_completion(f):
    def put(*args, **kwargs):
        kwargs['file'] = f
        print(*args, **kwargs)

    commands = stgit.commands.get_commands(allow_cached=False)
    aliases = []
    for name, values in stgit.config.DEFAULTS:
        if name.startswith('stgit.alias.'):
            alias = name.replace('stgit.alias.', '', 1)
            command = values[0]
            aliases.append((alias, command))

    put(
        '''\
# Fish shell completion for StGit (stg)
#
# To use, copy this file to one of the paths in $fish_complete_path, e.g.:
#
#   ~/.config/fish/completions
#
# This file is autogenerated.

function __fish_stg_all_branches
    command git for-each-ref --format='%(refname)' \\
        refs/heads/ refs/remotes/ 2>/dev/null \\
        | string replace -r '^refs/heads/(.*)$' '$1\\tLocal Branch' \\
        | string replace -r '^refs/remotes/(.*)$' '$1\\tRemote Branch'
end

function __fish_stg_stg_branches
    command stg branch --list 2>/dev/null \\
        | string match -r ". s.\\t\\S+" \\
        | string replace -r ". s.\\t" ""
end

function __fish_stg_applied_patches
    command stg series --noprefix --applied 2>/dev/null
end

function __fish_stg_other_applied_patches
    set -l top (command stg top 2>/dev/null)
    command stg series --noprefix --applied 2>/dev/null \\
        | string match --invert "$top"
end

function __fish_stg_unapplied_patches
    command stg series --noprefix --unapplied 2>/dev/null
end

function __fish_stg_hidden_patches
    command stg series --noprefix --hidden 2>/dev/null
end

function __fish_stg_tags
    command git tag --sort=-creatordate 2>/dev/null
end

function __fish_stg_commit
    __fish_stg_all_branches __fish_stg_tags
end

function __fish_stg_conflicting_files
    command git ls-files --unmerged \\
        | string replace -rf '^.*\\t(.*)$' '$1' \\
        | sort -u
end

function __fish_stg_dirty_files
    command git diff-index --name-only HEAD 2>/dev/null
end

function __fish_stg_unknown_files
    command git ls-files --others --exclude-standard 2>/dev/null
end

function __fish_stg_known_files
    command git ls-files 2>/dev/null
end

function __fish_stg_mail_aliases
    command git config --name-only --get-regexp "^mail\\.alias\\." \\
    | cut -d. -f 3
end'''
    )

    put(
        '''
function __fish_stg_is_alias
    set --local tokens (commandline -opc) (commandline -ct)
    if test "$tokens[1]" = "stg"
        switch "$tokens[2]"
            case %s
                return 0
            case '*'
                return 1
        end
    end
end''' % ' '.join(alias for alias, _ in aliases)
    )

    put(
        '''
function __fish_stg_complete_alias
    set --local tokens (commandline -opc) (commandline -ct)
    set --local cmd "$tokens[2]"
    set --erase tokens[1 2]
    switch "$cmd"'''
    )
    for alias, command in aliases:
        put('        case', alias)
        put('            set --prepend tokens', command)
    put(
        '''\
    end
    complete -C"$tokens"
end
'''
    )

    put('### Aliases: %s' % ' '.join(alias for alias, _ in aliases))
    put(
        "complete    -c stg -n '__fish_stg_is_alias' -x",
        "-a '(__fish_stg_complete_alias)'"
    )
    for alias, command in aliases:
        put(
            "complete    -c stg -n '__fish_use_subcommand' -x",
            """-a %s -d 'Alias for "%s"'""" % (alias, command),
        )

    put()

    put('### help')
    put(
        "complete -f -c stg -n '__fish_use_subcommand' -x",
        "-a help -d 'print the detailed command usage'",
    )
    for cmd, modname, _, _ in commands:
        mod = stgit.commands.get_command(modname)
        put(
            "complete -f -c stg -n '__fish_seen_subcommand_from help'",
            "-a %s -d '%s'" % (cmd, mod.help),
        )
    for alias, command in aliases:
        put(
            "complete -f -c stg -n '__fish_seen_subcommand_from help'",
            """-a %s -d 'Alias for "%s"'""" % (alias, command),
        )

    for cmd, modname, _, _ in commands:
        mod = stgit.commands.get_command(modname)
        completions = []
        put('', '### %s' % cmd, sep='\n')
        put(
            "complete    -c stg -n '__fish_use_subcommand' -x",
            "-a %s -d '%s'" % (cmd, mod.help),
        )

        completions = _completions_from_args(mod.args)
        if completions:
            extra = "-ra '%s'" % completions
        else:
            extra = ""

        put(
            "complete",
            _get_file_completion_flag(mod.args),
            "-c stg",
            "-n '__fish_seen_subcommand_from %s'" % cmd,
            extra,
        )
        put(
            "complete -f -c stg -n '__fish_seen_subcommand_from %s'" % cmd,
            "-s h -l help -d 'show detailed help for %s'" % cmd,
        )

        for opt in mod.options:
            long_opt = ''
            short_opt = '    '
            for flag in opt.flags:
                if len(flag) == 2 and flag.startswith('-'):
                    short_opt = '-s ' + flag[1]
                if flag.startswith('--'):
                    long_opt = '-l ' + flag[2:]
            completions = _completions_from_args(opt.args)
            if completions:
                extra = "-xa '%s'" % completions
            else:
                extra = ""
            put(
                "complete",
                _get_file_completion_flag(opt.args),
                "-c stg",
                "-n '__fish_seen_subcommand_from %s'" % cmd,
                short_opt,
                long_opt,
                "-d '%s'" % opt.kwargs.get('short'),
                extra,
            )


if __name__ == '__main__':
    import sys
    write_fish_completion(sys.stdout)
