#!/usr/bin/env python

gerrit_config = {
    'instance': 'review.openstack.org',
    'port': '29418',
    'mode': 'ssh',
    'submissions': {
        '778915': {
            'actions': [
                'watch',
                'rebase',
                'recheck'
            ]
        },
        '780794': {
            'actions': [
                'watch'
            ]
        },
        '781069': {
            'actions': [
                'watch'
            ]
        }
    },
    'allowed_ci': [
        'Zuul',
        'RDO Third Party CI'
    ],
    'user': {
        'name': 'cephbot',
        'psw': 'None',
        'key': '<path_of_the_cephbot_private_key>'
    }
}

irc = {
    'server': 'foo',
    'port': '6667',
    'nick': 'cephbot',
    "pass": "",
    'channels': [
        '#ch1',
        '#ch2',
    ],
    'log': 'cephbot.log'
}
