# Deep Disfluency Server

This project exposes the [deep_disfluency](https://github.com/dsg-bielefeld/deep_disfluency/) tagger - a deep learning tagger for speech disfluencies - as a TCP server.

Connect to the server, wait for a "ready" message, and start sending raw audio.
The server transcribes the audio with the help of IBM Watson, and sends tagged words in response.
For more information about the tagging check the [deep_disfluency](https://github.com/dsg-bielefeld/deep_disfluency/) package.

## Installation

- Obtain a `credentials.json` file from IBM Watson as described [here](https://watson-streaming.readthedocs.io/en/latest/installation.html), and put it in the project directory.
- Install dependencies with `pip install -r requirements.txt`. Suggestion: use [`pip-tools`](https://github.com/jazzband/pip-tools/) inside a virtual environment instead.
- `python server.py`

## `client.py`

The `client.py` script is a full demo client for the server, and a good reference for implementing your own clients.
Check it out!

## Configuration

The entire configuration is hard coded in `server.py` ATM.
Change the values there for your needs, or send a pull request with a better configuration mechanism :wink:
