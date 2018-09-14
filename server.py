"""
A TCP server that receives raw audio and reply with disfluency tags.
"""
from __future__ import print_function

import contextlib
import os
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
SOCKET_SETTINGS = (socket.AF_INET, socket.SOCK_STREAM)


@contextlib.contextmanager
def silence_stdout():
    old_target, sys.stdout = sys.stdout, open(os.devnull, "w")
    try:
        yield
    finally:
        sys.stdout = old_target


def get_pipeline():
    return [
        watson_streaming.Transcriber(WATSON_SETTINGS, CREDENTIALS),
        IBMWatsonAdapter(),
        DeepTaggerModule(),
        nodes.DisfluenciesFilter(),
        nodes.ChangeFilter(),
    ]


def handler(conn, addr):
    print(addr, 'connected')

    with silence_stdout():
        pipeline = get_pipeline()

    responder = nodes.Responder(conn)
    pipeline.append(responder)

    fluteline.connect(pipeline)
    fluteline.start(pipeline)
    try:
        print(addr, 'ready')
        responder.put({'state': 'ready'})
        while True:
            incoming = conn.recv(TCP_INPUT_BUFFER_SIZE)
            if not incoming:
                break
            pipeline[0].input.put(incoming)
    finally:
        fluteline.stop(pipeline)

    print(addr, 'disconnected')


def main():
    with contextlib.closing(socket.socket(*SOCKET_SETTINGS)) as sock:
        sock.bind((HOST, PORT))
        sock.listen(1)
        print('Server listening')

        while True:
            conn_addr = sock.accept()
            handler_thread = threading.Thread(target=handler, args=conn_addr)
            handler_thread.daemon = True
            handler_thread.start()


if __name__ == '__main__':
    main()
