from pydantic import BaseModel

class PlanRequest(BaseModel):
    paciente_id: int
    tipo_plan: str
