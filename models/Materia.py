from pydantic import BaseModel

class Materia(BaseModel):
    id: int
    ch_materia: int
    descricao_materia: str
