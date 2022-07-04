from typing import List
from pydantic import BaseModel
from connection.Neo4jConnection import Neo4jConnection

from models.Token import ValidateToken


class VinculoRequest(BaseModel):
    course: str
    materia: List[str]

    def bind_graduation(self, token: str, conn: Neo4jConnection):
        vToken = ValidateToken(
            token=token
        )
        login = vToken.decode_token()
        
        conn.bindGraduationStudent(self.course, login, self.dict())
        

