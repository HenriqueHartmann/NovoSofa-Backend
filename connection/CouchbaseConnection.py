from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, QueryOptions
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
            response = self.__cluster.query(query, QueryOptions())
        except Exception as e:
            print("Query failed: ", e)

        return response

    def getTokenId(self, login: str):
        query = '''SELECT META().id 
        FROM `novosofa`.project.token 
        WHERE usuario_ref = "%s"''' %(login)

        doc_id = ""
        result = self.__cluster.query(query)
        for item in result:
            doc_id = item['id']

        return doc_id

    def replace(self, collection: str, id: str, data: dict):
        bucket = self.__cluster.bucket("novosofa")
        coll = bucket.scope("project").collection(collection)
        try:
            coll.replace(id, data)
            print('LOGIN EFETUADO')
        except Exception as e:
            print('ERRO:')
            print(e)    
