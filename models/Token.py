from datetime import datetime, timedelta
import jwt
from pydantic import BaseModel
from connection.CouchbaseConnection import CouchbaseConnection
from connection.Neo4jConnection import Neo4jConnection

secret_key = "f9bf78b9a18ce6d46a0cd2b0b86df9da"
algorithm = "HS256"

class Token(BaseModel):
    usuario_ref: str
    token: str = ""
    expire: datetime = ""

    def create_access_token(self, data): 
        expire = datetime.utcnow() + timedelta(minutes=60)
        self.expire = expire.strftime("%Y-%m-%d %H:%M:%S.%f")
        self.token = jwt.encode(data, secret_key, algorithm)

    def token_document_exists(self, login: str, connC: CouchbaseConnection):
        return connC.tokenExistsByLogin(login) 

    def create_document(self, key: str, connC: CouchbaseConnection, connN: Neo4jConnection):
        connC.insert('token', key, self.dict())
        connN.createToken(key, self.usuario_ref)

        return self

    def update_document(self, connC: CouchbaseConnection):
        key = connC.getTokenId(self.usuario_ref)
        connC.replace('token', key, self.dict())
        print('LOGIN EFETUADO')
        
        return self

class ValidateToken(BaseModel):
    token: str = ""

    def decode_token(self):
        try:
            login = jwt.decode(self.token, secret_key, algorithms=[algorithm])
        except:
            return ""

        return login['login']

    def validate_token(self, conn: CouchbaseConnection):
        if conn.tokenExists(self.token):
            result = conn.getTokenExpireDatetime(self.decode_token())

            if result['count'] > 0:
                now = datetime.now()
                expire = datetime.strptime(result['expire'], "%Y-%m-%d %H:%M:%S.%f")
                if expire >= now:
                    return True

        return False