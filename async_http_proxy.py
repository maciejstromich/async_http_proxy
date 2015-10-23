import aiohttp
import aiohttp.server
import asyncio
import re
import time
import os
from urllib.parse import urlparse, parse_qsl
from aiohttp.multidict import MultiDict

# simple uptime counter start value
startup_time = time.time()
content_length = 0

class MyHTTPProxy(aiohttp.server.ServerHttpProtocol):

    @asyncio.coroutine
    def handle_request(self, message, payload):
        # it's ugly hack but at least it works. 
        # check's for url and serves content based on context.
        # !!! BROKEN after returning status it's doing also going to proxy context
        if message.path == '/status':
            yield from self.status(message) 
        elif message.path.startswith('/'):
            # any other local request is not valid
            yield from self.return_404(message)
        else:
            yield from self.proxy(message, payload)
    
    def ownlogger(self, message, status, source=None):
        print("%s [ %s ] \"%s %s HTTP/%s.%s\" %s" % \
                (time.time(), source, message.method, message.path, message.version.major, message.version.minor, status))
    @asyncio.coroutine
    def return_404(self, message):
        response = aiohttp.Response(self.writer, 404, http_version=message.version)
        content = '<h1>Not Found</h1>'
        response.send_headers()
        response.write(content.encode())
        response.write_eof()
        self.ownlogger(message, response.status, 'HTTP')

    @asyncio.coroutine
    def status(self, message):
        # http response for /status containing uptime and data transfered 
        response = aiohttp.Response(self.writer, 200, http_version=message.version)
        content = "uptime: %s\r\ndata transefered: %s" % ( self.count_uptime(startup_time), content_length)
        response.send_headers()
        response.write(content.encode())
        response.write_eof()
        self.ownlogger(message, response.status, 'HTTP')
    
    def check_ranges(self, message, queries):
        # checks if parameters passed via range query parameter and range http request are the same
        # if not returns HTTP 416 with proper notification
        if message.headers['range'][6:] != queries['range']:
            response = aiohttp.Response(self.writer, 416, http_version=message.version)
            content = 'Range request parameter and range query parameter have different values, aborting!\r\n'
            response.send_headers()
            response.write(content.encode())
            yield from response.write_eof()
            self.ownlogger(message, response.status)

    def convert_queries_to_dict(self, query_str):
        # takes and converts queries str to a dict
        queries = {}
        for i in query_str.split('&'):
            queries[i.split('=')[0]] = i.split('=')[1]
        return queries

    def count_uptime(self, start_time):
        # returns uptime
        return time.time() - startup_time

    @asyncio.coroutine
    def proxy(self, message, payload):
        # proxy method. handles download content
        queries = {}
        global content_length
        # check if there are query params. if yes convert them into dict for easier use
        if urlparse(message.path)[4]:
            queries = self.convert_queries_to_dict(urlparse(message.path)[4])
        # simple checks to get to know the situation with ranges
        # requirement #2 from https://github.com/castlabs/python_programming_task
        if 'range' in message.headers and 'range' in queries:
            yield from self.check_ranges(message, queries)
        # range query parameter is not supported as a true range request so we need to convert it into header which will be sent
        if 'range' in queries and not 'range' in message.headers:
            message.headers['range'] = "bytes=%s" % (queries['range'],)
        # make a http request to host 
        remote_resp = yield from aiohttp.request(message.method, message.path, headers=message.headers)
        # build a response based on remote_resp 
        response = aiohttp.Response(self.writer, remote_resp.status, http_version=message.version)
        response.add_header('content-length', remote_resp.headers['content-length'])
        response.add_header('content-type', remote_resp.headers['content-type'])
        if 'accept-ranges' in remote_resp.headers:
            response.add_header('accept-ranges', remote_resp.headers['accept-ranges'])
        if 'content-range' in remote_resp.headers:
            response.add_header('content-range', remote_resp.headers['content-range'])
        response.send_headers()
        # we don't want to store whole response in the memory and rather read and return every 1kB
        while True:
            chunk = yield from remote_resp.content.read(1024)
            if not chunk:
                break
        #content = yield from remote_resp.content.read()
            response.write(chunk)
        # update content-length for /status purposes
        yield from response.write_eof()
        self.ownlogger(message, response.status, 'PROXY')
        content_length = content_length + int(remote_resp.headers['content-length'])


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    f = loop.create_server(
        lambda: MyHTTPProxy(debug=True, keep_alive=60),
        '0.0.0.0', os.environ['HTTP_PROXY_PORT'])
    srv = loop.run_until_complete(f)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass   
