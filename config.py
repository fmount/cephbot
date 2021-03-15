#!/usr/bin/env python

gerrit_config = {
    'instance': 'review.openstack.org',
    'port': '29418',
    'mode': 'ssh',
    'watch_ps': '778915',
    'user': {
        'name': 'cephbot',
        'psw': 'None',
        'key': '<path_of_the_cephbot_private_key>'
    }
}
