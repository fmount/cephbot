#!/bin/env python

def on_hello(**kwargs) -> str:
    nick = kwargs.get('nick', 'cephbot')
    return 'Hello, I\'m %s\'s bot, how can I help you' % (nick)

def on_help(**kwargs) -> str:
    available_functions = []
    c = kwargs.get('callback', None)
    if c is not None:
        for f in dir(c):
            if f.startswith('on_'):
                available_functions.append('{}'.format(f[3:]))
        return ('Available functions are: %s' % (', '.join(available_functions)))
    return ''
