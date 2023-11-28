from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.diagnostics import PingState
from couchbase.exceptions import (
    CouchbaseException,
    DocumentExistsException,
    DocumentNotFoundException,
)
from couchbase.options import ClusterOptions

class CouchbaseClient(object):
    def __init__(self, host, bucket, scope, collection, username, pw):
        self.host = host
        self.bucket_name = bucket
        self.collection_name = collection
        self.scope_name = scope
        self.username = username
        self.password = pw

    def connect(self, **kwargs):

        conn_str = f"couchbase://{self.host}"
        try:
            cluster_opts = ClusterOptions( authenticator=PasswordAuthenticator(self.username, self.password) )
            self._cluster = Cluster(conn_str, cluster_opts, **kwargs)
        except CouchbaseException as error:
            print(f"Could not connect to cluster. Error: {error}")
            raise
        self._bucket = self._cluster.bucket(self.bucket_name)
        self._collection = self._bucket.scope(self.scope_name).collection(self.collection_name)

    def get(self, key):
        return self._collection.get(key)

    def insert(self, key, doc):
        return self._collection.insert(key, doc)

    def upsert(self, key, doc):
        return self._collection.upsert(key, doc)

    def remove(self, key):
        return self._collection.remove(key)

    def query(self, strQuery, *options, **kwargs):
        return self._cluster.query(strQuery, *options, **kwargs)

