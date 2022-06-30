from neo4j import GraphDatabase

class Neo4jConnection:
    
    def __init__(self, uri, user, pwd):
        self.__uri = uri
        self.__user = user
        self.__pwd = pwd
        self.__driver = None
        try:
            self.__driver = GraphDatabase.driver(
                self.__uri,
                auth=(self.__user, self.__pwd))
        except Exception as e:
            print("Failed to create the driver:", e)

    def close(self):
        if self.__driver is not None:
            self.__driver.close()

    def query(self, query, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None

        try:
            session = self.__driver.session(database=db) if db is not None else self.__driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed: ", e)
        finally:
            if session is not None:
                session.close()
        return response

    def createToken(self, key: str, login: str, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None

        query = '''MATCH (n:Usuario) WHERE n.login_usuario = "%s"
                   CREATE (m:Token {id: "%s"}),
                   (n)-[:ACESSO]->(m)''' %(login, key)

        try:
            session = self.__driver.session(database=db) if db is not None else self.__driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed: ", e)
        finally:
            if session is not None:
                session.close()
        return response

    def getCourses(self, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None

        query = '''MATCH (n:Curso) RETURN n'''

        try:
            session = self.__driver.session(database=db) if db is not None else self.__driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed: ", e)
        finally:
            if session is not None:
                session.close()
        return response

    def getCourseSubjects(self, keyWord: str, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None

        query = '''MATCH (n:Curso)-[r]->(m:Materia) WHERE n.palavra_chave = '%s' RETURN m''' %(keyWord)

        try:
            session = self.__driver.session(database=db) if db is not None else self.__driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed: ", e)
        finally:
            if session is not None:
                session.close()
        return response

    def populateCourseGangSubject(self, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None

        query = '''CREATE (curso1:Curso {key:"623d9d86-f807-11ec-bb60-7c70db79db90", palavra_chave:"bsi"}),
            (curso2:Curso {key:"6666f22f-f807-11ec-b6e4-7c70db79db90", palavra_chave:"redes"}),
            (curso3:Curso {key:"6a984261-f807-11ec-b1f8-7c70db79db90", palavra_chave:"tecinfo"}),
            (turma1:Turma {key:"2ac45349-f807-11ec-be5a-7c70db79db90"}),
            (turma2:Turma {key:"30192744-f807-11ec-b2c6-7c70db79db90"}),
            (turma3:Turma {key:"37353618-f807-11ec-a2fd-7c70db79db90"}),
            (turma4:Turma {key:"3d0a5caa-f807-11ec-8b60-7c70db79db90"}),
            (turma5:Turma {key:"410bc255-f807-11ec-841c-7c70db79db90"}),
            (materia1:Materia {key:"e870c439-f806-11ec-ae76-7c70db79db90", tipo:1}),
            (materia2:Materia {key:"0b08c899-f807-11ec-baa6-7c70db79db90", tipo:1}),
            (materia3:Materia {key:"129c43ab-f807-11ec-b263-7c70db79db90", tipo:1}),
            (materia4:Materia {key:"1a770f24-f807-11ec-9118-7c70db79db90", tipo:0}),
            (materia5:Materia {key:"253dbb95-f807-11ec-ac9a-7c70db79db90", tipo:0}),
            (curso1)-[:POSSUI]->(turma1),
            (curso1)-[:POSSUI]->(turma2),
            (curso1)-[:POSSUI]->(turma3),
            (curso2)-[:POSSUI]->(turma4),
            (curso3)-[:POSSUI]->(turma5),
            (turma1)-[:TEM]->(materia1),
            (turma2)-[:TEM]->(materia3),
            (turma3)-[:TEM]->(materia2),
            (turma4)-[:TEM]->(materia1),
            (turma4)-[:TEM]->(materia3),
            (turma5)-[:TEM]->(materia4),
            (turma5)-[:TEM]->(materia5),
            (curso1)-[:POSSUI]->(materia1),
            (curso1)-[:POSSUI]->(materia2),
            (curso1)-[:POSSUI]->(materia3),
            (curso2)-[:POSSUI]->(materia1),
            (curso2)-[:POSSUI]->(materia3),
            (curso3)-[:POSSUI]->(materia4),
            (curso3)-[:POSSUI]->(materia5),
            (materia1)-[:TEM]->(turma1),
            (materia1)-[:TEM]->(turma4),
            (materia2)-[:TEM]->(turma3),
            (materia3)-[:TEM]->(turma2),
            (materia3)-[:TEM]->(turma4),
            (materia4)-[:TEM]->(turma5),
            (materia5)-[:TEM]->(turma5)
        '''

        try:
            session = self.__driver.session(database=db) if db is not None else self.__driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed: ", e)
        finally:
            if session is not None:
                session.close()
        return response