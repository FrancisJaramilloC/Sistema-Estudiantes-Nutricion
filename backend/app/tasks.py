import time
from datetime import datetime
from app.database import get_or_create_table

def process_plan_task(task_id: str, paciente_id: str, tipo_plan: str):
    try:
        table = get_or_create_table()
        print(f" [x] Iniciando tarea {task_id} en segundo plano para paciente {paciente_id}")
        table.update_item(
            Key={"task_id": task_id},
            UpdateExpression="SET estado_actual = :state, started_at = :started, updated_at = :updated",
            ExpressionAttributeValues={
                ":state": "PROCESANDO",
                ":started": datetime.utcnow().isoformat(),
                ":updated": datetime.utcnow().isoformat()
            }
        )
        time.sleep(5)
        table.update_item(
            Key={"task_id": task_id},
            UpdateExpression="SET estado_actual = :state, finished_at = :finished, updated_at = :updated",
            ExpressionAttributeValues={
                ":state": "COMPLETADO",
                ":finished": datetime.utcnow().isoformat(),
                ":updated": datetime.utcnow().isoformat()
            }
        )
        print(f" [v] Tarea {task_id} completada con éxito.")
    except Exception as e:
        print(f" [!] Error procesando tarea {task_id}: {e}")
        try:
            table = get_or_create_table()
            table.update_item(
                Key={"task_id": task_id},
                UpdateExpression="SET estado_actual = :state, error_message = :err, updated_at = :updated",
                ExpressionAttributeValues={
                    ":state": "FALLIDO",
                    ":err": str(e),
                    ":updated": datetime.utcnow().isoformat()
                }
            )
        except Exception as db_err:
            print(f"Error actualizando tarea a FALLIDO en base de datos: {db_err}")
