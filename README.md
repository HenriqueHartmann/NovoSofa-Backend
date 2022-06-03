# NovoSofa-Backend

## 1 - Requirements:
- Python: 3.9.13
- Neo4j
- Couchbase

## 2 - Como Instalar:
### 2.1 - Criar Virtual Enviroment (venv)
```
python3 -m venv venv
```

### 2.2 - Executar a venv
#### 2.2.1 - Linux
```
source venv/bin/activate.bat
```

#### 2.2.2 - Windows
```
venv\Scripts\activate
```

### 2.3 - Instalar pacotes
#### 2.3.1 - Linux
```
pip install -r requirements.txt
```

#### 2.3.2 - Windows
```
python -m pip install -r requirements.txt
```

## 3 - Como executar
```
uvicorn main:app --reload
```
