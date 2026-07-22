"""
Rutas de Sugerencia Automática de Planes (RF5, RF11, RF7)
Genera sugerencias de plan alimenticio basadas en datos antropométricos.

Fórmula utilizada: Harris-Benedict (revisada) para TMB + factor de actividad
para GET, con distribución de macronutrientes según perfil clínico.

Auditable: cada sugerencia incluye la fórmula y parámetros utilizados.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.database import (
    get_or_create_alimentos_table,
    get_or_create_planes_table,
    get_or_create_pacientes_table,
    get_or_create_sugerencias_table,
    convert_decimals,
)
from app.auth import get_current_user, require_role
from app.audit import log_audit_event


def convert_to_decimal_recursive(obj):
    if isinstance(obj, dict):
        return {k: convert_to_decimal_recursive(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_decimal_recursive(i) for i in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, int):
        return Decimal(str(obj))
    return obj

router = APIRouter(prefix="/sugerencia", tags=["Sugerencia de Plan"])


def calcular_tmb_harris(peso_kg: float, estatura_m: float, edad: int, sexo: str) -> float:
    """TMB según Harris-Benedict revisada (RF5)."""
    estatura_cm = estatura_m * 100
    if sexo.strip().capitalize() == "Masculino":
        return round(66.47 + (13.75 * peso_kg) + (5.0 * estatura_cm) - (6.76 * edad), 2)
    else:
        return round(655.10 + (9.56 * peso_kg) + (1.85 * estatura_cm) - (4.68 * edad), 2)


def calcular_get(tmb: float, factor_actividad: float) -> float:
    """Gasto Energético Total."""
    return round(tmb * factor_actividad, 2)


def calcular_distribucion_macros(imc_clasificacion: str, icc_riesgo: str, antecedentes: List[str]) -> dict:
    """
    Determina distribución de macronutrientes según perfil clínico.
    
    Referencias:
    - Normal: 50-60% CHO, 15-20% PROT, 20-30% GRASA
    - Sobrepeso/Obesidad: 45-55% CHO, 20-25% PROT, 20-30% GRASA
    - Riesgo cardiovascular alto: reducir grasa saturada, aumentar fibra
    """
    base = {
        "porcentaje_carbohidratos": 50,
        "porcentaje_proteina": 20,
        "porcentaje_grasa": 30,
        "justificacion": "Distribución balanceada estándar",
    }

    if imc_clasificacion in ["Sobrepeso", "Obesidad"]:
        base = {
            "porcentaje_carbohidratos": 45,
            "porcentaje_proteina": 25,
            "porcentaje_grasa": 30,
            "justificacion": "Plan con mayor proporción proteica para preservar masa magra en paciente con sobrepeso/obesidad",
        }

    if icc_riesgo == "Alto":
        base["porcentaje_grasa"] = 25
        base["porcentaje_carbohidratos"] = 50
        base["porcentaje_proteina"] = 25
        base["justificacion"] += ". Reducción de grasa por riesgo cardiovascular alto."

    if antecedentes:
        for ant in antecedentes:
            if "diabetes" in ant.lower():
                base["porcentaje_carbohidratos"] = 45
                base["porcentaje_proteina"] = 20
                base["porcentaje_grasa"] = 35
                base["justificacion"] += ". Ajuste por diabetes: menor índice glucémico."
                break
            if "hipertensión" in ant.lower() or "hipertension" in ant.lower():
                base["restriccion_sodio"] = True
                base["justificacion"] += ". Restricción de sodio por hipertensión."
                break

    base["gramos_carbohidratos_recomendados"] = None
    base["gramos_proteina_recomendados"] = None
    base["gramos_grasa_recomendados"] = None

    return base


def seleccionar_alimentos_por_macros(
    alimentos_table,
    objetivos_kcal: float,
    distribucion: dict,
    num_alimentos: int = 15,
) -> List[dict]:
    """
    Selecciona alimentos del catálogo que se ajusten a los objetivos calóricos
    y de macronutrientes. Distribuye por categorías para lograr un menú variado.
    """
    response = alimentos_table.scan()
    todos = response.get("Items", [])
    todos = convert_decimals(todos)

    objetivo_prot = (distribucion["porcentaje_proteina"] / 100) * objetivos_kcal / 4
    objetivo_grasa = (distribucion["porcentaje_grasa"] / 100) * objetivos_kcal / 9
    objetivo_CHO = (distribucion["porcentaje_carbohidratos"] / 100) * objetivos_kcal / 4

    categorias_objetivo = {
        "Cereales y derivados": 3,
        "Frutas": 2,
        "Verduras y hortalizas": 3,
        "Carnes y aves": 2,
        "Pescados y mariscos": 1,
        "Lácteos y derivados": 2,
        "Huevos": 1,
        "Legumbres y derivados": 1,
    }

    alimentos_seleccionados = []
    for cat, cantidad in categorias_objetivo.items():
        candidatos = [a for a in todos if a.get("categoria") == cat and (a.get("energia_kcal") or 0) > 0]
        candidatos.sort(key=lambda x: x.get("proteina_g") or 0, reverse=True)
        for al in candidatos[:cantidad]:
            alimentos_seleccionados.append({
                "alimento_id": al["id"],
                "nombre": al["nombre"],
                "categoria": al["categoria"],
                "energia_kcal_100g": al.get("energia_kcal", 0),
                "proteina_g_100g": al.get("proteina_g", 0),
                "grasa_total_g_100g": al.get("grasa_total_g", 0),
                "carbohidratos_g_100g": al.get("carbohidratos_g", 0),
                "sugerencia_gramos": round(objetivos_kcal / (len(alimentos_seleccionados) + 1) * 100 / max(al.get("energia_kcal") or 1, 1), 0),
            })

    return alimentos_seleccionados[:num_alimentos]


@router.post("/generar", response_model=None)
def generar_sugerencia(
    req: dict,
    user: dict = Depends(require_role(["Estudiantes", "Docentes"])),
):
    """
    Genera una sugerencia de plan alimenticio basada en datos antropométricos.
    
    Fórmula: Harris-Benedict revisada para TMB × factor de actividad = GET
    Distribución de macros según IMC, ICC y antecedentes patológicos.
    
    La sugerencia NO se auto-guarda: debe ser aceptada/editada/descartada
    por el nutricionista antes de pasar al expediente (RF7).
    """
    paciente_id = req.get("paciente_id", "")
    peso_kg = req.get("peso_kg", 70)
    estatura_m = req.get("estatura_m", 1.70)
    edad = req.get("edad", 25)
    sexo = req.get("sexo_biologico", "Masculino")
    factor_actividad = req.get("factor_actividad", 1.55)
    imc_clasificacion = req.get("imc_clasificacion", "Normal")
    icc_riesgo = req.get("icc_riesgo", "Bajo")
    antecedentes = req.get("antecedentes", [])

    tmb = calcular_tmb_harris(peso_kg, estatura_m, edad, sexo)
    get_diario = calcular_get(tmb, factor_actividad)
    distribucion = calcular_distribucion_macros(imc_clasificacion, icc_riesgo, antecedentes)

    distribucion["gramos_carbohidratos_recomendados"] = round(
        (distribucion["porcentaje_carbohidratos"] / 100) * get_diario / 4, 1
    )
    distribucion["gramos_proteina_recomendados"] = round(
        (distribucion["porcentaje_proteina"] / 100) * get_diario / 4, 1
    )
    distribucion["gramos_grasa_recomendados"] = round(
        (distribucion["porcentaje_grasa"] / 100) * get_diario / 9, 1
    )

    alimentos_table = get_or_create_alimentos_table()
    alimentos_sugeridos = seleccionar_alimentos_por_macros(alimentos_table, get_diario, distribucion)

    sugerencia_id = str(uuid.uuid4())
    sugerencia_data = {
        "sugerencia_id": sugerencia_id,
        "paciente_id": paciente_id,
        "objetivo_kcal": get_diario,
        "tmb_harris": tmb,
        "distribucion_macros": distribucion,
        "alimentos_sugeridos": alimentos_sugeridos,
        "formula_utilizada": "Harris-Benedict revisada",
        "descripcion_formula": (
            f"TMB = {'66.47 + 13.75×{peso} + 5×{altura_cm} - 6.76×{edad}' if sexo.strip().capitalize() == 'Masculino' else '655.10 + 9.56×{peso} + 1.85×{altura_cm} - 4.68×{edad}'}. "
            f"GET = TMB × {factor_actividad} (factor actividad). "
            f"Macros según perfil: {distribucion['justificacion']}"
        ),
        "parametros_entrada": {
            "peso_kg": peso_kg,
            "estatura_m": estatura_m,
            "edad": edad,
            "sexo": sexo,
            "factor_actividad": factor_actividad,
            "imc_clasificacion": imc_clasificacion,
            "icc_riesgo": icc_riesgo,
            "antecedentes": antecedentes,
        },
        "estado": "pendiente",
        "created_by": user.get("username", "unknown"),
        "created_at": datetime.utcnow().isoformat(),
    }

    sugerencia_data = convert_to_decimal_recursive(sugerencia_data)

    sugerencias_table = get_or_create_sugerencias_table()
    sugerencias_table.put_item(Item=sugerencia_data)

    actor_id = user.get("username", user.get("sub", "unknown"))
    log_audit_event(
        actor_id=actor_id,
        accion="GENERAR_SUGERENCIA",
        entidad="sugerencia_plan",
        entidad_id=sugerencia_id,
        detalle=f"Sugerencia generada para paciente {paciente_id}: {get_diario} kcal",
    )

    return {
        "sugerencia_id": sugerencia_id,
        "objetivo_kcal": get_diario,
        "distribucion_macros": distribucion,
        "alimentos_sugeridos": alimentos_sugeridos,
        "formula_utilizada": "Harris-Benedict revisada",
        "descripcion_formula": sugerencia_data["descripcion_formula"],
    }


@router.post("/{sugerencia_id}/aceptar")
def aceptar_sugerencia(sugerencia_id: str, user: dict = Depends(require_role(["Estudiantes", "Docentes"]))):
    """
    Acepta una sugerencia y la convierte en plan alimenticio.
    Solo después de confirmación del nutricionista (RF7).
    """
    sugerencias_table = get_or_create_sugerencias_table()
    response = sugerencias_table.get_item(Key={"sugerencia_id": sugerencia_id})
    sugerencia = response.get("Item")
    if not sugerencia:
        raise HTTPException(status_code=404, detail="Sugerencia no encontrada")

    planes_table = get_or_create_planes_table()
    plan_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    alimentos_sugeridos = sugerencia.get("alimentos_sugeridos", [])
    alimentos_plan = []
    totales = {
        "energia_kcal": 0, "proteina_g": 0, "grasa_total_g": 0,
        "carbohidratos_g": 0, "fibra_g": 0, "calcio_mg": 0,
        "hierro_mg": 0, "potasio_mg": 0, "sodio_mg": 0,
        "vitamina_c_mg": 0, "vitamina_a_ug": 0, "acido_folico_ug": 0,
        "vitamina_b12_ug": 0,
    }

    comidas = ["Desayuno", "Almuerzo", "Cena", "Colación"]
    for i, al in enumerate(alimentos_sugeridos):
        grams = float(al.get("sugerencia_gramos", 100))
        factor = grams / 100.0
        item = {
            "alimento_id": al.get("alimento_id", ""),
            "nombre": al.get("nombre", ""),
            "cantidad_gramos": grams,
            "comida": comidas[i % len(comidas)],
            "energia_kcal": round(float(al.get("energia_kcal_100g", 0)) * factor, 2),
            "proteina_g": round(float(al.get("proteina_g_100g", 0)) * factor, 2),
            "grasa_total_g": round(float(al.get("grasa_total_g_100g", 0)) * factor, 2),
            "carbohidratos_g": round(float(al.get("carbohidratos_g_100g", 0)) * factor, 2),
        }
        alimentos_plan.append(item)
        for k in totales:
            totales[k] = round(totales[k] + item.get(k, 0), 2)

    plan_data = {
        "plan_id": plan_id,
        "paciente_id": sugerencia.get("paciente_id", ""),
        "tipo_plan": "Sugerido por NutrIA",
        "alimentos": [{k: Decimal(str(v)) if isinstance(v, (int, float)) else v for k, v in a.items()} for a in alimentos_plan],
        "totales": {k: Decimal(str(v)) for k, v in totales.items()},
        "estado": "activo",
        "sugerencia_origen": sugerencia_id,
        "created_by": user.get("username", "unknown"),
        "created_at": now,
        "updated_at": now,
    }
    planes_table.put_item(Item=plan_data)

    sugerencias_table.update_item(
        Key={"sugerencia_id": sugerencia_id},
        UpdateExpression="SET estado = :e, accepted_at = :a",
        ExpressionAttributeValues={":e": "aceptada", ":a": now},
    )

    actor_id = user.get("username", user.get("sub", "unknown"))
    log_audit_event(
        actor_id=actor_id,
        accion="ACEPTAR_SUGERENCIA",
        entidad="sugerencia_plan",
        entidad_id=sugerencia_id,
        detalle=f"Sugerencia aceptada → Plan {plan_id} creado",
    )

    return {"plan_id": plan_id, "mensaje": "Sugerencia aceptada y plan creado"}


@router.get("/historial/{paciente_id}")
def historial_sugerencias(paciente_id: str, user: dict = Depends(get_current_user)):
    """Obtiene el historial de sugerencias de un paciente."""
    sugerencias_table = get_or_create_sugerencias_table()
    try:
        response = sugerencias_table.scan(
            FilterExpression="paciente_id = :pid",
            ExpressionAttributeValues={":pid": paciente_id},
        )
        items = response.get("Items", [])
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return {"sugerencias": convert_decimals(items), "total": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
