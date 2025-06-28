#Main(hay que correr el main para que todo funcione, y descargar uvicorn y mysql en la terminal)
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Date, Time, Text, DateTime, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr, validator
from datetime import date, time, datetime
from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "mysql+pymysql://root:123Queso.@localhost/sip%26joy"

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ReservaDB(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    hora = Column(Time, nullable=False)
    personas = Column(Integer, nullable=False)
    comentarios = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


Base.metadata.create_all(bind=engine)


class ReservaCreate(BaseModel):
    nombre: str
    telefono: str
    email: EmailStr
    fecha: date
    hora: time
    personas: int
    comentarios: Optional[str] = None

    @validator('nombre')
    def validar_nombre(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('El nombre debe tener al menos 2 caracteres')
        return v.strip().title()

    @validator('telefono')
    def validar_telefono(cls, v):
        telefono_limpio = v.replace('-', '').replace(' ', '')
        if not telefono_limpio.isdigit() or len(telefono_limpio) not in [8, 11]:
            raise ValueError('Formato de teléfono inválido')
        return v

    @validator('personas')
    def validar_personas(cls, v):
        if v < 1 or v > 8:
            raise ValueError('Número de personas debe estar entre 1 y 8')
        return v

    @validator('fecha')
    def validar_fecha(cls, v):
        if v < date.today():
            raise ValueError('No se pueden hacer reservas para fechas pasadas')
        return v


class ReservaResponse(BaseModel):
    id: int
    nombre: str
    telefono: str
    email: str
    fecha: date
    hora: time
    personas: int
    comentarios: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class EstadisticasResponse(BaseModel):
    total_reservas: int
    personas_total: int
    reservas_hoy: int
    reservas_futuras: int


app = FastAPI(
    title="🍵 Sistema de Reservas - Sip & Joy Café",
    description="API completa para gestión de reservas de restaurante",
    version="2.0.0",
    contact={
        "name": "Sip & Joy Café",
        "email": "contacto@sipandjoy.com",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "error_type": "Validation Error"}
    )


@app.get("/", tags=["General"])
async def root():
    return {
        "message": "🍵 Bienvenido al Sistema de Reservas - Sip & Joy Café",
        "version": "2.0.0",
        "endpoints": {
            "reservas": "/reservas",
            "estadisticas": "/estadisticas",
            "documentacion": "/docs"
        }
    }


@app.get("/health", tags=["General"])
async def health_check():
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "healthy", "database": "connected", "timestamp": datetime.now()}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        )


@app.get("/reservas", response_model=List[ReservaResponse], tags=["Reservas"])
async def get_reservas(
        email: Optional[str] = Query(None, description="Filtrar por email"),
        fecha: Optional[date] = Query(None, description="Filtrar por fecha"),
        skip: int = Query(0, ge=0, description="Número de registros a saltar"),
        limit: int = Query(100, ge=1, le=1000, description="Límite de registros"),
        db: Session = Depends(get_db)
):
    query = db.query(ReservaDB)

    if email:
        query = query.filter(ReservaDB.email.ilike(f"%{email}%"))
    if fecha:
        query = query.filter(ReservaDB.fecha == fecha)

    reservas = query.order_by(ReservaDB.fecha.desc(), ReservaDB.hora.desc()).offset(skip).limit(limit).all()
    logger.info(f"Consulta de reservas: email={email}, fecha={fecha}, resultados={len(reservas)}")
    return reservas


@app.get("/reservas/{reserva_id}", response_model=ReservaResponse, tags=["Reservas"])
async def get_reserva(reserva_id: int, db: Session = Depends(get_db)):
    reserva = db.query(ReservaDB).filter(ReservaDB.id == reserva_id).first()
    if not reserva:
        logger.warning(f"Reserva no encontrada: ID={reserva_id}")
        raise HTTPException(status_code=404, detail=f"Reserva con ID {reserva_id} no encontrada")
    return reserva


@app.post("/reservas", response_model=ReservaResponse, status_code=201, tags=["Reservas"])
async def create_reserva(reserva: ReservaCreate, db: Session = Depends(get_db)):
    try:
        existing = db.query(ReservaDB).filter(
            and_(
                ReservaDB.fecha == reserva.fecha,
                ReservaDB.hora == reserva.hora
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe una reserva para {reserva.fecha} a las {reserva.hora}"
            )

        db_reserva = ReservaDB(**reserva.dict())
        db.add(db_reserva)
        db.commit()
        db.refresh(db_reserva)

        logger.info(f"Nueva reserva creada: ID={db_reserva.id}, Cliente={db_reserva.nombre}")
        return db_reserva

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando reserva: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.put("/reservas/{reserva_id}", response_model=ReservaResponse, tags=["Reservas"])
async def update_reserva(reserva_id: int, reserva: ReservaCreate, db: Session = Depends(get_db)):
    try:
        db_reserva = db.query(ReservaDB).filter(ReservaDB.id == reserva_id).first()
        if not db_reserva:
            raise HTTPException(status_code=404, detail=f"Reserva con ID {reserva_id} no encontrada")

        for key, value in reserva.dict().items():
            setattr(db_reserva, key, value)

        db.commit()
        db.refresh(db_reserva)

        logger.info(f"Reserva actualizada: ID={reserva_id}")
        return db_reserva

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando reserva {reserva_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.delete("/reservas/{reserva_id}", tags=["Reservas"])
async def delete_reserva(reserva_id: int, db: Session = Depends(get_db)):
    try:
        db_reserva = db.query(ReservaDB).filter(ReservaDB.id == reserva_id).first()
        if not db_reserva:
            raise HTTPException(status_code=404, detail=f"Reserva con ID {reserva_id} no encontrada")

        nombre_cliente = db_reserva.nombre
        db.delete(db_reserva)
        db.commit()

        logger.info(f"Reserva eliminada: ID={reserva_id}, Cliente={nombre_cliente}")
        return {"detail": f"Reserva de {nombre_cliente} eliminada correctamente", "id": reserva_id}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando reserva {reserva_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.get("/estadisticas", response_model=EstadisticasResponse, tags=["Estadísticas"])
async def get_estadisticas(db: Session = Depends(get_db)):
    try:
        total_reservas = db.query(ReservaDB).count()
        personas_total = db.query(ReservaDB).with_entities(ReservaDB.personas).all()
        personas_total = sum([p[0] for p in personas_total])

        hoy = date.today()
        reservas_hoy = db.query(ReservaDB).filter(ReservaDB.fecha == hoy).count()
        reservas_futuras = db.query(ReservaDB).filter(ReservaDB.fecha > hoy).count()

        return EstadisticasResponse(
            total_reservas=total_reservas,
            personas_total=personas_total,
            reservas_hoy=reservas_hoy,
            reservas_futuras=reservas_futuras
        )
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")