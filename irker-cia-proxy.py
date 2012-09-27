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

import json, socket, posixpath, re
from xml.dom import minidom
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

target_server = "localhost"
target_port = 6659
template = "%(bold)s%(project)s:%(bold)s %(green)s%(author)s%(reset)s %(yellow)s%(branch)s%(reset)s * r%(bold)s%(revision)s%(bold)s /%(files)s%(bold)s:%(bold)s %(log)s"

projmap = json.load(open("projmap.json"))

class CIAMessage:
    "Abstract class which represents a CIA message."
    def __init__(self, messagexml):
        self._dom = minidom.parseString(messagexml)
    def _render_files(self):
        prefix, endings = self._consolidate_files()
        endstr = ' '.join(endings)
        if len(endstr) > 60:
            endstr = self._summarize_files(endings)
        if prefix.startswith('/'):
            prefix = prefix[1:]
        if endstr:
            return "%s (%s)" % (prefix, endstr)
        return prefix
    def _consolidate_files(self):
        files = []
        filenode = self.dig('message', 'body', 'commit', 'files')
        if filenode is not None:
            for child in filenode.childNodes:
                if child.nodeName == 'file':
                    files.append(self._shallowtext(child))
        # Optimization: if we only have one file, don't waste CPU on any of the other
        # stuff we do to pretend to be CIA.
        if len(files) == 1:
            return files[0], []
        prefix = re.sub("[^/]*$", "", posixpath.commonprefix(files))
        endings = []
        for file in files:
            ending = file[len(prefix):].strip()
            if ending == '':
                ending = '.'
            endings.append(ending)
        return prefix, endings
    def _summarize_files(self, files):
        dirs = {}
        for file in files:
            dirs[posixpath.split(file)[0]] = True
        if len(dirs) <= 1:
            return "%d files" % len(files)
        return "%d files in %d dirs" % (len(files), len(dirs))
    def _shallowtext_generator(self, node):
        for child in node.childNodes:
            if child.nodeType == child.TEXT_NODE:
                yield child.data
    def _shallowtext(self, node):
        if node is None:
            return None
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
        return node
    def lookup(self, *subElements):
        text = self._shallowtext(self.dig(*subElements))
        if text is not None:
            return text.strip()
        return None
    def data(self):
        paths = {
            'bold': '\x02',
            'green': '\x033',
            'blue': '\x032',
            'yellow': '\x037',
            'reset': '\x0F' 
        }
        paths['project'] = self.lookup('message', 'source', 'project')
        paths['branch'] = self.lookup('message', 'source', 'branch')
        paths['module'] = self.lookup('message', 'source', 'module')
        paths['revision'] = self.lookup('message', 'body', 'commit', 'revision')
        paths['version'] = self.lookup('message', 'body', 'commit', 'version')
        paths['author'] = self.lookup('message', 'body', 'commit', 'author')
        paths['log'] = self.lookup('message', 'body', 'commit', 'log')
        paths['files'] = self._render_files()
        paths['url'] = self.lookup('message', 'body', 'commit', 'url')
        return paths
    def project(self):
        return self.lookup('message', 'source', 'project')
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

