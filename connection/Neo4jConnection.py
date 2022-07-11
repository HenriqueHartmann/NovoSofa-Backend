from typing import List
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

    def getCourseSubjects(self, keyWord: str, type: int, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None

        query = '''MATCH (n:Curso)-[r]->(m:Materia) WHERE n.palavra_chave = '%s' AND m.tipo = %d RETURN m''' %(keyWord, type)

        try:
            session = self.__driver.session(database=db) if db is not None else self.__driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed: ", e)
        finally:
            if session is not None:
                session.close()
        return response

    def getCourseGangs(self, keyWord: str, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None

        query = '''MATCH (c:Curso)-[r]->(t:Turma) WHERE c.palavra_chave = '%s' RETURN t''' %(keyWord)

        try:
            session = self._driver.session(database=db) if db is not None else self._driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed: ", e)
        finally:
            if session is not None:
                session.close()
        return response

    def getSubjectsGangs(self, course:str, subjects: List[str], parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None

        if len(subjects) == 1:
            query = '''MATCH (c:Curso)-[r0]->(t:Turma), (m:Materia)-[r1]->(t) WHERE c.palavra_chave = "%s" AND m.key = "%s" RETURN t''' %(course, subjects[0])
        else:
            query = '''MATCH (c:Curso)-[r0]->(t:Turma), (m:Materia)-[r1]->(t) WHERE c.palavra_chave = "%s" AND ''' %(course)

            conditions = '('
            for i, m in enumerate(subjects):
                separator = ' OR '

                if i == 0:
                    separator = ''
                    conditions = separator.join([conditions, '''m.key = "%s"''' %(m)])
                elif i == len(subjects) - 1:
                    conditions = separator.join([conditions, '''m.key = "%s")''' %(m)])
                else:
                    conditions = separator.join([conditions, '''m.key = "%s"''' %(m)])

            query = ''.join([query, conditions, ' RETURN DISTINCT t'])

        try:
            session = self.__driver.session(database=db) if db is not None else self.__driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed: ", e)
        finally:
            if session is not None:
                session.close()
        return response

    def getStudentBinds(self, login: str, userType: int, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        query = ''
        
        if userType == 1:
            query = '''MATCH (u:Usuario)-[r0]->(c:Curso), (u)-[r1]->(m:Materia), (c)-[r2]->(t:Turma)-[r3]->(m) WHERE u.login_usuario = "%s" RETURN DISTINCT u, c, m, t''' %(login)
        else:
            query = '''MATCH (u:Usuario)-[r0]->(c:Curso), (u)-[r1]->(m:Materia), (u)-[r2]->(t:Turma) WHERE u.login_usuario = "%s" RETURN DISTINCT u, c, m, t''' %(login)

        try:
            session = self.__driver.session(database=db) if db is not None else self.__driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed: ", e)
        finally:
            if session is not None:
                session.close()
        return response

    def bindGraduationStudent(self, login: str, data: dict, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        
        query = '''MATCH (u:Usuario) WHERE u.login_usuario = "%s" MATCH (c:Curso)-[r]->(m:Materia), (m)-[r1]->(t:Turma) WHERE c.palavra_chave = "%s" AND ''' %(login, data['curso'])
        separator = ''
        create = ''' MERGE (u)-[:MATRICULADO]->(c) MERGE (u)-[:INSCREVE_MATERIA]->(m)'''

        if len(data['materias']) == 1:
            query = separator.join([query, '''m.key = "%s"''' %(data['materia'][0])])
        else:
            conditions = ''

            for i, m in enumerate(data["materias"]):
                if i == 0:
                    conditions = separator.join([conditions, '''(m.key = "%s" OR ''' %(m)])
                elif i == (len(data['materias']) - 1):
                    conditions = separator.join([conditions, '''m.key = "%s")''' %(m)])
                else:
                    conditions = separator.join([conditions, '''m.key = "%s OR "''' %(m)])
                    
            query = separator.join([query, conditions])

        query = separator.join([query, create])

        try:
            session = self.__driver.session(database=db) if db is not None else self.__driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed: ", e)
        finally:
            if session is not None:
                session.close()
        return response

    def bindProfessor(self, login: str, data: dict, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        
        query = '''MATCH (u:Usuario) WHERE u.login_usuario = "%s" MATCH (c:Curso)-[r]->(m:Materia), (m)-[r1]->(t:Turma) WHERE ''' %(login)
        separator = ''
        courses = ''
        subjects = ''
        gangs = ''
        create = '''MERGE (u)-[:CONTRATADO_PARA]->(c) MERGE (u)-[:LECIONA_MATERIA]->(m) MERGE (u)-[:LECIONA_TURMA]->(t)''' # TODO: Adicionar atributos nos relacionamentos, ou criar novos nós com esses atributos

        if len(data['cursos']) == 1:
            separator.join([courses, '''c.palavra_chave = "%s" AND ''' %(data['curso'][0])])
        else:
            for i, c in enumerate(data['cursos']):
                if i == 0:
                    courses = separator.join([courses, '''(c.palavra_chave = "%s" OR ''' %(c)])
                elif i == (len(data['cursos']) - 1):
                    courses = separator.join([courses, '''c.palavra_chave = "%s") AND ''' %(c)])
                else:
                    courses = courses.join([courses, '''c.palavra_chave = "%s OR "''' %(c)])

        if len(data['materias']) == 1:
            query = separator.join([query, '''m.key = "%s" AND ''' %(data['materias'][0])])
        else:
            subjects = ''

            for i, m in enumerate(data["materias"]):
                if i == 0:
                    subjects = separator.join([subjects, '''(m.key = "%s" OR ''' %(m)])
                elif i == (len(data['materias']) - 1):
                    subjects = separator.join([subjects, '''m.key = "%s") AND ''' %(m)])
                else:
                    subjects = separator.join([subjects, '''m.key = "%s OR "''' %(m)])

        if len(data['turmas']) == 1:
            gangs = separator.join([gangs, '''t.key = "%s"''' %(data['turmas'][0])])
        else:
            gangs = ''

            for i, t in enumerate(data["turmas"]):
                if i == 0:
                    gangs = separator.join([gangs, '''(t.key = "%s" OR ''' %(t)])
                elif i == (len(data['turmas']) - 1):
                    gangs = separator.join([gangs, '''t.key = "%s") ''' %(t)])
                else:
                    gangs = separator.join([gangs, '''t.key = "%s OR "''' %(t)])

        query = separator.join([query, courses, subjects, gangs, create])
        print(query)

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

        query = '''CREATE (curso1:Curso {key:"623d9d86-f807-11ec-bb60-7c70db79db90", palavra_chave:"Bacharelado em Sistemas de Informação"}),
            (curso2:Curso {key:"6666f22f-f807-11ec-b6e4-7c70db79db90", palavra_chave:"Redes"}),
            (curso3:Curso {key:"6a984261-f807-11ec-b1f8-7c70db79db90", palavra_chave:"Técnico em Informática"}),
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