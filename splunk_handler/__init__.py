import logging
import socket
import traceback

from threading import Thread

import requests


class SplunkHandler(logging.Handler):
    """
    A logging handler to send events to a Splunk Enterprise instance
    """

    def __init__(self, host, port, username, password, index, hostname=None, source=None, sourcetype='json'):

        logging.Handler.__init__(self)

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.index = index
        self.source = source
        self.sourcetype = sourcetype

        if hostname is None:
            self.hostname = socket.gethostname()
        else:
            self.hostname = hostname

        # prevent infinite recursion by silencing requests logger
        requests_log = logging.getLogger('requests')
        requests_log.propagate = False

    def emit(self, record):

        thread = Thread(target=self._async_emit, args=(record, ))

        thread.start()

    def _async_emit(self, record):

        try:

            if self.source is None:
                source = record.pathname
            else:
                source = self.source

            params = {
                'host': self.hostname,
                'index': self.index,
                'source': source,
                'sourcetype': self.sourcetype
            }
            url = 'https://%s:%s/services/receivers/simple' % (self.host, self.port)
            payload = self.format(record)
            auth = (self.username, self.password)

            r = requests.post(
                url,
                auth=auth,
                data=payload,
                params=params
            )

            r.close()

        except Exception, e:

            print "Traceback:\n" + traceback.format_exc()
            print "Exception in Splunk logging handler: %s" % str(e)

