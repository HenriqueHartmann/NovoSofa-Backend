from datetime import datetime, timedelta
import jwt
from pydantic import BaseModel

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