from typing import List, Optional
import os
from unittest import result
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, BaseSettings
from connection.CouchbaseConnection import CouchbaseConnection
from connection.Neo4jConnection import Neo4jConnection
from models.Curso import Curso, CursoResponse, CursoTurmaMateria
from models.Materia import MateriaRequest, MateriaRequestKey, MateriaResponse
from models.RegistroAula import GetRegistroAula, RegistroAulaRequest
from models.Turma import Turma, TurmaMaterias, TurmaMateriasResponse, TurmaMateriasSimple, TurmaResponse
from models.Usuario import Usuario, UsuarioLogin
from models.Token import Token, ValidateToken
from models.Vinculo import ProfessorVinculoRequest, VinculoRequest, VinculoResponse
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

def parse_list(names: List[str] = Query(None)) -> Optional[List]:
    """
    accepts strings formatted as lists with square brackets
    names can be in the format
    "[bob,jeff,greg]" or '["bob","jeff","greg"]'
    """
    def remove_prefix(text: str, prefix: str):
        return text[text.startswith(prefix) and len(prefix):]

    def remove_postfix(text: str, postfix: str):
        if text.endswith(postfix):
            text = text[:-len(postfix)]
        return text

    if names is None:
        return

    # we already have a list, we can return
    if len(names) > 1:
        return names

    # if we don't start with a "[" and end with "]" it's just a normal entry
    flat_names = names[0]
    if not flat_names.startswith("[") and not flat_names.endswith("]"):
        return names

    flat_names = remove_prefix(flat_names, "[")
    flat_names = remove_postfix(flat_names, "]")

    names_list = flat_names.split(",")
    names_list = [remove_prefix(n.strip(), "\"") for n in names_list]
    names_list = [remove_postfix(n.strip(), "\"") for n in names_list]

    return names_list

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

@app.post("/CriarNovoUsuario", response_model=List[Usuario], response_model_exclude={"senha_usuario"}, status_code=201)
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

@app.get("/Usuarios", response_model=List[Usuario], response_model_exclude={"senha_usuario"}, status_code=200)
def get_all_users(token: str, response: Response):
    body = []

    token_is_valid = ValidateToken(token=token).validate_token(couchConn)
    if (token_is_valid is False):
        print('Token is Invalid')
        response.status_code = status.HTTP_401_UNAUTHORIZED

        return JSONResponse(status_code=401, content=[{"message": "Token is invalid"}])

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

@app.get("/Usuario", response_model=List[Usuario], response_model_exclude={"senha_usuario"}, status_code=200)
def get_user(login: str, token: str, response: Response):
    body = []

    token_is_valid = ValidateToken(token=token).validate_token(couchConn)
    if (token_is_valid is False):
        print('Token is Invalid')
        response.status_code = status.HTTP_401_UNAUTHORIZED

        return JSONResponse(status_code=401, content=[{"message": "Token is invalid"}])

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

@app.get("/Cursos", response_model=List[Curso], status_code=200)
def get_courses(token: str, response: Response):
    body = []

    token_is_valid = ValidateToken(token=token).validate_token(couchConn)
    if (token_is_valid is False):
        print('Token is Invalid')
        response.status_code = status.HTTP_401_UNAUTHORIZED

        return JSONResponse(status_code=401, content=[{"message": "Token is invalid"}])

    courses = neoConn.getCourses()
    for item in courses:
        result = couchConn.get('curso', item['n']['key']).value
        course = Curso(
            ch_curso=result['ch_curso'],
            nome_curso=result['nome_curso']
        )
        body.append(course)

    return body

# @app.get("/MedioMaterias", response_model=List[MateriaResponse], status_code=200)
# def get_graduation_subjects(course: str, token: str, response: Response):
#     body = []

#     token_is_valid = ValidateToken(token=token).validate_token(couchConn)
#     if (token_is_valid is False):
#         print('Token is Invalid')
#         response.status_code = status.HTTP_401_UNAUTHORIZED

#         return JSONResponse(status_code=401, content=[{"message": "Token is invalid"}])
    
