from typing import List
from pydantic import BaseModel

from connection.CouchbaseConnection import CouchbaseConnection
from connection.Neo4jConnection import Neo4jConnection
from models.Turma import TurmaMateriasResponse, TurmaMateriasSimple

class Curso(BaseModel):
    nome_curso: str
    ch_curso: int

    def create_document(self, key: str, connC: CouchbaseConnection, connN: Neo4jConnection):
        connC.insert('curso', key, self.dict())

        query = '''CREATE (n:Curso {id: "%s", nome_curso: "%s"}) RETURN n''' %(key, self.nome_curso)  
        connN.query(query)

class CursoResponse(BaseModel):
    curso: Curso
    turmas: List[TurmaMateriasResponse] = []

class CursoTurmaMateria(BaseModel):
    id: int
    key: str
    turmas: List[TurmaMateriasSimple] = []
