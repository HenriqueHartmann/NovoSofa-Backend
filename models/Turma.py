from typing import List
from pydantic import BaseModel

from connection.CouchbaseConnection import CouchbaseConnection
from connection.Neo4jConnection import Neo4jConnection
from models.Materia import MateriaRequest, MateriaRequestKey


class Turma(BaseModel):
    descricao_turma: str
    dt_inicio: str
    dt_fim: str

    def create_document(self, key: str, connC: CouchbaseConnection, connN: Neo4jConnection):
        connC.insert('turma', key, self.dict())

        query = '''CREATE (n:Turma {id: "%s", descricao_turma: "%s"}) RETURN n''' %(key, self.descricao_turma)  
        connN.query(query)

class TurmaResponse(BaseModel):
    key: str = ""
    descricao_turma: str
    dt_inicio: str
    dt_fim: str

class TurmaMaterias(BaseModel):
    turma: Turma
    materias: List[MateriaRequest]

class TurmaMateriasSimple(BaseModel):
    turma: str = ""
    materias: List[str] = []

class TurmaMateriasResponse(BaseModel):
    turma: TurmaResponse
    materias: List[MateriaRequestKey]