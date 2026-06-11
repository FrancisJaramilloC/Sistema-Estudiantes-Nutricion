from pydantic import BaseModel
from typing import List, Optional

class FoodItem(BaseModel):
    nombre: str
    cantidad: str
    comida: str  # "Desayuno", "Almuerzo", "Cena", "Colacion"

class PlanRequest(BaseModel):
    paciente_id: str
    tipo_plan: str
    alimentos: Optional[List[FoodItem]] = []
