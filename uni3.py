from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP, ForeignKey, DECIMAL, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel
import hashlib 
import requests 
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import shutil
import os 
from fastapi.staticfiles import StaticFiles

# --- CONFIGURACIÓN INICIAL ---
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True) # Crear carpeta 'uploads' si no existe

# Conexión a la base de datos (Usamos la de asistencia/roles como principal)
DATABASE_URL = "mysql+mysqlconnector://root:@localhost:3306/uni3" 
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) 
Base = declarative_base()

app = FastAPI()

app.mount(f"/{UPLOAD_DIR}", StaticFiles(directory=UPLOAD_DIR), name=UPLOAD_DIR)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)


# --- Modelos SQLAlchemy ---
class Role(Base):
    __tablename__ = "P9_roles"
    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False)
    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "P9_users" 
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role_id = Column(Integer, ForeignKey("P9_roles.role_id"), default=2) 
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    role = relationship("Role", back_populates="users")
    # Para el sistema de entregas
    assigned_packages = relationship("Package", back_populates="delivery_agent")

class Attendance(Base):
    __tablename__ = "P9_attendance" 
    attendance_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("P9_users.user_id"))
    latitude = Column(DECIMAL(10, 8), nullable=False)
    longitude = Column(DECIMAL(11, 8), nullable=False)
    address = Column(String(255))
    registered_at = Column(TIMESTAMP, default=datetime.utcnow)
    user = relationship("User")

# Nuevo modelo de FOTO (Unificado)
class Foto(Base):
    __tablename__ = "p10_foto"
    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(String(255), nullable=False)
    ruta_foto = Column(String(255), nullable=False)
    fecha = Column(TIMESTAMP, default=datetime.utcnow)

# Nuevo modelo de PAQUETE
class Package(Base):
    __tablename__ = "P9_packages"
    package_id = Column(Integer, primary_key=True, index=True)
    address = Column(String(255), nullable=False)
    description = Column(String(255))
    # Agente asignado: Solo roles con ID 3 (Delivery Agent, si lo creamos) o 1 (Admin)
    assigned_to_user_id = Column(Integer, ForeignKey("P9_users.user_id"))
    is_delivered = Column(Boolean, default=False)

    delivery_agent = relationship("User", back_populates="assigned_packages")
    delivery_record = relationship("Delivery", back_populates="package", uselist=False)

# Nuevo modelo de ENTREGA
class Delivery(Base):
    __tablename__ = "P9_deliveries"
    delivery_id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("P9_packages.package_id"), unique=True)
    delivered_by_user_id = Column(Integer, ForeignKey("P9_users.user_id"))
    delivery_latitude = Column(DECIMAL(10, 8), nullable=False)
    delivery_longitude = Column(DECIMAL(11, 8), nullable=False)
    delivery_address = Column(String(255))
    photo_route = Column(String(255))
    delivered_at = Column(TIMESTAMP, default=datetime.utcnow)

    package = relationship("Package", back_populates="delivery_record")
    deliverer = relationship("User")


