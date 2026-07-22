"""
Rutas de Plan Alimenticio con Cálculo Dinámico de Nutrientes (RF9, RF10, RNF2)
Calcula macro/micronutrientes proporcionalmente a la cantidad en gramos usando
la regla de 3 simple basada en valores por 100g de la tabla USFQ.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
from app.database import (
    get_or_create_planes_table,
    get_or_create_alimentos_table,
    get_or_create_auditoria_table,
    convert_decimals,
)
from app.auth import get_current_user, require_role
from app.audit import log_plan_event, log_audit_event, log_report_event
from app.monitoring import validate_privacy
from app.pdf_generator import generar_pdf_plan_nutricional

router = APIRouter(prefix="/planes", tags=["Planes Alimenticios"])


def calcular_nutrientes_por_porcion(alimento_base: dict, cantidad_gramos: float) -> dict:
    """
    Calcula todos los nutrientes proporcionalmente a la cantidad en gramos.
    Regla de 3 simple: (valor_por_100g * cantidad_gramos) / 100
    (RF9, RF10, RNF2)
    """
    from decimal import Decimal as D
    factor = cantidad_gramos / 100.0
    def _to_float(v):
        if v is None:
            return 0.0
        if isinstance(v, D):
            return float(v)
        return float(v)
    return {
        "energia_kcal": round(_to_float(alimento_base.get("energia_kcal")) * factor, 2),
        "proteina_g": round(_to_float(alimento_base.get("proteina_g")) * factor, 2),
        "grasa_total_g": round(_to_float(alimento_base.get("grasa_total_g")) * factor, 2),
        "carbohidratos_g": round(_to_float(alimento_base.get("carbohidratos_g")) * factor, 2),
        "fibra_g": round(_to_float(alimento_base.get("fibra_g")) * factor, 2),
        "calcio_mg": round(_to_float(alimento_base.get("calcio_mg")) * factor, 2),
        "hierro_mg": round(_to_float(alimento_base.get("hierro_mg")) * factor, 2),
        "potasio_mg": round(_to_float(alimento_base.get("potasio_mg")) * factor, 2),
        "sodio_mg": round(_to_float(alimento_base.get("sodio_mg")) * factor, 2),
        "vitamina_c_mg": round(_to_float(alimento_base.get("vitamina_c_mg")) * factor, 2),
        "vitamina_a_ug": round(_to_float(alimento_base.get("vitamina_a_ug")) * factor, 2),
        "acido_folico_ug": round(_to_float(alimento_base.get("acido_folico_ug")) * factor, 2),
        "vitamina_b12_ug": round(_to_float(alimento_base.get("vitamina_b12_ug")) * factor, 2),
    }


class PlanAlimentoInput(BaseModel):
    alimento_id: str
    cantidad_gramos: float
    comida: str


class CrearPlanRequest(BaseModel):
    paciente_id: str
    tipo_plan: str
    alimentos: List[PlanAlimentoInput]


@router.post("", status_code=201)
def crear_plan_alimenticio(
    req: CrearPlanRequest,
    user: dict = Depends(require_role(["Estudiantes", "Docentes"])),
):
    """
    Crea un plan alimenticio calculando todos los nutrientes por porción.
    Persiste alimento base (por id) + cantidad + valores calculados (RF10).
    """
    alimentos_table = get_or_create_alimentos_table()
    planes_table = get_or_create_planes_table()

    plan_id = str(uuid.uuid4())
    actor_id = user.get("username", user.get("sub", "unknown"))
    alimentos_procesados = []
    totales = {
        "energia_kcal": 0, "proteina_g": 0, "grasa_total_g": 0,
        "carbohidratos_g": 0, "fibra_g": 0, "calcio_mg": 0,
        "hierro_mg": 0, "potasio_mg": 0, "sodio_mg": 0,
        "vitamina_c_mg": 0, "vitamina_a_ug": 0, "acido_folico_ug": 0,
        "vitamina_b12_ug": 0,
    }

    for alimento_input in req.alimentos:
        response = alimentos_table.get_item(Key={"id": alimento_input.alimento_id})
        alimento_base = response.get("Item")
        if not alimento_base:
            raise HTTPException(
                status_code=404,
                detail=f"Alimento {alimento_input.alimento_id} no encontrado en catálogo"
            )

        nutrientes = calcular_nutrientes_por_porcion(alimento_base, alimento_input.cantidad_gramos)

        item_procesado = {
            "alimento_id": alimento_input.alimento_id,
            "nombre": alimento_base.get("nombre", ""),
            "cantidad_gramos": alimento_input.cantidad_gramos,
            "comida": alimento_input.comida,
            **nutrientes,
        }
        alimentos_procesados.append(item_procesado)

        for key in totales:
            totales[key] = round(totales[key] + nutrientes.get(key, 0), 2)

    now = datetime.utcnow().isoformat()
    plan_data = {
        "plan_id": plan_id,
        "paciente_id": req.paciente_id,
        "tipo_plan": req.tipo_plan,
        "alimentos": [
            {k: Decimal(str(v)) if isinstance(v, (int, float)) else v for k, v in a.items()}
            for a in alimentos_procesados
        ],
        "totales": {k: Decimal(str(v)) for k, v in totales.items()},
        "estado": "activo",
        "created_by": actor_id,
        "created_at": now,
        "updated_at": now,
    }

    planes_table.put_item(Item=plan_data)
    log_plan_event(actor_id, "CREATE", plan_id, f"Plan {req.tipo_plan} para paciente {req.paciente_id}")

    return {
        "plan_id": plan_id,
        "alimentos": alimentos_procesados,
        "totales": totales,
        "mensaje": "Plan alimenticio creado con éxito",
    }


@router.get("/{plan_id}")
def obtener_plan(plan_id: str, user: dict = Depends(get_current_user)):
    """Obtiene un plan alimenticio por ID."""
    planes_table = get_or_create_planes_table()
    try:
        response = planes_table.get_item(Key={"plan_id": plan_id})
        item = response.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="Plan no encontrado")
        return convert_decimals(item)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/paciente/{paciente_id}")
def planes_por_paciente(paciente_id: str, user: dict = Depends(get_current_user)):
    """Obtiene todos los planes de un paciente (histórico)."""
    planes_table = get_or_create_planes_table()
    try:
        response = planes_table.scan(
            FilterExpression="paciente_id = :pid",
            ExpressionAttributeValues={":pid": paciente_id},
        )
        items = response.get("Items", [])
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return {"planes": convert_decimals(items), "total": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{plan_id}")
def actualizar_plan(
    plan_id: str,
    req: CrearPlanRequest,
    user: dict = Depends(require_role(["Estudiantes", "Docentes"])),
):
    """Actualiza un plan alimenticio existente recalculando nutrientes."""
    alimentos_table = get_or_create_alimentos_table()
    planes_table = get_or_create_planes_table()

    existing = planes_table.get_item(Key={"plan_id": plan_id})
    if not existing.get("Item"):
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    actor_id = user.get("username", user.get("sub", "unknown"))
    alimentos_procesados = []
    totales = {
        "energia_kcal": 0, "proteina_g": 0, "grasa_total_g": 0,
        "carbohidratos_g": 0, "fibra_g": 0, "calcio_mg": 0,
        "hierro_mg": 0, "potasio_mg": 0, "sodio_mg": 0,
        "vitamina_c_mg": 0, "vitamina_a_ug": 0, "acido_folico_ug": 0,
        "vitamina_b12_ug": 0,
    }

    for alimento_input in req.alimentos:
        response = alimentos_table.get_item(Key={"id": alimento_input.alimento_id})
        alimento_base = response.get("Item")
        if not alimento_base:
            raise HTTPException(status_code=404, detail=f"Alimento {alimento_input.alimento_id} no encontrado")

        nutrientes = calcular_nutrientes_por_porcion(alimento_base, alimento_input.cantidad_gramos)
        item_procesado = {
            "alimento_id": alimento_input.alimento_id,
            "nombre": alimento_base.get("nombre", ""),
            "cantidad_gramos": alimento_input.cantidad_gramos,
            "comida": alimento_input.comida,
            **nutrientes,
        }
        alimentos_procesados.append(item_procesado)
        for key in totales:
            totales[key] = round(totales[key] + nutrientes.get(key, 0), 2)

    now = datetime.utcnow().isoformat()
    planes_table.update_item(
        Key={"plan_id": plan_id},
        UpdateExpression="SET alimentos = :a, totales = :t, tipo_plan = :tp, paciente_id = :pid, updated_at = :u",
        ExpressionAttributeValues={
            ":a": [{k: Decimal(str(v)) if isinstance(v, (int, float)) else v for k, v in al.items()} for al in alimentos_procesados],
            ":t": {k: Decimal(str(v)) for k, v in totales.items()},
            ":tp": req.tipo_plan,
            ":pid": req.paciente_id,
            ":u": now,
        },
    )

    log_plan_event(actor_id, "UPDATE", plan_id, f"Plan actualizado con {len(alimentos_procesados)} alimentos")

    return {
        "plan_id": plan_id,
        "alimentos": alimentos_procesados,
        "totales": totales,
        "mensaje": "Plan actualizado con éxito",
    }


@router.post("/calcular-porcion")
def calcular_porcion(alimento_id: str, cantidad_gramos: float, user: dict = Depends(get_current_user)):
    """
    Endpoint ligero para calcular nutrientes de una porción específica.
    Usado por el frontend para recálculo en vivo en <100ms (RNF2).
    """
    alimentos_table = get_or_create_alimentos_table()
    response = alimentos_table.get_item(Key={"id": alimento_id})
    alimento_base = response.get("Item")
    if not alimento_base:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")

    nutrientes = calcular_nutrientes_por_porcion(alimento_base, cantidad_gramos)
    return nutrientes


@router.delete("/{plan_id}")
def eliminar_plan(plan_id: str, user: dict = Depends(require_role(["Docentes"]))):
    """Elimina un plan alimenticio (solo docentes)."""
    planes_table = get_or_create_planes_table()
    existing = planes_table.get_item(Key={"plan_id": plan_id})
    if not existing.get("Item"):
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    planes_table.delete_item(Key={"plan_id": plan_id})
    actor_id = user.get("username", user.get("sub", "unknown"))
    log_plan_event(actor_id, "DELETE", plan_id)
    return {"mensaje": "Plan eliminado con éxito"}


@router.get("/{plan_id}/pdf")
def descargar_pdf_plan(
    plan_id: str,
    user: dict = Depends(require_role(["Estudiantes", "Docentes"])),
):
    """
    Descarga el PDF completo de un plan alimenticio con logo Nutria,
    datos del paciente, distribucion de macros, totales y desglose por comida.
    """
    planes_table = get_or_create_planes_table()
    try:
        response = planes_table.get_item(Key={"plan_id": plan_id})
        plan = response.get("Item")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    plan = convert_decimals(plan)
    actor_id = user.get("username", user.get("sub", "unknown"))

    pdf_buf = generar_pdf_plan_nutricional(plan)
    filename = f"plan_nutricional_{plan.get('paciente_id', plan_id[:8])}.pdf"

    log_report_event(actor_id, "PLAN_PDF", f"PDF descargado para plan {plan_id[:8]}...")

    return Response(
        content=pdf_buf.read(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )
