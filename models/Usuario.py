from pydantic import BaseModel

class Usuario(BaseModel):
    id: int
    cpf: str
    login_usuario: str
    nome_usuario: str
    senha_usuario: str
    tipo_usuario: str