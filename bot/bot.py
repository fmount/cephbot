#!/bin/env python

import irc.bot
import daemon
import sys
import os
import logging
import callback
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
            interact_with: list,
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

        c.privmsg(nick, self._handle_msg(args, nick))

    def on_pubmsg(self, c, e):
        if not self.identify_msg_cap:
            self.log.debug("Ignoring msg from a not well identified user")
            return

        nick = e.source.split('!')[0]
        args = e.arguments[0][1:]  # removing the '+' at the beginning
        chan = e.target

        self._handle_msg(args, nick, chan)

    def _handle_msg(self,
            msg: str,
            nick: str,
            chan=None):
        '''
        Process a generic message, sent on a pub channel or as privmsg.
        '''
        if len(msg.split()) < 1:
            self.log.debug("Ignoring msg from %s because no content is provided" % nick)
        w = msg.lower()
        if w.startswith('#') or w.startswith('+') or w.startswith('!'):
            w = msg.lower()[1:]

        # if it's a pubmsg, make sure it can be processes only if the nick
        # is +v and +o

        #if chan is not None and self._is_voiced(nick, chan)):
        #    print("Processing and executing %s" % w)

        self.log.debug("Processing and executing %s" % w)
        # TODO:
        # 1. tokenize words
        # 2. if it's a valid command, check if it's allowed
        # 3. call the proper callback
        if hasattr(callback, 'on_{}'.format(w)):
            cb = getattr(callback, 'on_{}'.format(w))
            return cb(self.nick)
        return self._usage(callback)

    def _usage(self, callback):
        self.log.debug(dir(callback))
        available_functions = []
        for f in dir(callback):
            if f.startswith('on_'):
                available_functions.append('{}'.format(f))
        self.log.debug(''.join(available_functions))
        return ("Sorry, I'm not able to understand that command! "
                "Run '!help' to see the full list of available commands :(")

    def _is_chanop(self, nick, chan):
        return self.channels[chan].is_oper(nick)

    def _is_voiced(self, nick, chan):
        if chan is not None:
            return (self.channels[chan].is_voiced(nick) or \
                    self.channels[chan].is_oper(nick))

    def allowed(current, ALLOWED_LIST):
        if ALLOWED_LIST is None or len(ALLOWED_LIST) < 1:
            '''
            No members are present in the allowed_list,
            hence anyone can run read-only commands against it
            (e.g. the status of a review can be seen)
            '''
            return False
        if current in ALLOWED_LIST:
            return True
        return False


if __name__ == '__main__':

    bot = CephBot(config.irc.get('server', ''),
            config.irc.get('nick', '_cephbot'),
            config.irc.get('psw', ''),
            config.irc.get('channels', []),
            config.irc.get('log', 'cephbot.log'),
            config.irc.get('allowed_nicks', ''),
            config.irc.get('port', 0))
    bot.start()
