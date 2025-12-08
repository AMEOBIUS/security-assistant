#!/usr/bin/env python3
"""
Example: Using Unified Checkpoint System

Демонстрирует полный workflow работы с чекпойнтами:
1. Создание нового чекпойнта
2. Генерация Issue Template
3. Обновление прогресса
4. Валидация
5. Генерация отчета
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.checkpoint_manager import CheckpointManager


def example_full_workflow():
    """Полный workflow сессии"""
    print("=" * 80)
    print("Unified Checkpoint System - Full Workflow Example")
    print("=" * 80)
    
    manager = CheckpointManager()
    
    # 1. Создать чекпойнт для новой сессии
    print("\n1️⃣ Creating checkpoint for Session 19: ML Scoring...")
    checkpoint_file = manager.create_checkpoint(
        session_number=19,
        session_name="ml_scoring",
        mode="BUILDER",
        feature="ML-based Vulnerability Scoring",
        priority="CRITICAL",
        version="v1.1.0"
    )
    print(f"   ✅ Created: {checkpoint_file}")
    
    # 2. Сгенерировать Issue Template
    print("\n2️⃣ Generating GitLab Issue Template...")
    issue_file = manager.generate_issue_template(19)
    print(f"   ✅ Generated: {issue_file}")
    
    # 3. Обновить статус (начало работы)
    print("\n3️⃣ Starting work (IN_PROGRESS)...")
    manager.update_checkpoint(
        session_number=19,
        status="IN_PROGRESS",
        completion_status="0%"
    )
    print("   ✅ Status updated: IN_PROGRESS (0%)")
    
    # 4. Обновить прогресс (25%)
    print("\n4️⃣ Updating progress (25%)...")
    manager.update_checkpoint(
        session_number=19,
        completion_status="25%"
    )
    print("   ✅ Progress updated: 25%")
    
    # 5. Обновить прогресс (50%)
    print("\n5️⃣ Updating progress (50%)...")
    manager.update_checkpoint(
        session_number=19,
        completion_status="50%"
    )
    print("   ✅ Progress updated: 50%")
    
    # 6. Обновить прогресс (75%)
    print("\n6️⃣ Updating progress (75%)...")
    manager.update_checkpoint(
        session_number=19,
        completion_status="75%"
    )
    print("   ✅ Progress updated: 75%")
    
    # 7. Завершить сессию
    print("\n7️⃣ Completing session (COMPLETED)...")
    manager.update_checkpoint(
        session_number=19,
        status="COMPLETED",
        completion_status="100%"
    )
    print("   ✅ Status updated: COMPLETED (100%)")
    
    # 8. Валидация
    print("\n8️⃣ Validating checkpoint...")
    errors = manager.validate_checkpoint(checkpoint_file)
    if errors:
        print(f"   ❌ Validation failed: {len(errors)} errors")
        for error in errors:
            print(f"      - {error}")
    else:
        print("   ✅ Validation passed")
    
    # 9. Показать последний чекпойнт
    print("\n9️⃣ Showing latest checkpoint...")
    latest = manager.show_latest()
    
    # 10. Генерация отчета
    print("\n🔟 Generating continuity report...")
    report = manager.generate_continuity_report()
    report_file = Path("docs/AI_AGENT_CONTINUITY_REPORT.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"   ✅ Report generated: {report_file}")
    
    print("\n" + "=" * 80)
    print("✅ Full workflow completed successfully!")
    print("=" * 80)


def example_list_and_filter():
    """Пример поиска и фильтрации"""
    print("\n" + "=" * 80)
    print("Unified Checkpoint System - List & Filter Example")
    print("=" * 80)
    
    manager = CheckpointManager()
    
    # Список всех чекпойнтов
    print("\n📋 All checkpoints:")
    all_checkpoints = manager.list_checkpoints()
    for cp in all_checkpoints:
        print(f"   {cp['session']:<40} {cp['status']:<15} {cp['completion']}")
    
    # Только завершенные
    print("\n✅ Completed checkpoints:")
    completed = manager.list_checkpoints(status="COMPLETED")
    for cp in completed:
        print(f"   {cp['session']:<40} {cp['date']}")
    
    # Только в процессе
    print("\n⏳ In-progress checkpoints:")
    in_progress = manager.list_checkpoints(status="IN_PROGRESS")
    for cp in in_progress:
        print(f"   {cp['session']:<40} {cp['completion']}")
    
    # Только запланированные
    print("\n📅 Planned checkpoints:")
    planned = manager.list_checkpoints(status="PLANNED")
    for cp in planned:
        print(f"   {cp['session']:<40} {cp['feature']}")


def example_validation():
    """Пример валидации"""
    print("\n" + "=" * 80)
    print("Unified Checkpoint System - Validation Example")
    print("=" * 80)
    
    manager = CheckpointManager()
    
    # Валидация всех чекпойнтов
    print("\n🔍 Validating all checkpoints...")
    results = manager.validate_all()
    
    if not results:
        print("   ✅ All checkpoints are valid")
    else:
        print(f"   ❌ Found {len(results)} invalid checkpoints:\n")
        for filename, errors in results.items():
            print(f"   {filename}:")
            for error in errors:
                print(f"      - {error}")


def example_create_multiple():
    """Пример создания нескольких чекпойнтов"""
    print("\n" + "=" * 80)
    print("Unified Checkpoint System - Create Multiple Example")
    print("=" * 80)
    
    manager = CheckpointManager()
    
    sessions = [
        (19, "ml_scoring", "ML-based Vulnerability Scoring", "CRITICAL"),
        (20, "llm_poc_generator", "LLM PoC Generator", "CRITICAL"),
        (21, "nlq_interface", "Natural Language Query Interface", "HIGH"),
        (22, "cloud_native_k8s", "Cloud-Native Kubernetes Support", "CRITICAL"),
    ]
    
    print("\n📝 Creating multiple checkpoints...")
    for session_num, name, feature, priority in sessions:
        try:
            checkpoint_file = manager.create_checkpoint(
                session_number=session_num,
                session_name=name,
                feature=feature,
                priority=priority,
                version="v1.1.0" if session_num <= 21 else "v1.2.0"
            )
            print(f"   ✅ Session {session_num}: {name}")
        except FileExistsError:
            print(f"   ⏭️  Session {session_num}: Already exists")
    
    # Генерация Issue Templates для всех
    print("\n📄 Generating Issue Templates...")
    for session_num, name, _, _ in sessions:
        try:
            issue_file = manager.generate_issue_template(session_num)
            print(f"   ✅ Session {session_num}: {issue_file.name}")
        except Exception as e:
            print(f"   ❌ Session {session_num}: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Checkpoint System Examples")
    parser.add_argument(
        "--example",
        choices=["full", "list", "validate", "create"],
        default="full",
        help="Which example to run"
    )
    
    args = parser.parse_args()
    
    if args.example == "full":
        example_full_workflow()
    elif args.example == "list":
        example_list_and_filter()
    elif args.example == "validate":
        example_validation()
    elif args.example == "create":
        example_create_multiple()
