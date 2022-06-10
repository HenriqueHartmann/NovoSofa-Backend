from datetime import timedelta
from fastapi import FastAPI, Response, status
from typing import List
from connection.CouchbaseConnection import CouchbaseConnection
from connection.Neo4jConnection import Neo4jConnection
from models.Usuario import Usuario, UsuarioLogin
from models.Token import Token
#from models.Materia import Materia
import uuid

app = FastAPI()

couchUri = "couchbase://localhost"
couchUser = "root"
couchPwd = "admin123"
couchConn = CouchbaseConnection(uri=couchUri, user=couchUser, pwd=couchPwd)

neoUri = "bolt://localhost:7687"
neoUser = "neo4j"
neoPwd = "root"
neoConn = Neo4jConnection(uri=neoUri, user=neoUser, pwd=neoPwd)

@app.post("/Login", response_model=List[Token], status_code=200)
def login(data: UsuarioLogin, response: Response):
    body = []

    query = '''SELECT a.login_usuario, a.senha_usuario  FROM `novosofa`.project.usuario a WHERE a.login_usuario = "%s"''' %(data.login_usuario)
    query_result = couchConn.query(query)
    for row in query_result:
        user = UsuarioLogin(
            login_usuario=row['login_usuario'],
            senha_usuario=row['senha_usuario']
        )
        if user.check_password(data.senha_usuario):
            token = Token(usuario_ref=data.login_usuario)
            token.create_access_token({"login": data.login_usuario})
            uuidOne = uuid.uuid1()
            
            query_token = '''INSERT INTO `novosofa`.project.token (KEY, VALUE) VALUES ("%s", {"usuario_ref": "%s", "token": "%s", "expire": "%s"}) RETURNING *''' %(uuidOne, token.usuario_ref, token.token, token.expire)
            query_token_result = couchConn.query(query_token)

            for row in query_token_result:
                response = Token(
                    usuario_ref=row['token']['usuario_ref'],
                    token=row['token']['token'],
                    expire=row['token']['expire'],
                )
                body.append(response)

            return body

    response.status_code = status.HTTP_404_NOT_FOUND
    return body

@app.post("/CriarNovoUsuario", response_model=List[Usuario], status_code=201)
def create_new_user(user: Usuario, response: Response):
    body = []

    cpf = [int(char) for char in user.cpf if char.isdigit()]

    if len(cpf) != 11 or cpf == cpf[::-1]:
        response.status_code = status.HTTP_400_BAD_REQUEST
        print("CPF is not valid")
        return body

    for i in range(9, 11):
        value = sum((cpf[num] * ((i+1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != cpf[i]:
            response.status_code = status.HTTP_400_BAD_REQUEST
            print("CPF is not valid")
            return body

    cpf = ''.join(map(str, cpf))
    user.format_cpf(cpf)

    cpf_query = '''SELECT COUNT(a.cpf)  FROM `novosofa`.project.usuario a WHERE a.cpf = "%s"''' %(user.cpf)
    cpf_query_res = couchConn.query(cpf_query)
    for row in cpf_query_res: 
        if row['$1'] > 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            print("CPF (%s) already registered" %(user.cpf))
            return body

    login_query = '''SELECT COUNT(a.login_usuario)  FROM `novosofa`.project.usuario a WHERE a.login_usuario = "%s"''' %(user.login_usuario)
    login_query_res = couchConn.query(login_query)
    for row in login_query_res:
        if row['$1'] > 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            print("Login (%s) already registered" %(user.login_usuario))
            return body 

    user.encrypt()
    uuidOne = uuid.uuid1()

    query = '''INSERT INTO `novosofa`.project.usuario (KEY, VALUE) VALUES ("%s", {"cpf": "%s", "login_usuario": "%s", "nome_usuario": "%s", "senha_usuario": "%s", "tipo_usuario": %d }) RETURNING *''' %(uuidOne, user.cpf, user.login_usuario, user.nome_usuario, user.senha_usuario, user.tipo_usuario)
    query_result = couchConn.query(query)
    for row in query_result:
        response = Usuario(
            cpf=row['usuario']['cpf'],
            login_usuario=row['usuario']['login_usuario'],
            nome_usuario=row['usuario']['nome_usuario'],
            senha_usuario=row['usuario']['senha_usuario'],
            tipo_usuario=row['usuario']['tipo_usuario']
        )
        body.append(response)
 
    return body

@app.get("/Usuarios", response_model=List[Usuario])
def get_all_users():
    body = []
    query_result = couchConn.query('''SELECT * FROM `novosofa`.project.usuario''')
    for row in query_result:
        user = Usuario(
            cpf=row['usuario']['cpf'],
            login_usuario=row['usuario']['login_usuario'],
            nome_usuario=row['usuario']['nome_usuario'],
            senha_usuario=row['usuario']['senha_usuario'],
            tipo_usuario=row['usuario']['tipo_usuario']
        )
        body.append(user)
    
    return body

@app.get("/Usuario", response_model=List[Usuario])
def get_user():
    body = []
    query_result = couchConn.query('''SELECT * FROM `novosofa`.project.usuario''')
    for row in query_result:
        user = Usuario(
            cpf=row['usuario']['cpf'],
            login_usuario=row['usuario']['login_usuario'],
            nome_usuario=row['usuario']['nome_usuario'],
            senha_usuario=row['usuario']['senha_usuario'],
            tipo_usuario=row['usuario']['tipo_usuario']
        )
        body.append(user)
    
    return body

"""
@app.get("/Materias", response_model=List[Materia])
def read_subject():
    materias = []
    queryReturn = neoConn.query('''MATCH (n: Materia) return n''')
    
    for item in queryReturn:
        materia = Materia(
            id=item['n'].id,
            ch_materia=item['n']['ch_materia'],
            descricao_materia=item['n']['descricao_materia']
        )
        materias.append(materia)

    return materias
"""    