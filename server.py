"""
A TCP server that receives raw audio and reply with disfluency tags.
"""
from __future__ import print_function

from contextlib import contextmanager
import os
import Queue
import socket
import sys
import threading

from deep_disfluency.asr.ibm_watson import IBMWatsonAdapter
from deep_disfluency.tagger.deep_tagger_module import DeepTaggerModule
import fluteline
import watson_streaming

import nodes

HOST = ''  # Symbolic name meaning all available interfaces
PORT = 50007  # Arbitrary non-privileged port
TCP_INPUT_BUFFER_SIZE = 1024  # Number of bytes to read from TCP socket
WATSON_SETTINGS = {
    'inactivity_timeout': -1,  # Don't kill me after 30 seconds
    'interim_results': True,
    'timestamps': True
}
CREDENTIALS = 'credentials.json'


@contextmanager
def silence_stdout():
    old_target, sys.stdout = sys.stdout, open(os.devnull, "w")
    try:
        yield
    finally:
        sys.stdout = old_target


class TCPHandler(threading.Thread):
    def __init__(self, conn):
        super(TCPHandler, self).__init__()
        self.conn = conn
        self.daemon = True

    def run(self):
        with silence_stdout():
            pipeline = [
                watson_streaming.Transcriber(WATSON_SETTINGS, CREDENTIALS),
                IBMWatsonAdapter(),
                DeepTaggerModule(),
                nodes.DisfluenciesFilter(),
                nodes.ChangeFilter(),
                nodes.Responder(self.conn),
            ]

        fluteline.connect(pipeline)
        fluteline.start(pipeline)
        try:
            self.ready()
            while True:
                incoming = self.conn.recv(TCP_INPUT_BUFFER_SIZE)
                if not incoming:
                    break
                pipeline[0].input.put(incoming)
        finally:
            fluteline.stop(pipeline)

    def ready(self):
        self.conn.send(json.dumps({'state': 'ready'}) + '\n')


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(1)
    print('Server listening')

    while True:
        conn, addr = sock.accept()
        print('Connected by', addr)
        handler = TCPHandler(conn)
        handler.start()


if __name__ == '__main__':
    main()
