import bcrypt
from pydantic import BaseModel
from enum import Enum

from connection.CouchbaseConnection import CouchbaseConnection
from connection.Neo4jConnection import Neo4jConnection

class TipoUsuario(int, Enum):
    aluno = 0,
    professor = 1

class Usuario(BaseModel):
    cpf: str
    login_usuario: str
    nome_usuario: str
    email_usuario: str = ""
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

    def user_exists(self, conn: CouchbaseConnection):
        response = {"error": False, "message": ""}
        
        result = conn.userExists(self.dict())

        for row in result:
            if row['cpf'] > 0:
                response['error'] = True
                response['message'] = "CPF already registered"
                print(response['message'])
                break
            elif row['login'] > 0:
                response['error'] = True
                response['message'] = "Login already registered"
                print(response['message'])
                break
            elif row['email'] > 0:
                response['error'] = True
                response['message'] = "Email already registered"
                print(response['message'])

        return response

    def create_document(self, key: str, connC: CouchbaseConnection, connN: Neo4jConnection):
        connC.insert('usuario', key, self.dict())

        query = '''CREATE (n:Usuario {id: "%s", login_usuario: "%s"}) RETURN n''' %(key, self.login_usuario)  
        connN.query(query)

        return self

class UsuarioLogin(BaseModel):
    login_usuario: str
    senha_usuario: str

    def retrieve_user(self, conn: CouchbaseConnection):
        return conn.getUser(self.login_usuario)
            
    def check_password(self, text: str):
        return bcrypt.checkpw(text.encode('utf-8'), self.senha_usuario.encode('utf-8'))