from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.auth import PasswordAuthenticator
import asyncio

class CouchbaseConnection:

    def __init__(self, uri, user, pwd):
        self.__uri = uri
        self.__user = user
        self.__pwd = pwd
        self.__cluster = None

        try:
            self.__cluster = Cluster(
                self.__uri,
                ClusterOptions(
                    PasswordAuthenticator(
                        self.__user,
                        self.__pwd
                    )
                )
            )
        except Exception as e:
            print("Failed to create the cluster: ", e)

    def query(self, query: str):
        assert self.__cluster is not None, "Cluster not initialized!"
        
        response = None
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = self.__cluster.query(query)
        except Exception as e:
            print("Query failed: ", e)

        return response
