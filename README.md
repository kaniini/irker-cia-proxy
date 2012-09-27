irker-cia-proxy
===============

Proxy server which emulates CIA.vc and translates to an [irker(1)][irker] JSON call.
irker is in, layman's terms, "decentralized CIA."

To set up, edit the script and projmap.json file as needed.

[irker]: http://www.catb.org/~esr/irker/irker.html

projmap.json syntax
===================

The project map file is just serialized JSON.  There's a few tricks you can do which are
kind of neat though.

Here is the simple configuration:

```JSON
{"CIA-project-field": {"to": "irc://..."}}
```

But, you can send to more than one channel at a time, and customize the "colortext" output
sent to IRC, as well:

```JSON
{"CIA-project-field": {"to": ["irc://irc.server.org/#channel","irc://irc.freenode.net/#commits"],
                       "template": "%(project)s %(author)s: %(log)s"},
 "Other-project-field": {"to": []}}
```

