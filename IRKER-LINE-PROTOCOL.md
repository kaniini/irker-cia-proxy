irker line protocol description
===============================

An implementation of [irker(1)][irker] is a server which listens for UDP datagrams and TCP connections
on port 6659, which contain a JSON serialized structure which lists instructions on what the irker
implementation should send and where.  This document is intended to be helpful for those looking to
write their own client or server implementation of the irker line protocol.

irker was proposed as a replacement to the aging CIA service, when it was realized that it may be
generally useful to have a generic notification posting mechanism to IRC channels.  An irker server
implementation may deliver messages using whatever mechanism is best suited to it's capabilities.
In other words, it can be an IRC server, a bot multiplexer, or perhaps a services implementation.

[irker]: http://www.catb.org/~esr/irker/irker.html

irker messages
==============

An irker message is a structure with two fields: `to` and one of `privmsg` or `notice`.

A sample irker message is below:

```JSON
{
	"to": "irc://irc.atheme.org/#atheme",
	"privmsg": "atheme: nenolod master r12345 * /src/services/main.c: fixed the desplunking bug"
}
```

There can be multiple `to` targets, in which case the `to` field is represented as a JSON list.

