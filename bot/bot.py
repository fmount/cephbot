#!/bin/env python

import irc.bot
import daemon
import sys
import os
import logging
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
            server_list=[(server, port)],
            nickname=nick,
            realname=nick,
            ident_password=psw,
            channels=[channel])

        self.nick = nick
        self.password = psw
        self.channel = channel
        self.server = server
        self.port = port

        logging.basicConfig(filename=log_path, level=logging.DEBUG)
        self.log = logging.getLogger(__name__)

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        pass

    def on_pubmsg(self, c, e):
        # e.target, e.source, e.arguments, e.type
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
