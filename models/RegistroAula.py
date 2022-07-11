from pydantic import BaseModel

from connection.CouchbaseConnection import CouchbaseConnection
from connection.Neo4jConnection import Neo4jConnection

class RegistroAula(BaseModel):
    dt_aula: str
    descricao_aula: str
    curso: str
    turma: str
    materia: str

    def create_document(self, key: str, connC: CouchbaseConnection, connN: Neo4jConnection):
        query = ''
        # connC.insert('curso', key, self.dict())

        # query = '''CREATE (n:Curso {id: "%s", nome_curso: "%s"}) RETURN n''' %(key, self.nome_curso)  
        # connN.query(query)