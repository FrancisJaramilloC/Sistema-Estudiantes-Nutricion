import uuid
from decimal import Decimal
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from botocore.exceptions import ClientError
from database import get_or_create_auditoria_table
from auth import require_role

router = APIRouter(tags=["Clinical"])

class ClinicalCalculateRequest(BaseModel):
    peso_kg: float = Field(..., gt=0, description="Peso del paciente en kilogramos")
    estatura_m: float = Field(..., gt=0, description="Estatura del paciente en metros")
    perimetro_cintura_cm: float = Field(..., gt=0, description="Perímetro de cintura del paciente en centímetros")
    perimetro_cadera_cm: float = Field(..., gt=0, description="Perímetro de cadera del paciente en centímetros")
    sexo_biologico: str = Field(..., description="Sexo biológico del paciente: 'Masculino' o 'Femenino'")

class ClinicalCalculateResponse(BaseModel):
    imc: float
    imc_clasificacion: str
    icc: float
    icc_riesgo: str
    distribucion_grasa: str

@router.post("/clinical/calculate", response_model=ClinicalCalculateResponse)
@router.post("/api/v1/clinical/calculate", response_model=ClinicalCalculateResponse)
async def calculate_clinical(
    req: ClinicalCalculateRequest,
    user: dict = Depends(require_role(["Estudiantes"]))
):
    """
    Endpoint síncrono del Motor Antropométrico protegido por rol.
    Calcula IMC e ICC, clasifica el riesgo cardiovascular según la OMS,
    y registra los datos de forma seudonimizada en DynamoDB (Auditoria_Planes_Table).
    """
    sex = req.sexo_biologico.strip().capitalize()
    if sex not in ["Masculino", "Femenino"]:
        raise HTTPException(status_code=400, detail="El sexo biológico debe ser 'Masculino' o 'Femenino'.")

    # 1. Calcular IMC
    imc = req.peso_kg / (req.estatura_m ** 2)
    imc = round(imc, 2)

    # Clasificación IMC (OMS)
    if imc < 18.5:
        imc_clasificacion = "Bajo peso"
    elif 18.5 <= imc < 25.0:
        imc_clasificacion = "Normal"
    elif 25.0 <= imc < 30.0:
        imc_clasificacion = "Sobrepeso"
    else:
        imc_clasificacion = "Obesidad"

    # 2. Calcular ICC
    icc = req.perimetro_cintura_cm / req.perimetro_cadera_cm
    icc = round(icc, 2)

    # Clasificación ICC y riesgo cardiovascular (OMS)
    if sex == "Masculino":
        if icc <= 0.90:
            icc_riesgo = "Bajo"
            distribucion_grasa = "Ginecoide (Pera)"
        elif 0.90 < icc <= 0.95:
            icc_riesgo = "Moderado"
            distribucion_grasa = "Ginecoide (Pera)"
        else:  # icc > 0.95
            icc_riesgo = "Alto"
            distribucion_grasa = "Obesidad Androide (Manzana)"
    else:  # Femenino
        if icc <= 0.80:
            icc_riesgo = "Bajo"
            distribucion_grasa = "Ginecoide (Pera)"
        elif 0.80 < icc <= 0.85:
            icc_riesgo = "Moderado"
            distribucion_grasa = "Ginecoide (Pera)"
        else:  # icc > 0.85
            icc_riesgo = "Alto"
            distribucion_grasa = "Obesidad Androide (Manzana)"

    # Generar Patient_ID y Calculation_ID únicos (Seudonimización ISO 25000)
    calculation_id = str(uuid.uuid4())
    patient_id = str(uuid.uuid4())

    # 3. Registrar en Auditoria_Planes_Table
    try:
        table = get_or_create_auditoria_table()
        log_item = {
            "calculation_id": calculation_id,
            "patient_id": patient_id,
            "peso_kg": Decimal(str(req.peso_kg)),
            "estatura_m": Decimal(str(req.estatura_m)),
            "perimetro_cintura_cm": Decimal(str(req.perimetro_cintura_cm)),
            "perimetro_cadera_cm": Decimal(str(req.perimetro_cadera_cm)),
            "sexo_biologico": sex,
            "imc": Decimal(str(imc)),
            "imc_clasificacion": imc_clasificacion,
            "icc": Decimal(str(icc)),
            "icc_riesgo": icc_riesgo,
            "distribucion_grasa": distribucion_grasa,
            "created_at": datetime.utcnow().isoformat()
        }
        table.put_item(Item=log_item)
    except ClientError as e:
        # No bloqueamos la respuesta en caso de error de persistencia, pero registramos el error
        print(f"Error persisting calculation in DynamoDB: {e}")
        raise HTTPException(status_code=500, detail=f"Error al guardar auditoría en base de datos: {str(e)}")

    return ClinicalCalculateResponse(
        imc=imc,
        imc_clasificacion=imc_clasificacion,
        icc=icc,
        icc_riesgo=icc_riesgo,
        distribucion_grasa=distribucion_grasa
    )
