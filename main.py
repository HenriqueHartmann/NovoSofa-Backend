from fastapi import FastAPI
from typing import List
from connection.Neo4jConnection import Neo4jConnection
from models.Materia import Materia

app = FastAPI()

uri = "bolt://localhost:7687"
user = "neo4j"
pwd = "root"

conn = Neo4jConnection(uri=uri, user=user, pwd=pwd)

@app.get("/materias", response_model=List[Materia])
def read_subject():
    materias = []
    queryReturn = conn.query('''MATCH (n: Materia) return n''')
    
    for item in queryReturn:
        materia = Materia(
            id=item['n'].id,
            ch_materia=item['n']['ch_materia'],
            descricao_materia=item['n']['descricao_materia']
        )
        materias.append(materia)

    return materias