#     subjects = neoConn.getCourseSubjects(course, 0)
#     for item in subjects:
#         result = couchConn.get('materia', item['m']['key']).value
#         subject = MateriaResponse(
#             key=item['m']['key'],
#             ch_materia=result['ch_materia'],
#             descricao_materia=result['descricao_materia'],
#             tipo_ensino=1
#         )
#         body.append(subject)

#     return body

@app.get("/SuperiorTurmas", response_model=List[TurmaResponse], status_code=200)
def get_graduation_gangs(course: str, token: str, response: Response):
    body = []

    token_is_valid = ValidateToken(token=token).validate_token(couchConn)
    if (token_is_valid is False):
        print('Token is Invalid')
        response.status_code = status.HTTP_401_UNAUTHORIZED

        return JSONResponse(status_code=401, content=[{"message": "Token is invalid"}])
    
    gangs = neoConn.getCourseGangs(course)
    for item in gangs:
        result = couchConn.get('turma', item['m']['key']).value
        gang = TurmaResponse(
            key=item['m']['key'],
            descricao_turma=result['descricao_turma'],
            dt_inicio=result['dt_inicio'],
            dt_fim=result['dt_fim']
        )
        body.append(gang)

    return body

@app.get("/CursosTurmasMaterias", response_model=List[CursoResponse], status_code=200)
def get_gangs_subjects_from_courses(token: str, response: Response, courses: List[str] = Depends(parse_list)):
    body = []

    token_is_valid = ValidateToken(token=token).validate_token(couchConn)
    if (token_is_valid is False):
        print('Token is Invalid')
        response.status_code = status.HTTP_401_UNAUTHORIZED

        return JSONResponse(status_code=401, content=[{"message": "Token is invalid"}])
    
    if courses is None:
        response.status_code = status.HTTP_400_BAD_REQUEST

        return JSONResponse(status_code=400, content=[{"message": "No course selected"}])

    results = neoConn.getCoursesSubjects(courses, 1)

    if len(results) == 0:
        response.status_code = status.HTTP_404_NOT_FOUND

        return JSONResponse(status_code=404, content=[{"message": "Data not found"}])
    else:
        courseIds = []
        courseObj = []

        for item in results:
            if item['c'].id not in courseIds:
                courseIds.append(item['c'].id)
                cObj = CursoTurmaMateria(id=item['c'].id, key=item['c']['key'])
                courseObj.append(cObj)

            for o in courseObj:
                obj = TurmaMateriasSimple()
                if o.id == item['r0'].nodes[0].id:
                    if keyGangAlreadyInserted(item['r0'].nodes[1]['key'], o.turmas) is False:
                        obj.turma=item['r0'].nodes[1]['key']
                if (item['r2'].nodes[0]['key'] == obj.turma):
                    obj.materias.append(item['r2'].nodes[1]['key'])

                if obj.turma != '':
                    o.turmas.append(obj)

        for o in courseObj:
            course: Curso
            gangs = []

            courseResult = couchConn.get('curso', o.key).value
            course = Curso(
                ch_curso=courseResult['ch_curso'],
                nome_curso=courseResult['nome_curso']
            )

            for i in o.turmas:
                gangResult = couchConn.get('turma', i.turma).value
                gang = TurmaResponse(
                    key=i.turma,
                    descricao_turma=gangResult['descricao_turma'],
                    dt_inicio=gangResult['dt_inicio'],
                    dt_fim=gangResult['dt_fim']
                )

                subjects = []
                subjectsResult = couchConn.getMulti('materia', i.materias).results.items()
                for row in subjectsResult:
                    row_content = row[1].value
                    subject = MateriaRequestKey(
                        key=row[1].key,
                        ch_materia=row_content['ch_materia'],
                        descricao_materia=row_content['descricao_materia'],
                        tipo_ensino=row_content['tipo_ensino'],
                        dt_inicio=returnKey(row_content, 'dt_inicio'),
                        dt_fim=returnKey(row_content, 'dt_fim'))
                    subjects.append(subject)

                gangs.append(TurmaMateriasResponse(
                    turma=gang,
                    materias=subjects
                ))

            body.append(
                CursoResponse(
                    curso=course,
                    turmas=gangs,
                )
            )

    return body

