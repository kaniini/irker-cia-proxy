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
from xml.dom import minidom
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

target_server = "localhost"
target_port = 6659
template = "%(project)s %(author)s %(branch)s * %(revision)s / %(files)s: %(log)s"

projmap = json.load(open("projmap.json"))

class CIAMessage:
    "Abstract class which represents a CIA message."
    def __init__(self, messagexml):
        self._dom = minidom.parseString(messagexml)
    def _shallowtext_generator(self, node):
        for child in node.childNodes:
            if child.nodeType == child.TEXT_NODE:
                yield child.data
    def _shallowtext(self, node):
        return ''.join(self._shallowtext_generator(node))
    def dig(self, *subElements):
        if not self._dom:
            return None
        node = self._dom
        for name in subElements:
            nextNode = None
            for child in node.childNodes:
                if child.nodeType == child.ELEMENT_NODE and child.nodeName == name:
                    nextNode = child
                    break
            if nextNode:
                node = nextNode
            else:
                return None
        return self._shallowtext(node).strip()
    def data(self):
        paths = {}
        paths['project'] = self.dig('message', 'source', 'project')
        paths['branch'] = self.dig('message', 'source', 'branch')
        paths['module'] = self.dig('message', 'source', 'module')
        paths['revision'] = self.dig('message', 'body', 'commit', 'revision')
        paths['version'] = self.dig('message', 'body', 'commit', 'version')
        paths['author'] = self.dig('message', 'body', 'commit', 'author')
        paths['log'] = self.dig('message', 'body', 'commit', 'log')
        paths['files'] = self.dig('message', 'body', 'commit', 'files')
        paths['url'] = self.dig('message', 'body', 'commit', 'url')
        return paths
    def project(self):
        return self.dig('message', 'source', 'project')
    def message(self):
        return template % self.data()
    def relay(self):
        structure = {"to": projmap[self.project()], "privmsg": self.message()}
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

