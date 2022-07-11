from typing import List
from pydantic import BaseModel
from connection.Neo4jConnection import Neo4jConnection
from models.Curso import Curso
from models.Materia import MateriaRequest

from models.Token import ValidateToken
from models.Turma import Turma
from models.Usuario import Usuario


class VinculoRequest(BaseModel):
    curso: str
    materias: List[str]

    def bind_graduation(self, token: str, conn: Neo4jConnection):
        vToken = ValidateToken(
            token=token
        )
        login = vToken.decode_token()
        
        conn.bindGraduationStudent(login, self.dict())

class ProfessorVinculoRequest(BaseModel):
    cursos: List[str]
    materias: List[str]
    turmas: List[str]

    def bind_professor(self, token: str, conn: Neo4jConnection):
        vToken = ValidateToken(
            token=token
        )
        login = vToken.decode_token()
        
        conn.bindProfessor(login, self.dict())
        
class VinculoResponse(BaseModel):
    usuario: Usuario
    curso: Curso
    materias: List[MateriaRequest]
    turmas: List[Turma]