@app.get("/TurmaMaterias", response_model=List[TurmaMaterias], status_code=200)
def get_gang_subjects(gang: str, token: str, response: Response):
    body = []

    token_is_valid = ValidateToken(token=token).validate_token(couchConn)
    if (token_is_valid is False):
        print('Token is Invalid')
        response.status_code = status.HTTP_401_UNAUTHORIZED

        return JSONResponse(status_code=401, content=[{"message": "Token is invalid"}])

    gangs = neoConn.getGangSubjects(gang)

    gangObj = None
    subjectObjs = []

    for item in gangs:
        if gangObj is None:
            gangResult = couchConn.get('turma', item['t']['key']).value
            gangObj = Turma(
                descricao_turma=gangResult['descricao_turma'],
                dt_inicio=gangResult['dt_inicio'],
                dt_fim=gangResult['dt_fim'])

        subjectsResult = couchConn.get('materia', item['m']['key']).value
        subjectObj = MateriaRequest(
                ch_materia=subjectsResult['ch_materia'],
                descricao_materia=subjectsResult['descricao_materia'],
                tipo_ensino=subjectsResult['tipo_ensino'])
        subjectObjs.append(subjectObj)

    body.append(TurmaMaterias(
        turma=gangObj,
        materias=subjectObjs
    ))

    if len(body) == 0:
       response.status_code = status.HTTP_404_NOT_FOUND

       return JSONResponse(status_code=404, content=[{"message": "Gang(s) not found"}])

    return body

@app.get("/TurmasPorMateria", response_model=List[Turma], status_code=200)
def get_gang_subjects(course: str, token: str, response: Response, subjects: List[str] = Depends(parse_list)):
    body = []

    token_is_valid = ValidateToken(token=token).validate_token(couchConn)
    if (token_is_valid is False):
        print('Token is Invalid')
        response.status_code = status.HTTP_401_UNAUTHORIZED

        return JSONResponse(status_code=401, content=[{"message": "Token is invalid"}])
    
    if subjects is None:
        response.status_code = status.HTTP_400_BAD_REQUEST

        return JSONResponse(status_code=400, content=[{"message": "Subject is empty"}])

    gangs = neoConn.getSubjectsGangs(course, subjects)

    for item in gangs:
        result = couchConn.get('turma', item['t']['key']).value
        gang = Turma(
            descricao_turma=result['descricao_turma'],
            dt_inicio=result['dt_inicio'],
            dt_fim=result['dt_fim']
        )
        body.append(gang)

    if len(body) == 0:
       response.status_code = status.HTTP_404_NOT_FOUND

       return JSONResponse(status_code=404, content=[{"message": "Gang(s) not found"}])

    return body

@app.get("/VinculosUsuario", response_model=List[VinculoResponse], response_model_exclude={"usuario": {"senha_usuario"}}, status_code=200)
def get_user_binds(userType: int, token: str, response: Response):
    body = []

    token_is_valid = ValidateToken(token=token).validate_token(couchConn)
    if (token_is_valid is False):
        print('Token is Invalid')
        response.status_code = status.HTTP_401_UNAUTHORIZED

        return JSONResponse(status_code=401, content=[{"message": "Token is invalid"}])

    vToken = ValidateToken(
        token=token
    )
    login = vToken.decode_token()

    binds = neoConn.getStudentBinds(login, userType)

    if len(binds) == 0:
        print('User do not have bonds')
        response.status_code = status.HTTP_404_NOT_FOUND

        return JSONResponse(status_code=404, content=[{"message": "User do not have bonds"}]) 
    else:
        userKey = ''
        courseKeys = []
        subjectKeys = []
        gangsKeys = []

        for item in binds:
            if userKey == '':
                userKey = item['u']['id']
            # if courseKey == '':
            #     courseKey = item['c']['key']
            courseKeys.append(item['c']['key'])
            subjectKeys.append(item['m']['key'])
            gangsKeys.append(item['t']['key'])

        user = None
        courses = []
        subjects = []
        gangs = []

        userResult = couchConn.get('usuario', userKey).value
        coursesResult = couchConn.getMulti('curso', courseKeys).results.items()
        subjectsResult = couchConn.getMulti('materia', subjectKeys).results.items()
        gangsResult = couchConn.getMulti('turma', gangsKeys).results.items()

        user = Usuario(
                cpf=userResult['cpf'],
                login_usuario=userResult['login_usuario'],
                nome_usuario=userResult['nome_usuario'],
                email_usuario=returnKey(userResult, 'email_usuario'),
                senha_usuario=userResult['senha_usuario'],
                tipo_usuario=userResult['tipo_usuario'])
        
        # course = Curso(
        #     ch_curso=courseResult['ch_curso'],
        #     nome_curso=courseResult['nome_curso'])

        for row in coursesResult:
            row_content = row[1].value
            course = Curso(
                ch_curso=row_content['ch_curso'],
                nome_curso=row_content['nome_curso'])
            courses.append(course)

        for row in subjectsResult:
            row_content = row[1].value
            subject = MateriaRequest(
                ch_materia=row_content['ch_materia'],
                descricao_materia=row_content['descricao_materia'],
                tipo_ensino=row_content['tipo_ensino'])
            subjects.append(subject)

        for row in gangsResult:
           row_content = row[1].value
           gang = Turma(
            descricao_turma=row_content['descricao_turma'],
            dt_inicio=row_content['dt_inicio'],
            dt_fim=row_content['dt_fim']
           )
           gangs.append(gang)

        userBonds = VinculoResponse(
            usuario=user,
            curso=courses,
            materias=subjects,
            turmas=gangs
        )
        
        body.append(userBonds)

        return body

