import uuid
from decimal import Decimal
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from botocore.exceptions import ClientError
from app.database import get_or_create_auditoria_table
from app.auth import require_role
from app.monitoring import track_clinical_performance, validate_privacy

router = APIRouter(tags=["Clinical"])

class ClinicalCalculateRequest(BaseModel):
    peso_kg: float = Field(..., gt=0)
    estatura_m: float = Field(..., gt=0)
    perimetro_cintura_cm: float = Field(..., gt=0)
    perimetro_cadera_cm: float = Field(..., gt=0)
    sexo_biologico: str = Field(...)
    edad: int = Field(..., gt=0, le=120)
    factor_actividad: float = Field(...)
    efecto_termogenico: float = Field(..., ge=1.0, le=10.0)

class ClinicalCalculateResponse(BaseModel):
    imc: float
    imc_clasificacion: str
    icc: float
    icc_riesgo: str
    distribucion_grasa: str
    tmb_harris: float
    tmb_mifflin: float
    gasto_total_harris: float
    gasto_total_mifflin: float

@router.post("/clinical/calculate", response_model=ClinicalCalculateResponse)
async def calculate_clinical(
    req: ClinicalCalculateRequest,
    user: dict = Depends(require_role(["Estudiantes", "Docentes"]))
):
    sex = req.sexo_biologico.strip().capitalize()
    if sex not in ["Masculino", "Femenino"]:
        raise HTTPException(status_code=400, detail="El sexo biológico debe ser 'Masculino' o 'Femenino'.")

    with track_clinical_performance():
        imc = round(req.peso_kg / (req.estatura_m ** 2), 2)

        if imc < 18.5:
            imc_clasificacion = "Bajo peso"
        elif 18.5 <= imc < 25.0:
            imc_clasificacion = "Normal"
        elif 25.0 <= imc < 30.0:
            imc_clasificacion = "Sobrepeso"
        else:
            imc_clasificacion = "Obesidad"

        icc = round(req.perimetro_cintura_cm / req.perimetro_cadera_cm, 2)

        if sex == "Masculino":
            if icc <= 0.90:
                icc_riesgo = "Bajo"
                distribucion_grasa = "Ginecoide (Pera)"
            elif 0.90 < icc <= 0.95:
                icc_riesgo = "Moderado"
                distribucion_grasa = "Ginecoide (Pera)"
            else:
                icc_riesgo = "Alto"
                distribucion_grasa = "Obesidad Androide (Manzana)"
        else:
            if icc <= 0.80:
                icc_riesgo = "Bajo"
                distribucion_grasa = "Ginecoide (Pera)"
            elif 0.80 < icc <= 0.85:
                icc_riesgo = "Moderado"
                distribucion_grasa = "Ginecoide (Pera)"
            else:
                icc_riesgo = "Alto"
                distribucion_grasa = "Obesidad Androide (Manzana)"

        estatura_cm = req.estatura_m * 100

        if sex == "Masculino":
            tmb_harris = 66.47 + (13.75 * req.peso_kg) + (5.0 * estatura_cm) - (6.76 * req.edad)
        else:
            tmb_harris = 655.10 + (9.56 * req.peso_kg) + (1.85 * estatura_cm) - (4.68 * req.edad)

        if sex == "Masculino":
            tmb_mifflin = (10.0 * req.peso_kg) + (6.25 * estatura_cm) - (5.0 * req.edad) + 5.0
        else:
            tmb_mifflin = (10.0 * req.peso_kg) + (6.25 * estatura_cm) - (5.0 * req.edad) - 161.0

        gasto_total_harris = (tmb_harris * req.factor_actividad) * (1.0 + (req.efecto_termogenico / 100.0))
        gasto_total_mifflin = (tmb_mifflin * req.factor_actividad) * (1.0 + (req.efecto_termogenico / 100.0))

        tmb_harris = round(tmb_harris, 2)
        tmb_mifflin = round(tmb_mifflin, 2)
        gasto_total_harris = round(gasto_total_harris, 2)
        gasto_total_mifflin = round(gasto_total_mifflin, 2)

        calculation_id = str(uuid.uuid4())
        patient_id = str(uuid.uuid4())

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
                "edad": int(req.edad),
                "factor_actividad": Decimal(str(req.factor_actividad)),
                "efecto_termogenico": Decimal(str(req.efecto_termogenico)),
                "imc": Decimal(str(imc)),
                "imc_clasificacion": imc_clasificacion,
                "icc": Decimal(str(icc)),
                "icc_riesgo": icc_riesgo,
                "distribucion_grasa": distribucion_grasa,
                "tmb_harris": Decimal(str(tmb_harris)),
                "tmb_mifflin": Decimal(str(tmb_mifflin)),
                "gasto_total_harris": Decimal(str(gasto_total_harris)),
                "gasto_total_mifflin": Decimal(str(gasto_total_mifflin)),
                "created_at": datetime.utcnow().isoformat()
            }

            validate_privacy(log_item)

            table.put_item(Item=log_item)
        except ClientError as e:
            print(f"Error persisting calculation in DynamoDB: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error al guardar auditoría en base de datos: {str(e)}"
            )

    return ClinicalCalculateResponse(
        imc=imc,
        imc_clasificacion=imc_clasificacion,
        icc=icc,
        icc_riesgo=icc_riesgo,
        distribucion_grasa=distribucion_grasa,
        tmb_harris=tmb_harris,
        tmb_mifflin=tmb_mifflin,
        gasto_total_harris=gasto_total_harris,
        gasto_total_mifflin=gasto_total_mifflin
    )
