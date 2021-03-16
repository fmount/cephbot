#!/usr/bin/python

from prettytable import PrettyTable
import paramiko
import json
import config
import keyring
import os


GERRIT_BASE_CMD = "gerrit"

def gerrit_cmd(mode,
               ps,
               psnum,
               args=None,
               format='JSON',
               **kwargs):
    '''
    Build the arguments on top of the basic gerrit
    command to run against the provided PS.
    '''

    cmd = "{} {}".format(GERRIT_BASE_CMD, mode)

    if mode == "query":
        if args is not None:
            for arg in args:
                cmd += " --{}".format(arg)
        cmd += " --current-patch-set {} --format={}".format(ps, format)

    # TODO:
    #       Check the options:
    #       1. --rebase
    #       2. --code-review (it should be 0 by default, hardcoded!)
    #       3. --message '"recheck"'
    #       4. the patchset should point to the latest change <PS>,<change:int>
    elif mode == "review":
        cmd += ' {},{}'.format(ps, psnum)
        if args is not None:
            for arg in args:
                cmd += ' --{}'.format(arg)
        if kwargs is not None:
            for key, value in kwargs.items():
                if isinstance(value, int):
                    cmd += ' --{} {}'.format(key, value)
                elif allowed(value, args):
                    cmd += ' --{} \'"{}"\''.format(key, value)
    else:
        raise Exception("No valid options provided")

    return cmd


def allowed(current, args):
    if args is None:
        return True
    if current == "recheck" and "rebase" in args:
        return False
    return True


def run_gerrit_cmd(gerrit_conf,
                   mode,
                   num=None,
                   args=None,
                   **kwargs):
    '''
    For now and for test purposes, I'm
    loading the config from  a dict
    '''

    key = paramiko.RSAKey(filename=(os.path.expanduser(gerrit_conf['user']['key'])))

    # generate the gerrit command to run against the defined PS
    cmd = gerrit_cmd(mode, gerrit_conf['watch_ps'], num, args, **kwargs)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.load_system_host_keys()

    ssh.connect(hostname=gerrit_conf['instance'],
                username=gerrit_conf['user']['name'],
                port=gerrit_conf['port'],
                pkey=key,
                allow_agent=True)

    stdin, stdout, stderr = ssh.exec_command(cmd)

    payload = stdout.readlines()
    perr = stderr.readlines()

    ssh.close()

    if len(perr) > 0:
        return perr

    return payload


def load_latest_available_data(conf):
    data = run_gerrit_cmd(config.gerrit_config, 'query')
    return data[0]


def _get_latest_ps(data):
    if data is not None:
        d = json.loads(data)
        return d['currentPatchSet']['number']


def _show_summary(data):
    '''
    Print a summary related to the last execution
    of the current patch
    '''
    s = json.loads(data)
    print("--------SUMMARY-------")
    print("PROJECT: %s" % s['project'])
    print("CURRENT PS: %d " % s['currentPatchSet']['number'])
    print("LAST ACTION: %s " % s['currentPatchSet']['kind'])

    # TODO: Append the links of the logs in a table field
    status = PrettyTable(["Name", "Status"])
    for approval in s['currentPatchSet']['approvals']:
        status.add_row([approval['by']['name'], approval['value']])
    print(status)


def _recheck(conf, psnum, args, **kwargs):
    #out = run_gerrit_cmd(config.gerrit_config, 'review', num, ['rebase'], **{'message':'recheck', 'code-review': 0})
    #out = run_gerrit_cmd(config.gerrit_config, 'review', **{'message':'recheck', 'code-review': 0})
    out = run_gerrit_cmd(conf,
                         'review',
                         psnum,
                         args,
                         **kwargs)
    return out



if __name__ == '__main__':


    # READING
    d = load_latest_available_data(config.gerrit_config)
    num = _get_latest_ps(d)
    _show_summary(d)

    # The following is within get_latest_available_data
    # out = run_gerrit_cmd(config.gerrit_config, 'query', ['comments'])
    # out = run_gerrit_cmd(config.gerrit_config, 'query')


    # WRITING
    out = _recheck(config.gerrit_config, num, ['rebase'], **{'message': 'recheck', 'code-review': 0})
    _show_summary(out)
