"""
Tests for app.tasks — validates process_plan_task background processing.
"""

from tests.conftest import _fake_tables


class TestProcessPlanTask:
    def test_successful_processing(self):
        """A task should transition from PENDIENTE -> PROCESANDO -> COMPLETADO."""
        from app.tasks import process_plan_task
        from tests.conftest import _get_fake_table

        # Manually seed a task in the mock database
        table = _get_fake_table("tasks")
        table.put_item(Item={
            "task_id": "task-001",
            "paciente_id": "pat-001",
            "tipo_plan": "Estandar",
            "estado_actual": "PENDIENTE",
        })

        process_plan_task("task-001", "pat-001", "Estandar")

        # Verify final state in the mock database
        result = table.get_item(Key={"task_id": "task-001"})
        item = result.get("Item", {})
        assert item["estado_actual"] == "COMPLETADO"
        assert "started_at" in item
        assert "finished_at" in item
        assert "updated_at" in item

    def test_error_handling(self):
        """If an error occurs (e.g. table missing), the function should not crash."""
        from app.tasks import process_plan_task

        # Pass invalid data; function should handle it gracefully
        process_plan_task("task-error", None, None)
        # No exception means error handling works
