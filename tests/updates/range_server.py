#!/usr/bin/env python3
"""A tiny HTTP file server with Range support (resumed downloads, a file read in parts) and a request log, for DRBR's
update tests. Files under norange/ are always sent whole (a server without ranges). A path with no file but a
"<path>.redirect" file is answered 302 to the address in it (as GitHub's latest -> v<version> -> its file host). Log
lines: "GET <path>", "RANGE <path> <first>-<last>", "REDIRECT <path> <address>" or "NOTFOUND <path>".
Usage: range_server.py <root dir> <port> <log file>"""
import http.server, os, sys, re, urllib.parse

ROOT, PORT, LOG = sys.argv[1], int(sys.argv[2]), sys.argv[3]


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        path = urllib.parse.unquote(self.path.split('?')[0]).lstrip('/')
        full = os.path.realpath(os.path.join(ROOT, path))
        if full.startswith(os.path.realpath(ROOT)) and not os.path.isfile(full) and os.path.isfile(full + '.redirect'):
            to = open(full + '.redirect').read().strip()
            with open(LOG, 'a') as lg:
                lg.write('REDIRECT %s %s\n' % (path, to))
            self.send_response(302)
            self.send_header('Location', to)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        if not full.startswith(os.path.realpath(ROOT)) or not os.path.isfile(full):
            # (DRBR 1.0.2: logged too - the wrong-tag release's own address is asked first)
            with open(LOG, 'a') as lg:
                lg.write('NOTFOUND %s\n' % path)
            self.send_response(404)
            self.end_headers()
            return
        size = os.path.getsize(full)
        rng = self.headers.get('Range')
        if path.startswith('norange/'):
            rng = None
        name = path
        start, end = 0, size - 1
        if rng:
            m = re.match(r'bytes=(\d+)-(\d*)', rng)
            if m:
                start = int(m.group(1))
                end = min(size - 1, int(m.group(2))) if m.group(2) else size - 1
                if start >= size or end < start:
                    self.send_response(416)
                    self.send_header('Content-Range', 'bytes */%d' % size)
                    self.end_headers()
                    return
        with open(LOG, 'a') as lg:
            lg.write(('RANGE %s %d-%d\n' % (name, start, end)) if rng else ('GET %s\n' % name))
        self.send_response(206 if rng else 200)
        self.send_header('Content-Length', str(end - start + 1))
        if rng:
            self.send_header('Content-Range', 'bytes %d-%d/%d' % (start, end, size))
        self.send_header('Accept-Ranges', 'bytes')
        self.end_headers()
        with open(full, 'rb') as f:
            f.seek(start)
            left = end - start + 1
            while left > 0:
                b = f.read(min(left, 1 << 20))
                if not b:
                    break
                self.wfile.write(b)
                left -= len(b)


http.server.ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