@app.post("/SuperiorVincular", status_code=201)
def bind_graduation(vinculo: VinculoRequest, token: str, response: Response):
    token_is_valid = ValidateToken(token=token).validate_token(couchConn)
    if (token_is_valid is False):
        print('Token is Invalid')
        response.status_code = status.HTTP_401_UNAUTHORIZED

        return JSONResponse(status_code=401, content=[{"message": "Token is invalid"}])

    vinculo.bind_graduation(token, neoConn)

    return []

@app.post("/ProfessorVincular", status_code=201)
def bind_professor(vinculo: ProfessorVinculoRequest, token: str, response: Response):
    token_is_valid = ValidateToken(token=token).validate_token(couchConn)
    if (token_is_valid is False):
        print('Token is Invalid')
        response.status_code = status.HTTP_401_UNAUTHORIZED

        return JSONResponse(status_code=401, content=[{"message": "Token is invalid"}])

    vinculo.bind_professor(token, neoConn)

    return []

@app.get('/RegistroAula', status_code=201)
def create_class_record(token: str, response: Response, curso: str = "", turma: str= "", materia: str = ""):
    token_is_valid = ValidateToken(token=token).validate_token(couchConn)
    if (token_is_valid is False):
        print('Token is Invalid')
        response.status_code = status.HTTP_401_UNAUTHORIZED

        return JSONResponse(status_code=401, content=[{"message": "Token is invalid"}])
    
    record = GetRegistroAula(
        curso=curso,
        turma=turma,
        materia=materia
    )

    record.get_document(token, couchConn, neoConn)

    return []

@app.post('/CriarRegistroAula', status_code=201)
def create_class_record(record: RegistroAulaRequest, token: str, response: Response):
    token_is_valid = ValidateToken(token=token).validate_token(couchConn)
    if (token_is_valid is False):
        print('Token is Invalid')
        response.status_code = status.HTTP_401_UNAUTHORIZED

        return JSONResponse(status_code=401, content=[{"message": "Token is invalid"}])
    
    key = str(uuid.uuid1())

    record.create_document(key, token, couchConn, neoConn)

    return []

# @app.get("/GerarUUID")
# def get_uuid():
#     return str(uuid.uuid1())

@app.post("/PopularCursoTurmaMateria", status_code=201)
def populate():
    couchConn.populateCourseGangSubject()
    neoConn.populateCourseGangSubject()

# Functions

def returnKey(row: dict, key: str):
    if key in row:
        return row[key]
    else:
        return ''

def keyGangAlreadyInserted(key: str, data: List[TurmaMateriasSimple]):
    for i in data:
        if key == i.turma:
            return True
    return False

def keySubjectAlreadyInserted(key: str, data: List[TurmaMateriasSimple]):
    for i in data:
        for j in i.materias:
            if key == j:
                return True
    return False