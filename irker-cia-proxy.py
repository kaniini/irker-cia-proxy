#!/usr/bin/env python
"""
irker-cia-proxy - proxy CIA requests to an irker relay agent

Copyright (c) 2012 William Pitcock <nenolod@dereferenced.org>

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

This software is provided 'as is' and without any warranty, express or
implied. In no event shall the authors be liable for any damages arising
from the use of this software.
"""

import json, socket
import xml.parsers.expat
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

target_server = "localhost"
target_port = 6659
template = "%(message/source/project)s %(message/body/commit/author)s %(message/source/branch)s * %(message/body/commit/revision)s / %(message/body/commit/files/file)s: %(message/body/commit/log)s"

projmap = json.load(open("projmap.json"))

class CIAMessage:
    "Abstract class which represents a CIA message."
    def __init__(self, messagexml):
        self._field = []
        self._data = {}
        parser = xml.parsers.expat.ParserCreate()
        def _elem_start(name, attrs):
            self._field.append(name)
        parser.StartElementHandler = _elem_start
        def _elem_data(data):
            self._data['/'.join(self._field)] = data
        parser.CharacterDataHandler = _elem_data
        def _elem_end(end):
            self._field.pop()
        parser.EndElementHandler = _elem_end
        parser.Parse(messagexml)
    def data(self):
        return self._data
    def message(self):
        return template % self._data
    def relay(self):
        structure = {"to": projmap[self._data['message/source/project']], "privmsg": self.message()}
        envelope = json.dumps(structure)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(envelope + "\n", (target_server, target_port))
        finally:
            sock.close()

class CIARequestHandler(SimpleXMLRPCRequestHandler):
    "A fake CIA server for receiving messages to translate and proxy."
    rpc_paths = ('/RPC2')

def deliver(message):
    CIAMessage(message).relay()
    return True

server = SimpleXMLRPCServer(('', 8000), CIARequestHandler)
server.register_introspection_functions()
server.register_function(deliver, 'hub.deliver')
server.serve_forever()

