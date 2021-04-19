#!/bin/env python

import irc.bot
import daemon
import sys
import os
import re
import logging
import callback
import textwrap
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa E402


# When a msg is split, we should sleep a specific amount of time before
# sending the next part. Freenode allows an higher rate, but this sleep
# time should be enough.
MESSAGE_CONTINUATION_SLEEP = 0.5

# Sleep time between sent messages
ANTI_FLOOD_SLEEP = 2

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

        self.send_wrapped_msg(c, nick, (self._handle_msg(args, nick)))

    def on_pubmsg(self, c, e):
        if not self.identify_msg_cap:
            self.log.debug("Ignoring msg from a not well identified user")
            return

        nick = e.source.split('!')[0]
        args = e.arguments[0][1:]  # removing the '+' at the beginning
        chan = e.target

        self.log.debug("Replying on chan: %s" % chan)
        self.send_wrapped_msg(c, chan, (self._handle_msg(args, nick)))

    def _handle_msg(self,
            msg: str,
            nick: str,
            chan=None):
        '''
        Process a generic message, sent on a pub channel or as privmsg.
        '''
        if len(msg.split()) < 1:
            self.log.debug("Ignoring msg from %s because no content is provided" % nick)
        wds = msg.lower()
        if wds.startswith('#') or wds.startswith('+') or wds.startswith('!'):
            wds = msg.lower()[1:]

            # if it's a pubmsg, make sure it can be processes only if the nick
            # is +v and +o

            #if chan is not None and self._is_voiced(nick, chan)):
            #    print("Processing and executing %s" % w)

            # normalize words, removing all that fun human symbols
            wds = re.sub(r'[?|$|.|!|,|>|<|\]|\[|\{|\}|\/|\\|]', r'', wds).strip()

            w = wds.split()

            self.log.debug("(Normalized) tokens: %s" % w)

            if len(w) < 1:
                return self._usage()

            self.log.debug("Processing and executing %s" % w[0])

            kw = {
                'callback': callback,
                'nick': self.nick,
                'chan': chan,
                'args': w[1:]
            }

            '''
            Check if it's a valid command and is allowed, then
            call the proper registered callback (using the on_
            prefix).
            '''
            if(hasattr(callback, 'on_{}'.format(w[0])) and \
                    self._is_allowed(w[0], 'callback') and \
                    self._is_allowed(nick, 'allowed_nicks')):
                cb = getattr(callback, 'on_{}'.format(w[0]))
                return cb(**kw)
        return self._usage()

    def _is_allowed(self, elem, key):
        '''
        Only process commands explicitly allowed in the config
        area, if the nick is allowed to do that!
        :param elem is the item that can be or cannot be found in the list
        :param key is the key of the dict returning the list where the item can be found
        '''
        return True if elem in config.irc.get(key, []) else False

    def _usage(self):
        return ("Sorry, I'm not able to understand that command or you're "
                "just not allowed to run it! "
                "Run '!help' to see the full list of available commands :(")

    def _is_chanop(self, nick, chan):
        return self.channels[chan].is_oper(nick)

    def _is_voiced(self, nick, chan):
        if chan is not None:
            return (self.channels[chan].is_voiced(nick) or \
                    self.channels[chan].is_oper(nick))

    def send_wrapped_msg(self, c, chan, msg):
        for chunks in msg.split('\n'):
            # 400 chars should be safe
            chunks = textwrap.wrap(chunks, 400)
            count = 0
            if len(chunks) > 10:
                raise Exception("Unusually large message: %s" % (msg,))
            for count, chunk in enumerate(chunks):
                c.privmsg(chan, chunk)
            if count:
                time.sleep(MESSAGE_CONTINUATION_SLEEP)
        time.sleep(ANTI_FLOOD_SLEEP)


if __name__ == '__main__':

    bot = CephBot(config.irc.get('server', ''),
            config.irc.get('nick', '_cephbot'),
            config.irc.get('psw', ''),
            config.irc.get('channels', []),
            config.irc.get('log', 'cephbot.log'),
            config.irc.get('allowed_nicks', ''),
            config.irc.get('port', 0))
    bot.start()
