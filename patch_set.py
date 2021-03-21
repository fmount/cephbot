#!/usr/bin/python

from prettytable import PrettyTable
import paramiko
import json
import config
import keyring
import logging
from datetime import datetime
import os
import re


GERRIT_BASE_CMD = "gerrit"
LOG_PATH = "/tmp/gerrit_cmds.log"

# logging should be moved into the wrapping class
logging.basicConfig(filename=LOG_PATH, level=logging.DEBUG)
log = logging.getLogger(__name__)

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
                   review,
                   num=None,
                   args=None,
                   **kwargs):
    '''
    For now and for test purposes, I'm
    loading the config from  a dict
    '''

    key = paramiko.RSAKey(filename=(os.path.expanduser(gerrit_conf['user']['key'])))

    # generate the gerrit command to run against the defined PS
    cmd = gerrit_cmd(mode, review, num, args, **kwargs)
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


def load_latest_available_data(conf, review):
    data = run_gerrit_cmd(config.gerrit_config, 'query', review, None, ['comments'])
    return data[0]


def _show_summary(data):
    '''
    Print a summary related to the last execution
    of the current patch
    '''
    s = json.loads(data)
    summary = PrettyTable(["Project", "Current PS", "Last Action"])
    summary.add_row([s['project'], s['currentPatchSet']['number'], s['currentPatchSet']['kind']])

    status = PrettyTable(["Name", "Status"])
    if s['currentPatchSet'].get('approvals', None) is None:  # CI is currently running!
        print("STATUS: The patch is currently running on CI")
    else:
        for approval in s['currentPatchSet']['approvals']:
            status.add_row([approval['by']['name'], approval['value']])
    return (summary, status)


def _unpack(log):
    s = ""
    for name, link in log.items():
        s += '- {} {}\n'.format(name, link)
    return s


def _show_ci_logs(retrieved_data):
    summary = PrettyTable(["Date/Time", "Reviewer", "Logs"])
    for elem in retrieved_data:

        log.debug("TIME: %s \nREVIEWER: %s\n" % (list(elem.keys())[0][0], list(elem.keys())[0][1]))

        s = ""
        for k, lg in elem.items():
            s = _unpack(lg)

        log.debug(s)

        summary.add_row([datetime.fromtimestamp(list(elem.keys())[0][0]), list(elem.keys())[0][1], s])

    return summary


def _rebase(conf, review, psnum, args, **kwargs):

    # out = run_gerrit_cmd(config.gerrit_config, 'review', num, ['rebase'], **{'message':'recheck', 'code-review': 0})
    out = run_gerrit_cmd(conf,
                         'review',
                         review,
                         psnum,
                         args,
                         **kwargs)
    if len(out) == 0:
        '''
        rebase succeeded, an empty array is
        returned, no more actions to perform
        '''
        return True

    print(out)
    if "fatal" in out[0]:  # Cannot rebase, just recheck for now
        return False
    return True


def _recheck(conf, review, psnum, args=None, **kwargs):

    # out = run_gerrit_cmd(config.gerrit_config, 'review', **{'message':'recheck', 'code-review': 0})
    run_gerrit_cmd(conf,
                   'review',
                   review,
                   psnum,
                   **kwargs)
    return True


def _show_ci_comment_list(comments):
    for k in list(comments.keys()):
        print('{}, {}'.format(k[0], k[1]))


def _get_job(k, v, depth):
    _jobs = {}
    indent_level = 0  # just check the first level
    line = re.compile(r'( *)- ([^\n]+)(?:: ([^\n]*))?\n?')
    indent_level = 0  # just check the first level
    for indent, job, other in line.findall(v[depth].strip()):
        indent = len(indent)
        if indent > indent_level:
            raise Exception("unexpected indent")
        k = job.split(" ")[0]
        log.debug("TOKEN NAME DETECTED: %s\nTOKEN VALUE DETECTED %s" % (job.split(" ")[0], job.split(" ")[1]))
        v = job.split(" ")[1]
        _jobs[k] = v
    return _jobs


def _get_ci_logs(filtered, data, depth):
    k = list(filtered.keys())
    v = list(filtered.values())

    log.debug("%s, %s" % (k[-2]))
    log.debug("%s, %s" % (k[-1], v[-1].strip()))

    jobs = []
    for index in reversed(range(depth, 0)):
        j = _get_job(k, v, index)
        jobs.append({k[int(index)]: j})
    return jobs


def process_data(gerrit_conf, data):
    s = json.loads(data)
    allowed = gerrit_conf['allowed_ci']
    latest_ps = s['currentPatchSet']['number']
    filtered = {}


    # let's filter according to the allowed CI(s)
    for comment in s.get('comments', {}):
        if comment['reviewer']['name'] in allowed:
            filtered[(comment['timestamp'], comment['reviewer']['name'])] = comment['message']

            log.debug("%s, %s" % (comment['timestamp'], comment['reviewer']['name']))
    # _show_ci_comment_list(filtered)
    depth = -2
    jb = _get_ci_logs(filtered, data, depth)

    log.debug(jb)  # log the resulting jobs
    return latest_ps, jb


if __name__ == '__main__':

    reviews = config.gerrit_config['watch_ps']
    comments = []
    psnum = 0

    assert isinstance(reviews, list)

    for r in reviews:
        # READING
        d = load_latest_available_data(config.gerrit_config, r)
        psnum, comments = process_data(config.gerrit_config, d)
        summary, status = _show_summary(d)
        logs = _show_ci_logs(comments)

        print(summary)
        print(status)
        print(logs)


        # TODO:
        #   1. turn script definition into OO

        # WRITING
        #if not _rebase(config.gerrit_config, review, num, ['rebase']):
        #    _recheck(config.gerrit_config, review, num, **{'message': 'recheck', 'code-review': 0})
        #    print("RECHECK?")
