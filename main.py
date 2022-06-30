import os
from dotenv import load_dotenv
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
from pydantic import BaseModel, BaseSettings
from connection.CouchbaseConnection import CouchbaseConnection
from connection.Neo4jConnection import Neo4jConnection
from models.Curso import Curso
from models.Materia import Materia
from models.Turma import Turma
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

class Message(BaseModel):
    message: str

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

# Endpoints
@app.post("/Login", response_model=List[Token], status_code=200)
def login(user: UsuarioLogin, response: Response):
    body = []
    
    result = user.retrieve_user(couchConn)

    if result != "":
        user_result = UsuarioLogin(
            login_usuario=result['login_usuario'],
            senha_usuario=result['senha_usuario']
        )

        if user_result.check_password(user.senha_usuario):
            token = Token(usuario_ref=user.login_usuario)
            key = str(uuid.uuid1())
            token.create_access_token({"login": user_result.login_usuario, "key": key})

            if token.token_document_exists(user_result.login_usuario, couchConn):
                response = token.update_document(couchConn)
            else:
                response = token.create_document(key, couchConn, neoConn)
            
            body.append(response)
        else:
            response.status_code = status.HTTP_403_FORBIDDEN
        return body

    response.status_code = status.HTTP_403_FORBIDDEN

    return body

@app.post("/CriarNovoUsuario", response_model=List[Usuario], response_model_exclude={"senha_usuario"}, responses={400: {"model": Message}}, status_code=201)
def create_new_user(user: Usuario, response: Response):
    body = []

    cpf = [int(char) for char in user.cpf if char.isdigit()]

    if len(cpf) != 11 or cpf == cpf[::-1]:
        response.status_code = status.HTTP_400_BAD_REQUEST
        print("CPF is not valid")
        
        return JSONResponse(status_code=400, content=[{"message": "CPF is not valid"}])

    for i in range(9, 11):
        value = sum((cpf[num] * ((i+1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != cpf[i]:
            response.status_code = status.HTTP_400_BAD_REQUEST
            print("CPF is not valid")
            return JSONResponse(status_code=400, content=[{"message": u"CPF is not valid"}])

    cpf = ''.join(map(str, cpf))
    user.format_cpf(cpf)
    user.encrypt()

    user_exists_result = user.user_exists(couchConn) 
    if user_exists_result["error"]:
        response.status_code = status.HTTP_400_BAD_REQUEST

        return JSONResponse(status_code=400, content=[{"message": user_exists_result['message']}])

    key = str(uuid.uuid1())
    user.create_document(key, couchConn, neoConn)
    body.append(user)

    return body

@app.get("/Usuarios", response_model=List[Usuario], response_model_exclude={"senha_usuario"}, responses={401: {"model": Message}}, status_code=200)
def get_all_users(token: str, response: Response):
    body = []

    token_is_valid = ValidateToken(token=token).validate_token(couchConn)
    if (token_is_valid is False):
        print('Token is Invalid')
        response.status_code = status.HTTP_401_UNAUTHORIZED

        return JSONResponse(status_code=400, content=[{"message": "Token is invalid"}])

    result = couchConn.getAllUsers()
    for row in result:
        user = Usuario(
            cpf=row['cpf'],
            login_usuario=row['login_usuario'],
            nome_usuario=row['nome_usuario'],
            email_usuario=returnKey(row, 'email_usuario'),
            senha_usuario=row['senha_usuario'],
            tipo_usuario=row['tipo_usuario']
        )
        body.append(user)
    
    return body

@app.get("/Usuario", response_model=List[Usuario], response_model_exclude={"senha_usuario"})
def get_user(login: str, token: str, response: Response):
    body = []

    token_is_valid = ValidateToken(token=token).validate_token(couchConn)
    if (token_is_valid is False):
        print('Token is Invalid')
        response.status_code = status.HTTP_401_UNAUTHORIZED

        return JSONResponse(status_code=400, content=[{"message": "Token is invalid"}])

    result = couchConn.getUser(login)
    user = Usuario(
        cpf=result['cpf'],
        login_usuario=result['login_usuario'],
        nome_usuario=result['nome_usuario'],
        email_usuario=returnKey(result, 'email_usuario'),
        senha_usuario=result['senha_usuario'],
        tipo_usuario=result['tipo_usuario']
    )
    body.append(user)
    
    return body

@app.get("/GerarUUID")
def get_uuid():
    return str(uuid.uuid1())

@app.post("/PopularCursoTurmaMateria", responses={400: {"model": Message}}, status_code=201)
def populate():
    couchConn.populateCourseGangSubject()
    neoConn.populateCourseGangSubject()

# Functions

def returnKey(row: dict, key: str):
    if key in row:
        return row[key]
    else:
        return '' 