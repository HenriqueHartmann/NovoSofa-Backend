import json
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

    def get(self, collection: str, key):
        response = []
        bucket = self.__cluster.bucket("novosofa")
        coll = bucket.scope("project").collection(collection)
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = coll.get(key)
        except Exception as e:
            print('ERRO:')
            print(e)

        return response

    def insert(self, collection: str, key: str, doc: dict):
        response = ""
        bucket = self.__cluster.bucket("novosofa")
        coll = bucket.scope("project").collection(collection)
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = coll.insert(key, doc)
        except Exception as e:
            print('ERRO:')
            print(e)

        return response
    
    def insert_multi(self, collection: str, keys: dict):
        response = ""
        bucket = self.__cluster.bucket("novosofa")
        coll = bucket.scope("project").collection(collection)
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = coll.insert_multi(keys)
        except Exception as e:
            print('ERRO:')
            print(e)

        return response

    def replace(self, collection: str, id: str, data: dict):
        bucket = self.__cluster.bucket("novosofa")
        coll = bucket.scope("project").collection(collection)
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            coll.replace(id, data)
        except Exception as e:
            print('ERRO:')
            print(e)

    def getAllUsers(self):
        response = []
        query = '''SELECT * FROM `novosofa`.project.usuario'''

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = self.__cluster.query(query)

            for row in result:
                response.append(row['usuario'])
        except ParsingFailedException as ex:
            print(ex)

        return response

    def getUser(self, login: str):
        response = ""
        query = '''SELECT * 
                    FROM `novosofa`.project.usuario
                    WHERE login_usuario = $login'''
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = self.__cluster.query(query, QueryOptions(named_parameters={"login": login}))

            for row in result:
                response = row['usuario']
        except ParsingFailedException as ex:
            print(ex)

        return response

    def userExists(self, user: dict):
        response = []
        query = '''SELECT (
                        SELECT RAW COUNT(email_usuario)
                        FROM `novosofa`.project.usuario
                        WHERE email_usuario = $email)[0]
                        AS email,
                    (
                        SELECT RAW COUNT(login_usuario)
                        FROM `novosofa`.project.usuario
                        WHERE login_usuario = $login )[0] 
                        AS login,
                    (
                        SELECT RAW COUNT(cpf)
                        FROM `novosofa`.project.usuario
                        WHERE cpf = $cpf)[0]
                        AS cpf'''
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = self.__cluster.query(query, QueryOptions(named_parameters={"email": user['email_usuario'],"login": user['login_usuario'], "cpf": user['cpf']}))

        except ParsingFailedException as ex:
            print(ex)

        return response

    def getTokenId(self, login: str):
        response = ""
        query = '''SELECT RAW META().id 
                    FROM `novosofa`.project.token 
                    WHERE `usuario_ref` = $login'''
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = self.__cluster.query(query, QueryOptions(named_parameters={"login": login}))

            for row in result:
                response = row
        except ParsingFailedException as ex:
            print(ex)

        return response
    
    def tokenExists(self, token):
        response = False
        query = '''SELECT (
                    SELECT RAW COUNT(*)
                    FROM `novosofa`.project.token t
                    WHERE t.token = $token)[0] as count'''

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = self.__cluster.query(query, QueryOptions(named_parameters={"token": token}))
            for row in result:
                if row['count'] > 0:
                    response = True
        except ParsingFailedException as ex:
            print(ex)

        return response

    def tokenExistsByLogin(self, login:str):
        response = False
        query = '''SELECT RAW COUNT(*) FROM `novosofa`.project.token WHERE usuario_ref = $login'''

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = self.__cluster.query(query, QueryOptions(named_parameters={"login": login}))

            for row in result:
                if row > 0:
                    response = True
        except ParsingFailedException as ex:
            print(ex)

        return response

    def getTokenExpireDatetime(self, login: str):
        response = ""
        query = '''SELECT expire, 
                   (SELECT RAW COUNT(*) 
                        FROM `novosofa`.project.token t 
                        WHERE t.usuario_ref = $login)[0] as count 
                    FROM `novosofa`.project.token 
                    WHERE usuario_ref = $login'''
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = self.__cluster.query(query, QueryOptions(named_parameters={"login": login}))

            for row in result:
                response = row
        except ParsingFailedException as ex:
            print(ex)

        return response

    def populateCourseGangSubject(self):
        f = open('populate.json')
        data = json.load(f)

        self.insert_multi('materia', data['subjects'])
        self.insert_multi('turma', data['gangs'])
        self.insert_multi('curso', data['courses'])

        f.close()
               