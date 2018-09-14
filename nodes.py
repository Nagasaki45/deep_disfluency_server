import json

import fluteline



class ChangeFilter(fluteline.SynchronousConsumer):
    '''
    Filter out updates when the tag doesn't change.
    '''
    def __init__(self):
        super(ChangeFilter, self).__init__()
        self.tags = {}  # ID to disf_tag

    def consume(self, item):
        previous_tag = self.tags.get(item['id'])
        if item['disf_tag'] != previous_tag:
            self.tags[item['id']] = item['disf_tag']
            self.output.put(item)


class DisfluenciesFilter(fluteline.SynchronousConsumer):
    '''
    Filter out everything but disfluent words.
    '''
    disfluent_tags = [
        '<e',
        '<rps',
    ]

    def consume(self, item):
        for disfluent_tag in self.disfluent_tags:
            if item['disf_tag'].startswith(disfluent_tag):
                self.output.put(item)
                break


class Responder(fluteline.Consumer):
    def __init__(self, conn):
        super(Responder, self).__init__()
        self.conn = conn

    def consume(self, item):
        msg = json.dumps(item)
        self.conn.sendall(msg + '\n')
