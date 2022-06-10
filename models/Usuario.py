import bcrypt
from pydantic import BaseModel
from enum import Enum

class TipoUsuario(int, Enum):
    aluno = 0,
    professor = 1

class Usuario(BaseModel):
    cpf: str
    login_usuario: str
    nome_usuario: str
    senha_usuario: str
    tipo_usuario: TipoUsuario = TipoUsuario.aluno

    def encrypt(self):
        salt = bcrypt.gensalt()
        hash = bcrypt.hashpw(self.senha_usuario.encode('utf-8'), salt)
        self.senha_usuario = hash.decode("utf-8")
    
    def format_cpf(self, cpf:str):
        one = cpf[:3]
        two = cpf[3:6]
        three = cpf[6:9]
        four = cpf[9:]

        self.cpf =  "{}.{}.{}-{}".format(
            one,
            two,
            three,
            four
        )

class UsuarioLogin(BaseModel):
    login_usuario: str
    senha_usuario: str

    def check_password(self, text: str):
        return bcrypt.checkpw(text.encode('utf-8'), self.senha_usuario.encode('utf-8'))