# Función para encriptar con MD5
def md5_hash(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return md5_hash(plain_password) == hashed_password

# Función para poblar roles y crear un admin de prueba
def create_roles_and_admin():
    db = SessionLocal()
    # P9_roles debe ser creado antes de P9_users
    if db.query(Role).count() == 0:
        print("Creando roles iniciales...")
        admin_role = Role(role_id=1, role_name="admin")
        student_role = Role(role_id=2, role_name="student")
        agent_role = Role(role_id=3, role_name="delivery_agent") # Nuevo Rol
        db.add_all([admin_role, student_role, agent_role])
        db.commit()
        print("Roles creados con éxito.")
    
    # Crear o asegurar que el usuario 1 (Admin) exista
    if not db.query(User).filter(User.user_id == 1).first():
        print("Creando usuario administrador de prueba (ID 1)...")
        admin_user = User(
            user_id=1,
            username="admin", 
            password_hash=md5_hash("adminpass"), 
            full_name="Admin User", 
            role_id=1
        )
        db.add(admin_user)
        db.commit()

    # Crear usuario Agente de prueba (ID 3)
    if not db.query(User).filter(User.user_id == 3).first():
        print("Creando usuario Delivery Agent de prueba (ID 3)...")
        agent_user = User(
            user_id=3,
            username="agent", 
            password_hash=md5_hash("agentpass"), 
            full_name="Delivery Agent", 
            role_id=3
        )
        db.add(agent_user)
        db.commit()

    # Crear paquetes de prueba (Asignados al agente 3)
    if db.query(Package).count() == 0:
        print("Creando paquetes de prueba...")
        pkg1 = Package(package_id=1, address="Calle Falsa 123, Ciudad A", description="TV 55 pulgadas", assigned_to_user_id=3)
        pkg2 = Package(package_id=2, address="Avenida Siempre Viva 456, Ciudad B", description="Documentos urgentes", assigned_to_user_id=3)
        pkg3 = Package(package_id=3, address="Bulevard de los Sueños 789, Ciudad C", description="Libros de texto", assigned_to_user_id=1) # Asignado a Admin
        db.add_all([pkg1, pkg2, pkg3])
        db.commit()
        print("Paquetes creados con éxito.")

    db.close()


Base.metadata.create_all(bind=engine)
create_roles_and_admin() 


# --- Modelos Pydantic ---
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    role_id: int
    full_name: str

# Para la Asistencia
class AttendanceModel(BaseModel):
    user_id: int
    latitude: float
    longitude: float

# Para el Historial
class UserIdModel(BaseModel):
    user_id: int

class AttendanceReadModel(BaseModel):
    attendance_id: int
    user_id: int
    latitude: float
    longitude: float
    address: str
    registered_at: datetime 

    class Config:
        from_attributes = True 

# Para la Galería
class PhotoReadModel(BaseModel):
    id: int
    descripcion: str
    ruta_foto: str
    fecha: Optional[datetime]

    class Config:
        from_attributes = True

# Para Entregas
class PackageReadModel(BaseModel):
    package_id: int
    address: str
    description: Optional[str] = None
    assigned_to_user_id: Optional[int] = None
    is_delivered: bool

    class Config:
        from_attributes = True

class DeliveryModel(BaseModel):
    package_id: int
    delivery_latitude: float
    delivery_longitude: float
    # El user_id se obtiene del contexto de la sesión/token, pero para simplificar, se envía en el body:
    delivered_by_user_id: int 
    photo_route: str # Ruta de la foto subida


# --- Dependencia DB ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FUNCIONES DE SEGURIDAD ---
def authenticate_user(db, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


# --- ENDPOINTS ---

## 🔑 LOGIN (Seguridad)
@app.post("/login/", response_model=Token)
def login(form_data: UserLogin, db=Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Token simulado: En un sistema real, se usaría JWT
    token_simulado = f"{user.username}:{user.password_hash[:10]}"
    return Token(
        access_token=token_simulado, 
        token_type="bearer", 
        user_id=user.user_id,
        role_id=user.role_id,
        full_name=user.full_name
    )

## 📍 ASISTENCIA/MAPA
@app.post("/attendance/")
def attendance(data: AttendanceModel, db=Depends(get_db)):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={data.latitude}&lon={data.longitude}"
        headers = {"User-Agent": "FastAPIApp/1.0"} 
        response = requests.get(url, headers=headers)

        address = "Dirección no disponible"
        if response.status_code == 200:
            result = response.json()
            address = result.get("display_name", address)

        record = Attendance(
            user_id=data.user_id,
            latitude=data.latitude,
            longitude=data.longitude,
            address=address,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return {
            "msg": "Registro de asistencia guardado",
            "attendance_id": record.attendance_id,
            "address": address,
            "latitude": float(data.latitude),  
            "longitude": float(data.longitude), 
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en Asistencia: {str(e)}")


## 📸 GALERÍA/FOTO
@app.post("/fotos/")
async def subir_foto(descripcion: str = Form(...), file: UploadFile = File(...), user_id: int = Form(...), db=Depends(get_db)):
    try:
        ruta = f"{UPLOAD_DIR}/user_{user_id}_{file.filename}"
        with open(ruta, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        nueva_foto = Foto(descripcion=descripcion, ruta_foto=ruta)

        db.add(nueva_foto)
        db.commit()
        db.refresh(nueva_foto)

        return {
            "msg": "Foto subida correctamente",
            "foto": PhotoReadModel.from_orm(nueva_foto),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en Subida de Foto: {str(e)}")

@app.get("/fotos/", response_model=List[PhotoReadModel])
def listar_fotos(db=Depends(get_db)):
    fotos = db.query(Foto).all()
    return fotos

## 📦 ENTREGAS

@app.get("/packages/assigned/{user_id}", response_model=List[PackageReadModel])
def get_assigned_packages(user_id: int, db=Depends(get_db)):
    """Obtiene los paquetes asignados y no entregados a un agente."""
    packages = db.query(Package).filter(
        Package.assigned_to_user_id == user_id,
        Package.is_delivered == False
    ).all()
    
    # Simulación de verificación de rol (solo agente o admin pueden ver)
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role_id not in [1, 3]:
        raise HTTPException(status_code=403, detail="Permiso denegado. Solo Agentes y Admin.")

    return packages

@app.post("/deliveries/record/")
async def record_delivery(
    package_id: int = Form(...),
    delivered_by_user_id: int = Form(...),
    delivery_latitude: float = Form(...),
    delivery_longitude: float = Form(...),
    file: UploadFile = File(...),
    db=Depends(get_db)
):
    """Guarda el registro de entrega, actualiza el estado del paquete y la foto."""
    # 1. Validación de Paquete
    pkg = db.query(Package).filter(Package.package_id == package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Paquete no encontrado.")
    if pkg.is_delivered:
        raise HTTPException(status_code=400, detail="El paquete ya ha sido entregado.")
    if pkg.assigned_to_user_id != delivered_by_user_id:
        raise HTTPException(status_code=403, detail="El paquete no está asignado a este agente.")
        
    # 2. Guardar Foto de la prueba de entrega
    photo_route = f"{UPLOAD_DIR}/delivery_{package_id}_{file.filename}"
    try:
        with open(photo_route, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar la foto de entrega: {str(e)}")

    # 3. Obtener dirección por geolocalización (Nominatim)
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={delivery_latitude}&lon={delivery_longitude}"
    headers = {"User-Agent": "FastAPIApp/1.0-Delivery"} 
    response = requests.get(url, headers=headers)
    delivery_address = "Dirección no disponible"
    if response.status_code == 200:
        result = response.json()
        delivery_address = result.get("display_name", delivery_address)

    # 4. Crear el registro de Entrega
    delivery_record = Delivery(
        package_id=package_id,
        delivered_by_user_id=delivered_by_user_id,
        delivery_latitude=delivery_latitude,
        delivery_longitude=delivery_longitude,
        delivery_address=delivery_address,
        photo_route=photo_route,
    )
    db.add(delivery_record)
    
    # 5. Actualizar estado del paquete
    pkg.is_delivered = True
    
    db.commit()
    db.refresh(delivery_record)
    
    return {
        "msg": "Entrega registrada con éxito.",
        "delivery_id": delivery_record.delivery_id,
        "address": delivery_address,
        "photo_route": photo_route,
    }
## 📖 HISTORIAL DE ASISTENCIA (Admin)
@app.post("/attendance/history/", response_model=List[AttendanceReadModel])
def get_attendance_history(data: UserIdModel, db=Depends(get_db)):
    """
    Obtiene todos los registros de asistencia para todos los usuarios.
    El user_id enviado en el body (data) se usa para simular verificación de rol.
    """
    user_requesting = db.query(User).filter(User.user_id == data.user_id).first()

    if not user_requesting or user_requesting.role_id != 1:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado. Solo administradores pueden ver el historial completo.",
        )


    history = db.query(Attendance).order_by(Attendance.registered_at.desc()).all()
    
  
    return history