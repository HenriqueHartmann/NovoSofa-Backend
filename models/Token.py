import time
from datetime import datetime, timedelta
import jwt
from pydantic import BaseModel

from connection.CouchbaseConnection import CouchbaseConnection

secret_key = "f9bf78b9a18ce6d46a0cd2b0b86df9da"
algorithm = "HS256"

class Token(BaseModel):
    usuario_ref: str
    token: str = ""
    expire: datetime = ""

    def create_access_token(self, data): 
        self.expire = datetime.utcnow() + timedelta(minutes=60)
        access_token = jwt.encode(data, secret_key, algorithm)
        self.token = access_token

class ValidateToken(BaseModel):
    token: str = ""

    def validate_token(self, conn: CouchbaseConnection):
        try:
            login = jwt.decode(self.token, secret_key, algorithms=[algorithm])
        except:
            return False

        query = '''SELECT COUNT(a.usuario_ref) FROM `novosofa`.project.token a WHERE a.usuario_ref = "%s"''' %(login['login'])
        query_result = conn.query(query)

        for row in query_result:
            if row['$1'] > 0:
                return True
        return False