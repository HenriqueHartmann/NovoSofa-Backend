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

    def token_document_exist(self, data: str, connC: CouchbaseConnection):
        query = '''SELECT RAW COUNT(*) FROM `novosofa`.project.token WHERE usuario_ref = "%s"''' %(data)
        query_result = connC.query(query)

        for item in query_result:
            if item > 0:
                return True

        return False 

    def create_document(self, uuid: str, connC: CouchbaseConnection, connN: Neo4jConnection):
        # query_couch = '''INSERT INTO `novosofa`.project.token (KEY, VALUE) 
        #                  VALUES ("%s", {"usuario_ref": "%s", "token": "%s", "expire": "%s"})
        #                  RETURNING * 
        #               ''' %(uuid, self.usuario_ref, self.token, self.expire)
        # connC.query(query_couch)

        # query_neo = '''CREATE (n:Token {id: "%s"}) RETURN n''' %(uuid)  
        # connN.query(query_neo)

        connC.createToken(uuid, self)

        return self

    def update_document(self, connC: CouchbaseConnection):
        connC.replace(
            'token', 
            connC.getTokenId(self.usuario_ref), 
            self.dict()
        )

        return self

class ValidateToken(BaseModel):
    token: str = ""

    def validate_token(self, conn: CouchbaseConnection):
        try:
            login = jwt.decode(self.token, secret_key, algorithms=[algorithm])
        except:
            return False

        query = '''SELECT expire, 
                   (SELECT RAW COUNT(*) 
                        FROM `novosofa`.project.token t 
                        WHERE t.usuario_ref = "%s")[0] as count 
                    FROM `novosofa`.project.token 
                    WHERE usuario_ref = "%s"''' %(login['login'], login['login'])
        query_result = conn.query(query)

        for item in query_result:
            if item['count'] > 0:
                now = datetime.now()
                expire = datetime.strptime(item['expire'], "%Y-%m-%d %H:%M:%S.%f")
                print(expire >= now)
                if expire >= now:
                    return True
        return False