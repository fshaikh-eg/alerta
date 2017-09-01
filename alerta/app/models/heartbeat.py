
import os
import sys
import platform

from datetime import datetime
from uuid import uuid4

from flask import current_app

from alerta.app import db
from alerta.app.utils.api import absolute_url
from alerta.app.utils.format import DateTime


class Heartbeat(object):

    def __init__(self, origin=None, tags=None, create_time=None, timeout=None, customer=None, **kwargs):

        self.id = kwargs.get('id', str(uuid4()))
        self.origin = origin or '%s/%s' % (os.path.basename(sys.argv[0]), platform.uname()[1])
        self.tags = tags or list()
        self.event_type = kwargs.get('event_type', kwargs.get('type', None)) or 'Heartbeat'
        self.create_time = create_time or datetime.utcnow()
        self.timeout = timeout or current_app.config['DEFAULT_HEARTBEAT_TIMEOUT']
        self.receive_time = kwargs.get('receive_time', None) or datetime.utcnow()
        self.customer = customer

    @classmethod
    def parse(cls, json):
        if not isinstance(json.get('tags', []), list):
            raise ValueError('tags must be a list')
        if not isinstance(json.get('timeout', 0), int):
            raise ValueError('timeout must be an integer')

        return Heartbeat(
            origin=json.get('origin', None),
            tags=json.get('tags', list()),
            create_time=DateTime.parse(json.get('createTime')),
            timeout=json.get('timeout', None),
            customer=json.get('customer', None)
        )

    @property
    def serialize(self):
        return {
            'id': self.id,
            'href': absolute_url('/heartbeat/' + self.id),
            'origin': self.origin,
            'tags': self.tags,
            'type': self.event_type,
            'createTime': self.create_time,
            'timeout': self.timeout,
            'receiveTime': self.receive_time,
            'customer': self.customer
        }

    def __repr__(self):
        return 'Heartbeat(id=%r, origin=%r, create_time=%r, timeout=%r, customer=%r)' % (
            self.id, self.origin, self.create_time, self.timeout, self.customer)

    @classmethod
    def from_document(cls, doc):
        return Heartbeat(
            id=doc.get('id', None) or doc.get('_id'),
            origin=doc.get('origin', None),
            tags=doc.get('tags', list()),
            event_type=doc.get('type', None),
            create_time=doc.get('createTime', None),
            timeout=doc.get('timeout', None),
            receive_time=doc.get('receiveTime', None),
            customer=doc.get('customer', None)
        )

    @classmethod
    def from_record(cls, rec):
        return Heartbeat(
            id=rec.id,
            origin=rec.origin,
            tags=rec.tags,
            event_type=rec.type,
            create_time=rec.create_time,
            timeout=rec.timeout,
            receive_time=rec.receive_time,
            customer=rec.customer
        )

    @classmethod
    def from_db(cls, r):
        if isinstance(r, dict):
            return cls.from_document(r)
        elif isinstance(r, tuple):
            return cls.from_record(r)
        else:
            return

    # create/update a heartbeat
    def create(self):
        return Heartbeat.from_db(db.upsert_heartbeat(self))

    # retrieve an heartbeat
    @staticmethod
    def get(id, customer=None):
        return Heartbeat.from_db(db.get_heartbeat(id, customer))

    # search heartbeats
    @staticmethod
    def find_all(query=None, page=1, page_size=100):
        return [Heartbeat.from_db(heartbeat) for heartbeat in db.get_heartbeats(query, page, page_size)]

    # delete a heartbeat
    def delete(self):
        return db.delete_heartbeat(self.id)
