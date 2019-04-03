"""
A TCP server that receives raw audio and reply with disfluency tags.
"""
from __future__ import print_function

import argparse
import contextlib
import json
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
TCP_INPUT_BUFFER_SIZE = 1024  # Number of bytes to read from TCP socket
SOCKET_SETTINGS = (socket.AF_INET, socket.SOCK_STREAM)


@contextlib.contextmanager
def silence_stdout():
    old_target, sys.stdout = sys.stdout, open(os.devnull, "w")
    try:
        yield
    finally:
        sys.stdout = old_target


def get_pipeline(watson_settings, credentials, addr):
    return [
        watson_streaming.Transcriber(watson_settings, credentials),
        IBMWatsonAdapter(),
        nodes.Logger(addr),
        DeepTaggerModule(),
        nodes.DisfluenciesFilter(),
        nodes.ChangeFilter(),
    ]


def handler(conn, addr, watson_settings, credentials):
    print(addr, 'connected')

    with silence_stdout():
        pipeline = get_pipeline(watson_settings, credentials, addr)

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


def parse_arguments(args):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--credentials', default='credentials.json',
        help='Path to Watson credentials file (default: credentials.json)',
    )
    parser.add_argument(
        '--watson-settings', default='watson_settings.json',
        help='Path to Watson settings file (default: watson_settings.json)',
    )
    parser.add_argument(
        '--port', default=50007,
        help='TCP port (default: 50007)',
    )
    return parser.parse_args()


def main():
    args = parse_arguments(sys.argv[1:])
    with open(args.watson_settings) as f:
        watson_settings = json.load(f)
    with contextlib.closing(socket.socket(*SOCKET_SETTINGS)) as sock:
        sock.bind((HOST, args.port))
        sock.listen(1)
        print('Server listening')

        while True:
            conn, addr = sock.accept()
            handler_args = [conn, addr, watson_settings, args.credentials]
            handler_thread = threading.Thread(target=handler, args=handler_args)
            handler_thread.daemon = True
            handler_thread.start()


if __name__ == '__main__':
    main()
