from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, QueryOptions
from couchbase.auth import PasswordAuthenticator
from couchbase.exceptions import ParsingFailedException
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

    def insert(self, collection: str, key: str, doc: dict):
        bucket = self.__cluster.bucket("novosofa")
        coll = bucket.scope("project").collection(collection)
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            coll.insert(key, doc)
        except Exception as e:
            print('ERRO:')
            print(e)

    def replace(self, collection: str, id: str, data: dict):
        bucket = self.__cluster.bucket("novosofa")
        coll = bucket.scope("project").collection(collection)
        try:
            coll.replace(id, data)
            print('LOGIN EFETUADO')
        except Exception as e:
            print('ERRO:')
            print(e)

    def getTokenId(self, login: str):
        response = ''
        query = '''SELECT RAW META().id 
                    FROM `novosofa`.project.token 
                    WHERE `usuario_ref` = $login'''
        
        try:
            result = self.__cluster.query(query, QueryOptions(named_parameters={"login": login}))

            for row in result:
                response = row
        except ParsingFailedException as ex:
            print(ex)

        return response

    def getTokenExpireDatetime(self, login: str):
        response = ''
        query = '''SELECT expire, 
                   (SELECT RAW COUNT(*) 
                        FROM `novosofa`.project.token t 
                        WHERE t.usuario_ref = $login)[0] as count 
                    FROM `novosofa`.project.token 
                    WHERE usuario_ref = $login'''
        
        try:
            result = self.__cluster.query(query, QueryOptions(named_parameters={"login": login}))

            for row in result:
                response = row
        except ParsingFailedException as ex:
            print(ex)

        return response