from pydantic import BaseModel

from connection.CouchbaseConnection import CouchbaseConnection
from connection.Neo4jConnection import Neo4jConnection
from models.Token import ValidateToken

class RegistroAula(BaseModel):
    dt_aula: str
    descricao_aula: str 

class RegistroAulaRequest(BaseModel):
    dt_aula: str
    descricao_aula: str
    curso: str
    turma: str
    materia: str

    def create_document(self, key: str, token: str, connC: CouchbaseConnection, connN: Neo4jConnection):
        record = RegistroAula(
            dt_aula=self.dt_aula,
            descricao_aula=self.descricao_aula
        )
        # connC.insert('registroAula', key, record.dict())

        vToken = ValidateToken(
            token=token
        )
        login = vToken.decode_token()

        connN.bindClassRecord(key, login, self.dict())
