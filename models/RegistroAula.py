from pydantic import BaseModel

class RegistroAula(BaseModel):
    dt_aula: str
    descricao_aula: str