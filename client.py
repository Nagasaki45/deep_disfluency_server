"""
A TCP client that listen to the computer sound card (e.g. microphone),
sends raw audio samples to a TCP server (implemented in
`asr_tcp_server_demo.py`) and receives disfluency tags.
"""
import contextlib
import json
import socket
import threading

import sounddevice

HOST = '127.0.0.1'
PORT = 50007
AUDIO_OPTS = {
    'dtype': 'int16',
    'samplerate': 44100,
    'channels': 1,
}
BUFFER_SIZE = 2048


def tcp_transmitter(sock, server_ready):
    server_ready.wait()
    with sounddevice.RawInputStream(**AUDIO_OPTS) as stream:
        while True:
            chunk, _ = stream.read(BUFFER_SIZE)
            sock.sendall(chunk[:])


def main():
    server_ready = threading.Event()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    with contextlib.closing(sock):

        t = threading.Thread(target=tcp_transmitter, args=(sock, server_ready))
        t.daemon = True
        t.start()

        sock_file = sock.makefile()
        with contextlib.closing(sock_file):
            while True:
                msg = json.loads(sock_file.readline())
                if msg.get('state') == 'ready':
                    server_ready.set()
                print(msg)


if __name__ == '__main__':
    main()
