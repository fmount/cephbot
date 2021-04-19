#!/bin/env python

import sys
import itertools
import random
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa E402
import patch_set as ps  # noqa E402

def on_hello(**kwargs) -> str:
    nick = kwargs.get('nick', 'cephbot')
    return 'Hello, I\'m %s\'s bot, how can I help you' % (nick)

def on_help(**kwargs) -> str:
    available_functions = []
    c = kwargs.get('callback', None)
    if c is not None:
        for f in dir(c):
            if (f.startswith('on_') and \
                    f.split('on_')[1] in config.irc.get('callback', [])):
                available_functions.append('{}'.format(f[3:]))
        return ('Available functions are: %s' % (', '.join(available_functions)))
    return ''

def on_gerrit(**kwargs) -> str:
    '''
    This command can be processed if provided with the following
    syntax:

    !gerrit <command> <submission_id>

    There are a few available sub-commands:

    * summary
    * status
    * recheck
    * rebase
    '''

    c_read = ['status', 'summary', 'logs']
    c_write = ['recheck', 'rebase']
    # process arguments
    args = kwargs.get('args', [])
    if not args or len(args) < 2:
        return("Please follow this syntax: \n"
               "!gerrit <command> <submission_id> \n"
               "Available gerrit functions are: %s" % (', '.join(list(itertools.chain(c_read, c_write)))))

    if args[0] in c_read:
        try:
            review = int(args[1])
        except ValueError:
            return "The submission_id is wrong, it's not an int!"
        d = ps.load_latest_available_data(config.gerrit_config, review)

    # a switch - case statement looking for the proper ps function
    if args[0] == "status":
        _, status = ps._show_summary(d, True)
        return (str(status))
    elif args[0] == "summary":
        summary, _ = ps._show_summary(d, True)
        return (str(summary))
    elif args[0] == "logs":
        psnum, comments = ps.process_data(config.gerrit_config, d)
        logs = ps._show_ci_logs(comments)
        return str(logs)
    else:
        return("I barely understand what gerrit is, I don't remember a command like the "
               "one you run! (rebase and recheck are not yet available)")

def on_squad(**kwargs) -> str:
    '''
    This command can be processed if provided with the following
    syntax:

    !squad <command>

    There are a few available sub-commands:

    * status
    '''
    squad_etherpad = 'https://etherpad.openstack.org/p/tripleo-integration-squad-status'
    subcmds = ['status']
    # process arguments
    args = kwargs.get('args', [])
    if not args or len(args) < 1:
        return("Please follow this syntax: \n"
               "!squad <command> \n"
               "Available squad functions are: %s" % (', '.join(subcmds)))

    # a switch - case statement looking for the proper subcommand
    if args[0] == "status":
        return ('The Ceph Squad status can be found here: {}'.format(str(squad_etherpad)))
    else:
        return ("Command not valid, please provide one of the available commands [ %s ]" % (' '.join(subcmds)))

def on_guess(**kwargs) -> str:
    '''
    This command is just implemented to have some fun with this bot.
    It represents a quick version of the "guess the number" game.
    syntax:

    !guess <number>

    an int must be passed and will be evaluated within the function.
    '''


    args = kwargs.get('args', [])
    if not args or len(args) < 1:
        return("Please follow this syntax: \n"
               "!guess <integer> \n")

    number = random.randint(1, 50)

    try:
        guess = int(args[0])
        if guess == number:
            return("You did it!")
        return("You're not so lucky today, try again! (my number was %d)" % number)
    except ValueError:
        return("Please enter an integer")
