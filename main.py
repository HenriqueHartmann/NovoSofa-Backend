import os
import re
from dotenv import load_dotenv
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseSettings
from connection.CouchbaseConnection import CouchbaseConnection
from connection.Neo4jConnection import Neo4jConnection
from models.Usuario import Usuario, UsuarioLogin
from models.Token import Token, ValidateToken
import uuid

load_dotenv()

class Settings(BaseSettings):
    couchUri: str
    couchUser: str
    couchPwd: str
    neoUri:str
    neoUser: str
    neoPwd: str

settings = Settings(
    couchUri=os.getenv('COUCHURI'),
    couchUser=os.getenv('COUCHUSER'),
    couchPwd=os.getenv('COUCHPWD'),
    neoUri=os.getenv('NEOURI'),
    neoUser=os.getenv('NEOUSER'),
    neoPwd=os.getenv('NEOPWD')
)

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Couchbase
couchConn = CouchbaseConnection(uri=settings.couchUri, user=settings.couchUser, pwd=settings.couchPwd)

# Neo4j
neoConn = Neo4jConnection(uri=settings.neoUri, user=settings.neoUser, pwd=settings.neoPwd)

@app.post("/Login", response_model=List[Token], status_code=200) # Atualizar token document ao invés de criar um novo. Possibilidade de criar histórico no neo4j.
def login(data: UsuarioLogin, response: Response):
    body = []

    query = '''SELECT a.login_usuario, a.senha_usuario 
               FROM `novosofa`.project.usuario a 
               WHERE a.login_usuario = "%s"
            ''' %(data.login_usuario)

    query_result = couchConn.query(query)
    for item in query_result:
        user = UsuarioLogin(
            login_usuario=item['login_usuario'],
            senha_usuario=item['senha_usuario']
        )

        if user.check_password(data.senha_usuario):
            token = Token(usuario_ref=data.login_usuario)
            idToken = uuid.uuid1()
            token.create_access_token({"login": data.login_usuario, "id": str(idToken)})

            if token.token_document_exist(data.login_usuario, couchConn):
                response = token.update_document(couchConn)
            else:
                uuidOne = uuid.uuid1()
                response = token.create_document(uuidOne, couchConn, neoConn)
                
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

    cpf_query = '''SELECT COUNT(a.cpf) 
                   FROM `novosofa`.project.usuario a 
                   WHERE a.cpf = "%s"''' %(user.cpf)
    cpf_query_res = couchConn.query(cpf_query)
    for row in cpf_query_res: 
        if row['$1'] > 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            print("CPF (%s) already registered" %(user.cpf))
            return body

    login_query = '''SELECT COUNT(a.login_usuario) 
                     FROM `novosofa`.project.usuario a 
                     WHERE a.login_usuario = "%s"''' %(user.login_usuario)
    login_query_res = couchConn.query(login_query)

    for row in login_query_res:
        if row['$1'] > 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            print("Login (%s) already registered" %(user.login_usuario))
            return body 

    user.encrypt()
    uuidOne = uuid.uuid1()

    coach_query = '''INSERT INTO `novosofa`.project.usuario (KEY, VALUE) 
                     VALUES ("%s", {"cpf": "%s", "login_usuario": "%s", "nome_usuario": "%s", "senha_usuario": "%s", "tipo_usuario": %d }) 
                     RETURNING *''' %(uuidOne, user.cpf, user.login_usuario, user.nome_usuario, user.senha_usuario, user.tipo_usuario)
    coach_query_result = couchConn.query(coach_query)
    for item in coach_query_result:
        response = Usuario(
            cpf=item['usuario']['cpf'],
            login_usuario=item['usuario']['login_usuario'],
            nome_usuario=item['usuario']['nome_usuario'],
            senha_usuario=item['usuario']['senha_usuario'],
            tipo_usuario=item['usuario']['tipo_usuario']
        )
        body.append(response)
    
    neo_query = '''CREATE (n:Usuario {id: "%s", login_usuario: "%s"}) RETURN n''' %(uuidOne, user.login_usuario)
    neo_query_result = neoConn.query(neo_query)
    for item in neo_query_result:
        print(item)

    return body

@app.get("/Usuarios", response_model=List[Usuario], status_code=200)
def get_all_users(token: str, response: Response):
    body = []

    token_is_valid = ValidateToken(token=token).validate_token(couchConn)
    if (token_is_valid is False):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        print('Token is Invalid')
        return body

    query_result = couchConn.query('''SELECT * FROM `novosofa`.project.usuario''')
    for item in query_result:
        user = Usuario(
            cpf=item['usuario']['cpf'],
            login_usuario=item['usuario']['login_usuario'],
            nome_usuario=item['usuario']['nome_usuario'],
            senha_usuario=item['usuario']['senha_usuario'],
            tipo_usuario=item['usuario']['tipo_usuario']
        )
        body.append(user)
    
    return body

@app.get("/Usuario", response_model=List[Usuario])
def get_user(login: str, token: str, response: Response):
    body = []

    token_is_valid = ValidateToken(token=token).validate_token(couchConn)
    if (token_is_valid is False):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        print('Token is Invalid')
        return body

    query = '''SELECT * FROM `novosofa`.project.usuario WHERE login_usuario = "%s"''' %(login)
    query_result = couchConn.query(query)
    for item in query_result:
        user = Usuario(
            cpf=item['usuario']['cpf'],
            login_usuario=item['usuario']['login_usuario'],
            nome_usuario=item['usuario']['nome_usuario'],
            senha_usuario=item['usuario']['senha_usuario'],
            tipo_usuario=item['usuario']['tipo_usuario']
        )
        body.append(user)
    
    return body
