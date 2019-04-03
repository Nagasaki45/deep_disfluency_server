import json
import time

import fluteline


class Logger(fluteline.SynchronousConsumer):
    '''
    Log messages.
    '''
    def __init__(self, addr):
        super(Logger, self).__init__()
        ip, port = addr
        ip = ip.replace('.', '-')
        now = time.strftime("%Y%m%d-%H%M%S")
        self.filename = '{}_{}_{}.log'.format(now, ip, port)

    def enter(self):
        self.file = open(self.filename, 'a')

    def exit(self):
        self.file.close()

    def consume(self, item):
        json.dump(item, self.file)
        self.file.write('\n')
        self.output.put(item)


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


class Profiler(fluteline.SynchronousConsumer):
    '''
    Add a timestamp to incoming messages.
    '''
    def __init__(self, key):
        super(Profiler, self).__init__()
        self.key = key

    def consume(self, item):
        item[self.key] = time.time()
        self.output.put(item)
