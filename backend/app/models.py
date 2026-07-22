from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class UserRole(str, Enum):
    ESTUDIANTES = "Estudiantes"
    DOCENTES = "Docentes"


class FoodItem(BaseModel):
    nombre: str
    cantidad: str
    comida: str


class PlanRequest(BaseModel):
    paciente_id: str
    tipo_plan: str
    alimentos: Optional[List[FoodItem]] = []


class AlimentoBase(BaseModel):
    id: str
    nombre: str
    nombre_ingles: Optional[str] = ""
    categoria: str
    fuente_tabla: str = "USFQ - Tabla de composición de alimentos (2021)"
    energia_kcal: Optional[float] = 0.0
    proteina_g: Optional[float] = 0.0
    grasa_total_g: Optional[float] = 0.0
    carbohidratos_g: Optional[float] = 0.0
    fibra_g: Optional[float] = 0.0
    aga_g: Optional[float] = 0.0
    aga_mono_g: Optional[float] = 0.0
    aga_poly_g: Optional[float] = 0.0
    colesterol_mg: Optional[float] = 0.0
    calcio_mg: Optional[float] = 0.0
    fosforo_mg: Optional[float] = 0.0
    hierro_mg: Optional[float] = 0.0
    potasio_mg: Optional[float] = 0.0
    sodio_mg: Optional[float] = 0.0
    zinc_mg: Optional[float] = 0.0
    vitamina_c_mg: Optional[float] = 0.0
    vitamina_a_ug: Optional[float] = 0.0
    acido_folico_ug: Optional[float] = 0.0
    vitamina_b12_ug: Optional[float] = 0.0


class PlanAlimentoItem(BaseModel):
    alimento_id: str
    nombre: str
    cantidad_gramos: float
    comida: str
    energia_kcal: float = 0.0
    proteina_g: float = 0.0
    grasa_total_g: float = 0.0
    carbohidratos_g: float = 0.0
    fibra_g: float = 0.0
    calcio_mg: float = 0.0
    hierro_mg: float = 0.0
    potasio_mg: float = 0.0
    sodio_mg: float = 0.0
    vitamina_c_mg: float = 0.0
    vitamina_a_ug: float = 0.0
    acido_folico_ug: float = 0.0
    vitamina_b12_ug: float = 0.0


class PlanAlimenticioCreate(BaseModel):
    paciente_id: str
    tipo_plan: str
    alimentos: List[PlanAlimentoItem]


class SugerenciaPlanRequest(BaseModel):
    paciente_id: str


class SugerenciaPlanResponse(BaseModel):
    paciente_id: str
    objetivo_kcal: float
    distribucion_macros: dict
    alimentos_sugeridos: List[dict]
    formula_utilizada: str
    descripcion_formula: str


class AuditLogEntry(BaseModel):
    timestamp: str
    actor_id: str
    actor_seudonimizado: Optional[str] = None
    accion: str
    entidad: str
    entidad_id: Optional[str] = None
    resultado: str
    detalle: Optional[str] = None


class PacienteAntropometria(BaseModel):
    paciente_id: str
    peso_kg: float
    estatura_m: float
    edad: int
    sexo_biologico: str
    imc: Optional[float] = None
    imc_clasificacion: Optional[str] = None
    tmb_harris: Optional[float] = None
    tmb_mifflin: Optional[float] = None
    gasto_total_harris: Optional[float] = None
    gasto_total_mifflin: Optional[float] = None
    icc: Optional[float] = None
    icc_riesgo: Optional[str] = None
    factor_actividad: float = 1.55
    antecedentes: Optional[List[str]] = []
    created_at: Optional[str] = None
