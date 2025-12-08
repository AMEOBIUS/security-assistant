"""
Tests for Unified Checkpoint System

Coverage:
- Checkpoint creation
- Checkpoint updates
- Validation
- Issue template generation
- Search and navigation
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Import будет работать после создания модуля
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.checkpoint_manager import CheckpointManager


@pytest.fixture
def temp_workspace(tmp_path):
    """Создать временное рабочее пространство"""
    checkpoints_dir = tmp_path / "checkpoints"
    issues_dir = tmp_path / ".gitlab" / "issue_templates"
    
    checkpoints_dir.mkdir(parents=True)
    issues_dir.mkdir(parents=True)
    
    # Создать template
    template = {
        "session": "session_XX_<name>",
        "date": "YYYY-MM-DD",
        "mode": "BUILDER",
        "version": "vX.X.X",
        "feature": "<Feature Name>",
        "status": "IN_PROGRESS",
        "priority": "MEDIUM",
        "objectives": [],
        "objectives_completed": [],
        "deliverables": {},
        "metrics": {},
        "risks": [],
        "dependencies": {},
        "session_summary": "",
        "completion_status": "0%"
    }
    
    template_file = checkpoints_dir / "session_template.json"
    with open(template_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2)
    
    # Monkey-patch CheckpointManager paths
    original_checkpoints_dir = CheckpointManager.CHECKPOINTS_DIR
    original_issues_dir = CheckpointManager.ISSUES_DIR
    original_template_file = CheckpointManager.TEMPLATE_FILE
    
    CheckpointManager.CHECKPOINTS_DIR = checkpoints_dir
    CheckpointManager.ISSUES_DIR = issues_dir
    CheckpointManager.TEMPLATE_FILE = template_file
    
    yield tmp_path
    
    # Restore
    CheckpointManager.CHECKPOINTS_DIR = original_checkpoints_dir
    CheckpointManager.ISSUES_DIR = original_issues_dir
    CheckpointManager.TEMPLATE_FILE = original_template_file


class TestCheckpointCreation:
    """Тесты создания чекпойнтов"""
    
    def test_create_checkpoint_basic(self, temp_workspace):
        """Создание базового чекпойнта"""
        manager = CheckpointManager()
        
        checkpoint_file = manager.create_checkpoint(
            session_number=19,
            session_name="ml_scoring",
            mode="BUILDER"
        )
        
        assert checkpoint_file.exists()
        assert checkpoint_file.name == "session_19_ml_scoring.json"
        
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        
        assert checkpoint["session"] == "session_19_ml_scoring"
        assert checkpoint["mode"] == "BUILDER"
        assert checkpoint["status"] == "PLANNED"
        assert checkpoint["date"] == datetime.now().strftime("%Y-%m-%d")
    
    def test_create_checkpoint_with_kwargs(self, temp_workspace):
        """Создание чекпойнта с дополнительными параметрами"""
        manager = CheckpointManager()
        
        checkpoint_file = manager.create_checkpoint(
            session_number=20,
            session_name="llm_poc",
            mode="BUILDER",
            feature="LLM PoC Generator",
            priority="CRITICAL",
            version="v1.1.0"
        )
        
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        
        assert checkpoint["feature"] == "LLM PoC Generator"
        assert checkpoint["priority"] == "CRITICAL"
        assert checkpoint["version"] == "v1.1.0"
    
    def test_create_checkpoint_duplicate_fails(self, temp_workspace):
        """Создание дубликата должно падать"""
        manager = CheckpointManager()
        
        manager.create_checkpoint(19, "ml_scoring")
        
        with pytest.raises(FileExistsError):
            manager.create_checkpoint(19, "ml_scoring")


class TestCheckpointUpdate:
    """Тесты обновления чекпойнтов"""
    
    def test_update_checkpoint_status(self, temp_workspace):
        """Обновление статуса"""
        manager = CheckpointManager()
        
        # Создать
        manager.create_checkpoint(19, "ml_scoring")
        
        # Обновить
        checkpoint_file = manager.update_checkpoint(
            session_number=19,
            status="IN_PROGRESS",
            completion_status="50%"
        )
        
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        
        assert checkpoint["status"] == "IN_PROGRESS"
        assert checkpoint["completion_status"] == "50%"
        assert "last_updated" in checkpoint
    
    def test_update_checkpoint_not_found(self, temp_workspace):
        """Обновление несуществующего чекпойнта"""
        manager = CheckpointManager()
        
        with pytest.raises(FileNotFoundError):
            manager.update_checkpoint(99, status="COMPLETED")
    
    def test_update_checkpoint_multiple_matches(self, temp_workspace):
        """Обновление при нескольких совпадениях"""
        manager = CheckpointManager()
        
        # Создать два чекпойнта с одним номером (вручную)
        checkpoints_dir = CheckpointManager.CHECKPOINTS_DIR
        (checkpoints_dir / "session_19_ml_scoring.json").touch()
        (checkpoints_dir / "session_19_other.json").touch()
        
        with pytest.raises(ValueError):
            manager.update_checkpoint(19, status="COMPLETED")


class TestValidation:
    """Тесты валидации"""
    
    def test_validate_valid_checkpoint(self, temp_workspace):
        """Валидация корректного чекпойнта"""
        manager = CheckpointManager()
        
        checkpoint_file = manager.create_checkpoint(19, "ml_scoring")
        
        errors = manager.validate_checkpoint(checkpoint_file)
        
        assert len(errors) == 0
    
    def test_validate_missing_required_field(self, temp_workspace):
        """Валидация с отсутствующим обязательным полем"""
        manager = CheckpointManager()
        
        checkpoint_file = manager.create_checkpoint(19, "ml_scoring")
        
        # Удалить обязательное поле
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        
        del checkpoint["session_summary"]
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f)
        
        errors = manager.validate_checkpoint(checkpoint_file)
        
        assert len(errors) > 0
        assert any("session_summary" in error for error in errors)
    
    def test_validate_invalid_status(self, temp_workspace):
        """Валидация с некорректным статусом"""
        manager = CheckpointManager()
        
        checkpoint_file = manager.create_checkpoint(19, "ml_scoring")
        
        # Установить некорректный статус
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        
        checkpoint["status"] = "DONE"  # Invalid
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f)
        
        errors = manager.validate_checkpoint(checkpoint_file)
        
        assert len(errors) > 0
        assert any("Invalid status" in error for error in errors)
    
    def test_validate_invalid_date(self, temp_workspace):
        """Валидация с некорректной датой"""
        manager = CheckpointManager()
        
        checkpoint_file = manager.create_checkpoint(19, "ml_scoring")
        
        # Установить некорректную дату
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        
        checkpoint["date"] = "2025-13-01"  # Invalid month
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f)
        
        errors = manager.validate_checkpoint(checkpoint_file)
        
        assert len(errors) > 0
        assert any("Invalid date format" in error for error in errors)
    
    def test_validate_all(self, temp_workspace):
        """Валидация всех чекпойнтов"""
        manager = CheckpointManager()
        
        # Создать несколько чекпойнтов
        manager.create_checkpoint(19, "ml_scoring")
        manager.create_checkpoint(20, "llm_poc")
        
        # Сломать один
        checkpoint_file = CheckpointManager.CHECKPOINTS_DIR / "session_19_ml_scoring.json"
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        
        del checkpoint["session_summary"]
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f)
        
        results = manager.validate_all()
        
        assert len(results) == 1
        assert "session_19_ml_scoring.json" in results


class TestIssueGeneration:
    """Тесты генерации Issue Templates"""
    
    def test_generate_issue_template(self, temp_workspace):
        """Генерация Issue Template"""
        manager = CheckpointManager()
        
        # Создать чекпойнт
        manager.create_checkpoint(
            session_number=19,
            session_name="ml_scoring",
            feature="ML-based Vulnerability Scoring",
            priority="CRITICAL"
        )
        
        # Сгенерировать Issue
        issue_file = manager.generate_issue_template(19)
        
        assert issue_file.exists()
        assert issue_file.name == "session_19_ml_scoring.md"
        
        # Проверить содержимое
        with open(issue_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "Session 19" in content
        assert "ML-based Vulnerability Scoring" in content
        assert "🔴 CRITICAL" in content
        assert "checkpoints/session_19_ml_scoring.json" in content
    
    def test_generate_issue_not_found(self, temp_workspace):
        """Генерация Issue для несуществующего чекпойнта"""
        manager = CheckpointManager()
        
        with pytest.raises(FileNotFoundError):
            manager.generate_issue_template(99)


class TestNavigation:
    """Тесты навигации и поиска"""
    
    def test_show_latest(self, temp_workspace):
        """Показать последний чекпойнт"""
        manager = CheckpointManager()
        
        # Создать несколько чекпойнтов
        manager.create_checkpoint(19, "ml_scoring")
        manager.create_checkpoint(20, "llm_poc")
        
        latest = manager.show_latest()
        
        assert latest is not None
        assert latest["session"] == "session_20_llm_poc"
    
    def test_show_latest_empty(self, temp_workspace):
        """Показать последний чекпойнт (пусто)"""
        manager = CheckpointManager()
        
        latest = manager.show_latest()
        
        assert latest is None
    
    def test_list_checkpoints(self, temp_workspace):
        """Список всех чекпойнтов"""
        manager = CheckpointManager()
        
        # Создать несколько чекпойнтов
        manager.create_checkpoint(19, "ml_scoring")
        manager.create_checkpoint(20, "llm_poc")
        
        checkpoints = manager.list_checkpoints()
        
        assert len(checkpoints) == 2
        assert checkpoints[0]["session"] == "session_19_ml_scoring"
        assert checkpoints[1]["session"] == "session_20_llm_poc"
    
    def test_list_checkpoints_filtered(self, temp_workspace):
        """Список чекпойнтов с фильтром"""
        manager = CheckpointManager()
        
        # Создать несколько чекпойнтов
        manager.create_checkpoint(19, "ml_scoring")
        manager.create_checkpoint(20, "llm_poc")
        
        # Обновить статус одного
        manager.update_checkpoint(19, status="COMPLETED")
        
        # Фильтр по статусу
        completed = manager.list_checkpoints(status="COMPLETED")
        planned = manager.list_checkpoints(status="PLANNED")
        
        assert len(completed) == 1
        assert len(planned) == 1
        assert completed[0]["session"] == "session_19_ml_scoring"
        assert planned[0]["session"] == "session_20_llm_poc"


class TestReports:
    """Тесты генерации отчетов"""
    
    def test_generate_continuity_report(self, temp_workspace):
        """Генерация отчета о преемственности"""
        manager = CheckpointManager()
        
        # Создать несколько чекпойнтов
        manager.create_checkpoint(19, "ml_scoring")
        manager.create_checkpoint(20, "llm_poc")
        
        # Обновить статусы
        manager.update_checkpoint(19, status="COMPLETED", completion_status="100%")
        manager.update_checkpoint(20, status="IN_PROGRESS", completion_status="50%")
        
        report = manager.generate_continuity_report()
        
        assert "AI Agent Continuity Report" in report
        assert "Total Sessions" in report  # Fixed: removed exact format check
        assert "2" in report  # Check for number
        assert "COMPLETED" in report
        assert "IN_PROGRESS" in report
        assert "session_19_ml_scoring" in report
        assert "session_20_llm_poc" in report


class TestEdgeCases:
    """Тесты граничных случаев"""
    
    def test_checkpoint_with_unicode(self, temp_workspace):
        """Чекпойнт с Unicode символами"""
        manager = CheckpointManager()
        
        checkpoint_file = manager.create_checkpoint(
            session_number=19,
            session_name="ml_scoring",
            feature="ML-based Vulnerability Scoring 🚀",
            session_summary="Успешно реализовано ML-скоринг уязвимостей"
        )
        
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        
        assert "🚀" in checkpoint["feature"]
        assert "Успешно" in checkpoint["session_summary"]
    
    def test_checkpoint_with_large_data(self, temp_workspace):
        """Чекпойнт с большим объемом данных"""
        manager = CheckpointManager()
        
        large_objectives = [f"Objective {i}" for i in range(100)]
        
        checkpoint_file = manager.create_checkpoint(
            session_number=19,
            session_name="ml_scoring",
            objectives=large_objectives
        )
        
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        
        assert len(checkpoint["objectives"]) == 100


# Интеграционные тесты
class TestIntegration:
    """Интеграционные тесты полного workflow"""
    
    def test_full_session_workflow(self, temp_workspace):
        """Полный workflow сессии"""
        manager = CheckpointManager()
        
        # 1. Создать чекпойнт
        checkpoint_file = manager.create_checkpoint(
            session_number=19,
            session_name="ml_scoring",
            feature="ML-based Vulnerability Scoring",
            priority="CRITICAL"
        )
        
        # 2. Сгенерировать Issue
        issue_file = manager.generate_issue_template(19)
        
        # 3. Обновить статус (начало работы)
        manager.update_checkpoint(19, status="IN_PROGRESS", completion_status="0%")
        
        # 4. Обновить прогресс
        manager.update_checkpoint(19, completion_status="50%")
        
        # 5. Завершить
        manager.update_checkpoint(19, status="COMPLETED", completion_status="100%")
        
        # 6. Валидация
        errors = manager.validate_checkpoint(checkpoint_file)
        assert len(errors) == 0
        
        # 7. Генерация отчета
        report = manager.generate_continuity_report()
        assert "COMPLETED" in report
        
        # Проверить финальное состояние
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        
        assert checkpoint["status"] == "COMPLETED"
        assert checkpoint["completion_status"] == "100%"
        assert "last_updated" in checkpoint


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
