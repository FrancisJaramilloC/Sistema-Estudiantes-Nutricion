"""
Rutas del Catálogo de Alimentos (RF9, RF12, RNF14, RES2)
Endpoints REST para búsqueda, filtrado y consulta del catálogo de alimentos
basado en la tabla USFQ. Los valores son inmutables para el usuario final.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from boto3.dynamodb.conditions import Attr
from app.database import get_or_create_alimentos_table, convert_decimals
from app.auth import get_current_user, require_role
from app.audit import log_audit_event

router = APIRouter(prefix="/alimentos", tags=["Alimentos"])


@router.get("")
def listar_alimentos(
    buscar: Optional[str] = Query(None, description="Búsqueda por nombre"),
    categoria: Optional[str] = Query(None, description="Filtro por categoría"),
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    """
    Lista alimentos del catálogo con soporte de búsqueda por nombre
    y filtro por categoría (RF12).
    """
    table = get_or_create_alimentos_table()

    try:
        if categoria:
            response = table.query(
                IndexName='categoria-index',
                KeyConditionExpression='categoria = :cat',
                ExpressionAttributeValues={':cat': categoria}
            )
            items = response.get('Items', [])
        else:
            response = table.scan()
            items = response.get('Items', [])

        if buscar:
            buscar_lower = buscar.lower()
            items = [
                a for a in items
                if buscar_lower in a.get('nombre', '').lower()
                or buscar_lower in a.get('nombre_ingles', '').lower()
                or buscar_lower in a.get('id', '').lower()
            ]

        total = len(items)
        items = items[offset:offset + limite]
        items = convert_decimals(items)

        return {
            "alimentos": items,
            "total": total,
            "limite": limite,
            "offset": offset,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar catálogo: {str(e)}")


@router.get("/categorias")
def listar_categorias(user: dict = Depends(get_current_user)):
    """Devuelve la lista de categorías disponibles."""
    table = get_or_create_alimentos_table()
    try:
        response = table.scan(ProjectionExpression='categoria')
        items = response.get('Items', [])
        categorias = sorted(set(a.get('categoria', '') for a in items if a.get('categoria')))
        return {"categorias": categorias}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{alimento_id}")
def obtener_alimento(alimento_id: str, user: dict = Depends(get_current_user)):
    """Obtiene un alimento específico por su ID."""
    table = get_or_create_alimentos_table()
    try:
        response = table.get_item(Key={"id": alimento_id})
        item = response.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="Alimento no encontrado")
        return convert_decimals(item)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
