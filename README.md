# Yet another IRC Bot to help me stop wasting time!

** NOTE **

The purpose of this project is automating _actions_ I do on a daily basis, automating them
as much as possible and allowing /me to work more via IRC.

## Dependencies

The bot is built around `**SingleServerIRCBot**`, hence this library should be available in
the python environment to successfully execute the bot.

## Running the bot

Provided that a valid config.py is filled with at least the irc information, the bot can be
deployed by running its main function:

    ./bot/bot.py

## Features

This bot is designed to be easily extensible: the act of providing callback functions is
the way to register and, later in the process, handle specific commands. The current
implementation provides some basic (default) functionalities, such as the helper and the
gerrit interaction, which is something I use on a regular basis.
However, the existing features can be extended and multiple features can be easily added.
The next sections are supposed to explain how extending this bot works.

## Callback(s)

Callbacks represent a generic approach to make the provided functions resolved as a member
of a regular python class and executed when a given command matches the callback name; for
each callback a default structure is passed as an argument and can be useful to define a
generic way of accessing and processing functions, passing an arbitrary number of args,
encapsulated in a **kwargs structure.

A generic callback looks like the following:

```
def on_<callback_name>(**kwargs) -> str:
    pass
```

As you can see in the snipped above, it always returns a string, which is the content of
the message the bot should return on the channel where the interaction is happening.
Within the function, the `**kwargs` structure should be unpacked and processes according
to the function logic that is going to be implemented.

At the moment of writing, the default available callbacks are:

1. *on_gerrit*: I use gerrit (and its web UI) for coding reviews in my daily basis job. Given
              the fact I spend a lot of time looking for the status of a given submission,
              reading the summary, the CI logs, re-triggering the CI jobs related to many
              submissions, this function represents for me a shortcut in the gerrit interaction,
              and its syntax can be extended as needed.

2. *on_guess*: This command is just implemented to have some fun with this bot. It represents
             a quick version of the *guess the number* game.

3. *on_hello*: A must have function, easy to implement and used to return the hello message,
             it shows how a value (the nick in this case), can be unpacked from the kwargs
             structure passed as argument.

4. *on_help*:  It's a dynamic function, returning all the available functions registered in
             the callback array (defined in the config.py)

## Config.py

When the bot starts, the config provided in [config.py](https://github.com/fmount/cephbot/blob/master/config.py)
is loaded and used, during its execution, when specific events occur.
The config is just a set of dictionaries, and each of them contains a piece of configuration
that is related to different aspects (or functions) of the bot.
For instance, the **irc** dictionary can be used to define the basic IRC configuration, such as
the server instance, the port, the nick, channels; the irc dictionary has been extended to
support many other bot specific configurations:

1. allowed\_nick: this represents an array of the nicks that are allowed to interact with
   the bot This represents some sort of security function because allowing all the nicks
   interacting with the bot can be dangerous (just because we can't assume the registered
   and available callbacks are safe and can be called by anyone).

2. callback: this represents the array of the registered callbacks. When a new callback is
   developed within [callback.py](https://github.com/fmount/cephbot/blob/master/bot/callback.py),
   it should be registered here, or it will be ignored and calling it has no effect.


    irc = {
        'server': 'chat.freenode.net',
        'port': '6667',
        'nick': 'mybot',
        "pass": "mybot",
        'channels': [
            '#tripleo-ceph',
        ],
        'allowed_nicks': [
            'fmount'
        ],
        'log': 'mybot.log',
        'callback': [
            'hello',
            'help',
            'gerrit',
            'guess',
        ]
    }


In [config.py](https://github.com/fmount/cephbot/blob/master/config.py) multiple dictionaries,
containing configurations for different components can be added.
As an example, when the *!gerrit* command is executed, the bot should be able to reach the
gerrit instance, authenticate against it (via ssh), and finally run the query.
This means a gerrit specific configuration should be added and loaded during this kind of
interaction.

See [config.py](https://github.com/fmount/cephbot/blob/master/config.py) for more details.

## Extending the bot capabilities

As mentioned before, the idea behind this bot is to make it reusable in many contexts,
extensible in terms of capabilities, highly configurable and easy to use.
For this reason extending it shouldn't be painful and shouldn't require to make a big
reverse engineering of the project.
Here a simple list of steps that are supposed to help to extend the functions provided by
the bot.

Assuming one wants to add a new function:

1. Register the callback name in the callbacks array provided by config.py in the irc
   dictionary.
2. In the [callback.py](https://github.com/fmount/cephbot/blob/master/bot/callback.py) file,
   start a new function with the `on_` prefix, like the following:

```
def on_<callback_name>(**kwargs) -> str:
    pass
```

This function should contain the logic of the new command. As a reference example, look at the
gerrit function implementation, which also includes the patchset.py library which is supposed
to provide all the functions needed to interact with gerrit.
All the libraries should go under $project/lib.

## TODO

1. Improve the way the bot is run
2. Include some packaging info
3. Add some tox tests
