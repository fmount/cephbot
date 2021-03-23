#!/bin/env python

import irc.bot
import daemon
import sys
import os
import logging
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa E402


class CephBot(irc.bot.SingleServerIRCBot):
    def __init__(
            self,
            server: str,
            nick: str,
            psw: str,
            channel: list,
            log_path: str,
            port=6667):

        super(CephBot, self).__init__(
            server_list=[(server, int(port))],
            nickname=nick,
            realname=nick)
            #ident_password=psw,
            #channels=[channel])

        self.nick = nick
        self.password = psw
        self.channel = channel
        self.server = server
        self.port = port

        logging.basicConfig(filename=log_path, level=logging.DEBUG)
        self.log = logging.getLogger(__name__)

    def on_welcome(self, c, e):
        '''
        This event is generated after the connection to an irc server,
        and should be the signal to join the target channel(s)
        '''
        self.identify_msg_cap = False
        c.cap('REQ', 'identify-msg')
        c.cap('END')

        for ch in self.channel:
            self.log.debug('Joining %s' % ch)
            c.join(ch)

    def on_cap(self, c, e):
        '''
        The identify-msg capability causes the server to send an
        "identification" prefix in the message parameter of PRIVMSG
        and NOTICES commands.
        '''
        self.log.debug("Received cap response %s" % repr(e.arguments))
        if e.arguments[0] == 'ACK' and 'identify-msg' in e.arguments[1]:
            self.log.debug("identify-msg cap acked")
            self.identify_msg_cap = True

    def on_privmsg(self, c, e):
        '''
        The prefix is a single character, + (ASCII plus) if the sender is
        "identified" according to services, - (ASCII minus) otherwise.
        '''
        if not self.identify_msg_cap:
            self.log.debug("Ignoring msg from a not well identified user")
            return

        # Capture who posted the message, and what the message was.
        nick = e.source.split('!')[0]
        args = e.arguments[0][1:]  # removing the '+' at the beginning

        words = args.split()

        if len(words) < 1:
            self.log.debug("Ignoring privmsg from %s with no content" % nick)

        cmd = words[0].lower()
        if cmd.startswith('#') or cmd.startswith('+') or cmd.startswith('!'):
            cmd = words[0].lower()[1:]

        # here we can start processing private commands
        # TODO:
        # 1. only specific nicks (identified by the network) should be able
        #    to process commands
        print("Processing and executing %s" % cmd)

    def on_pubmsg(self, c, e):
        # e.target, e.source, e.arguments, e.type
        print("Public")
        print(e.arguments)

    def _whoami(self) -> str:
        return 'o/ I\'m %s' % (self.nick)


if __name__ == '__main__':

    bot = CephBot(config.irc.get('server', ''),
            config.irc.get('nick', '_cephbot'),
            config.irc.get('psw', ''),
            config.irc.get('channels', []),
            config.irc.get('log', 'cephbot.log'),
            config.irc.get('port', 0))
    bot.start()
