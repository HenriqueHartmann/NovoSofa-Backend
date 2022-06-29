from enum import Enum
from pydantic import BaseModel

from connection.CouchbaseConnection import CouchbaseConnection
from connection.Neo4jConnection import Neo4jConnection

class TipoEnsino(int, Enum):
    medio = 0,
    superior = 1

class Materia(BaseModel):
    ch_materia: int
    descricao_materia: str
    tipo_ensino: TipoEnsino = TipoEnsino.medio

    def create_document(self, key: str, connC: CouchbaseConnection, connN: Neo4jConnection):
        connC.insert('turma', key, self.dict())

        query = '''CREATE (n:Materia {id: "%s", descricao_materia: "%s"}) RETURN n''' %(key, self.descricao_materia)  
        connN.query(query)
