#!/bin/env python

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa E402

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
    return("I barely understand what gerrit is, let me try to understand the parameters")
