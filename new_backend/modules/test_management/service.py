"""
test_management/service.py
─────────────────────────────
All business logic for the Test Management module — CRUD for the 9 entities,
the /run-tests orchestration, and dashboard aggregation. Flat "_flow"
functions, matching jira/service.py and test_runner/service.py: no
repository/controller layers, HTTPException raised directly.
"""

import json
import re
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from new_backend.core.logger import logger
from new_backend.modules.test_management import models as schemas
from new_backend.modules.test_management.db_models import (
    Application,
    Attachment,
    Bug,
    ExecutionLog,
    Module,
    Priority,
    TestCase,
    TestRun,
    TestRunResult,
)
from new_backend.modules.test_management.runner import runner_service
from new_backend.modules.test_management.discovery import discover_automation_tests


# ─────────────────────────────────────────────────────────────────────────
# Small local helpers
# ─────────────────────────────────────────────────────────────────────────
def _paginate(page: int, page_size: int) -> tuple[int, int]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), schemas.MAX_PAGE_SIZE)
    return page, page_size


def _paginated(items, total: int, page: int, page_size: int, schema) -> dict:
    total_pages = (total + page_size - 1) // page_size if page_size else 0
    return {
        "items": [schema.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def _abbreviate(name: str, length: int) -> str:
    words = re.findall(r"[A-Za-z0-9]+", name or "")
    if not words:
        return "GEN"
    if len(words) == 1:
        return words[0][:length].upper()
    return "".join(w[0] for w in words)[:length].upper() or words[0][:length].upper()


def _next_testcase_key(db: Session, application_name: str, module_name: str) -> str:
    prefix = f"{_abbreviate(application_name, 3)}_{_abbreviate(module_name, 4)}"
    existing = db.scalars(select(TestCase.testcase_key).where(TestCase.testcase_key.like(f"{prefix}_%"))).all()
    max_seq = 0
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)$")
    for key in existing:
        m = pattern.match(key)
        if m:
            max_seq = max(max_seq, int(m.group(1)))
    return f"{prefix}_{max_seq + 1:03d}"


# ═══════════════════════════════════════════════════════════════════════
# Applications
# ═══════════════════════════════════════════════════════════════════════
def create_application_flow(payload: schemas.ApplicationCreate, db: Session) -> Application:
    obj = Application(**payload.model_dump())
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_applications_flow(status: bool | None, q: str | None, page: int, page_size: int, db: Session) -> dict:
    page, page_size = _paginate(page, page_size)
    filters = []
    if status is not None:
        filters.append(Application.status == status)
    if q:
        filters.append(Application.application_name.ilike(f"%{q}%"))

    stmt = select(Application).where(*filters)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(Application.application_name.asc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return _paginated(items, total, page, page_size, schemas.ApplicationRead)


def get_application_flow(application_id: str, db: Session) -> Application:
    obj = db.get(Application, application_id)
    if not obj:
        raise HTTPException(404, f"Application {application_id} not found")
    return obj


def update_application_flow(application_id: str, payload: schemas.ApplicationUpdate, db: Session) -> Application:
    obj = get_application_flow(application_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.flush()
    db.refresh(obj)
    return obj


def delete_application_flow(application_id: str, db: Session) -> None:
    obj = get_application_flow(application_id, db)
    db.delete(obj)
    db.flush()


# ═══════════════════════════════════════════════════════════════════════
# Modules
# ═══════════════════════════════════════════════════════════════════════
def create_module_flow(payload: schemas.ModuleCreate, db: Session) -> Module:
    obj = Module(**payload.model_dump())
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_modules_flow(
    application_id: str | None, status: bool | None, page: int, page_size: int, db: Session
) -> dict:
    page, page_size = _paginate(page, page_size)
    filters = []
    if application_id:
        filters.append(Module.application_id == application_id)
    if status is not None:
        filters.append(Module.status == status)

    stmt = select(Module).where(*filters)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(Module.display_order.asc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return _paginated(items, total, page, page_size, schemas.ModuleRead)


def get_module_flow(module_id: str, db: Session) -> Module:
    obj = db.get(Module, module_id)
    if not obj:
        raise HTTPException(404, f"Module {module_id} not found")
    return obj


def update_module_flow(module_id: str, payload: schemas.ModuleUpdate, db: Session) -> Module:
    obj = get_module_flow(module_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.flush()
    db.refresh(obj)
    return obj


def delete_module_flow(module_id: str, db: Session) -> None:
    obj = get_module_flow(module_id, db)
    db.delete(obj)
    db.flush()


# ═══════════════════════════════════════════════════════════════════════
# Priorities
# ═══════════════════════════════════════════════════════════════════════
def create_priority_flow(payload: schemas.PriorityCreate, db: Session) -> Priority:
    obj = Priority(**payload.model_dump())
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_priorities_flow(page: int, page_size: int, db: Session) -> dict:
    page, page_size = _paginate(page, page_size)
    stmt = select(Priority)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(Priority.display_order.asc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return _paginated(items, total, page, page_size, schemas.PriorityRead)


def get_priority_flow(priority_id: str, db: Session) -> Priority:
    obj = db.get(Priority, priority_id)
    if not obj:
        raise HTTPException(404, f"Priority {priority_id} not found")
    return obj


def update_priority_flow(priority_id: str, payload: schemas.PriorityUpdate, db: Session) -> Priority:
    obj = get_priority_flow(priority_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.flush()
    db.refresh(obj)
    return obj


def delete_priority_flow(priority_id: str, db: Session) -> None:
    obj = get_priority_flow(priority_id, db)
    db.delete(obj)
    db.flush()


# ═══════════════════════════════════════════════════════════════════════
# Test Cases
# ═══════════════════════════════════════════════════════════════════════
def create_test_case_flow(payload: schemas.TestCaseCreate, db: Session) -> TestCase:
    application = db.get(Application, payload.application_id)
    if not application:
        raise HTTPException(404, f"Application {payload.application_id} not found")
    module = db.get(Module, payload.module_id)
    if not module:
        raise HTTPException(404, f"Module {payload.module_id} not found")
    if module.application_id != payload.application_id:
        raise HTTPException(409, "Module does not belong to the given application")

    data = payload.model_dump()
    testcase_key = data.pop("testcase_key", None)
    if testcase_key:
        if db.scalar(select(TestCase).where(TestCase.testcase_key == testcase_key)):
            raise HTTPException(409, f"Test case key '{testcase_key}' already exists")
    else:
        testcase_key = _next_testcase_key(db, application.application_name, module.module_name)

    obj = TestCase(**data, testcase_key=testcase_key)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_test_cases_flow(
    application_id: str | None,
    module_id: str | None,
    priority_id: str | None,
    test_type: str | None,
    status: bool | None,
    polarity: str | None,
    q: str | None,
    page: int,
    page_size: int,
    db: Session,
) -> dict:
    page, page_size = _paginate(page, page_size)
    filters = []
    if application_id:
        filters.append(TestCase.application_id == application_id)
    if module_id:
        filters.append(TestCase.module_id == module_id)
    if priority_id:
        filters.append(TestCase.priority_id == priority_id)
    if status is not None:
        filters.append(TestCase.status == status)
    if polarity:
        filters.append(TestCase.polarity == polarity)
    if test_type:
        filters.append(func.json_contains(TestCase.test_types, json.dumps(test_type)))
    if q:
        like = f"%{q}%"
        filters.append(or_(TestCase.title.ilike(like), TestCase.testcase_key.ilike(like), TestCase.description.ilike(like)))

    stmt = select(TestCase).where(*filters)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(TestCase.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return _paginated(items, total, page, page_size, schemas.TestCaseRead)


def get_test_case_flow(testcase_id: str, db: Session) -> TestCase:
    obj = db.get(TestCase, testcase_id)
    if not obj:
        raise HTTPException(404, f"Test case {testcase_id} not found")
    return obj


def update_test_case_flow(testcase_id: str, payload: schemas.TestCaseUpdate, db: Session) -> TestCase:
    obj = get_test_case_flow(testcase_id, db)
    data = payload.model_dump(exclude_unset=True)
    if "module_id" in data:
        module = db.get(Module, data["module_id"])
        if not module:
            raise HTTPException(404, f"Module {data['module_id']} not found")
        if module.application_id != obj.application_id:
            raise HTTPException(409, "Module does not belong to this test case's application")
    for field, value in data.items():
        setattr(obj, field, value)
    db.flush()
    db.refresh(obj)
    return obj


def delete_test_case_flow(testcase_id: str, db: Session) -> None:
    obj = get_test_case_flow(testcase_id, db)
    db.delete(obj)
    db.flush()


# ═══════════════════════════════════════════════════════════════════════
# Test Runs — POST /run-tests orchestration
# ═══════════════════════════════════════════════════════════════════════
def run_tests_flow(payload: schemas.TestRunCreate, db: Session) -> dict:
    started = datetime.utcnow()

    run = TestRun(
        run_name=payload.run_name or f"Run {started.strftime('%Y-%m-%d %H:%M:%S')}",
        application_id=payload.application_id,
        module_id=payload.module_id,
        test_type=payload.test_type,
        environment=payload.environment,
        build_number=payload.build_number,
        execution_type=payload.execution_type,
        triggered_by=payload.triggered_by,
        status="RUNNING",
        started_at=started,
    )
    db.add(run)
    db.flush()
    db.refresh(run)

    filters = [TestCase.application_id == payload.application_id, TestCase.status.is_(True)]
    if payload.module_id:
        filters.append(TestCase.module_id == payload.module_id)
    if payload.test_type:
        filters.append(func.json_contains(TestCase.test_types, json.dumps(payload.test_type)))

    matching_cases = db.scalars(select(TestCase).where(*filters)).all()
    testcase_ids = [tc.testcase_id for tc in matching_cases]

    # Still a valid, informative outcome when nothing matches — not an error.
    runner_results = (
        runner_service.run_tests(testcase_ids, payload.environment, payload.execution_type) if testcase_ids else []
    )

    created_results: list[TestRunResult] = []
    for r in runner_results:
        result = TestRunResult(
            run_id=run.run_id,
            testcase_id=r.testcase_id,
            status=r.status,
            execution_time=Decimal(str(r.execution_time)),
            device_name=r.device_name,
            os_version=r.os_version,
            browser=r.browser,
            failure_reason=r.failure_reason,
            allure_report=None,
            started_at=r.started_at,
            completed_at=r.completed_at,
        )
        db.add(result)
        created_results.append(result)
    if created_results:
        db.flush()
        for result in created_results:
            db.refresh(result)

    log_rows = [
        ExecutionLog(execution_id=db_result.execution_id, log_level=level, message=message)
        for db_result, runner_result in zip(created_results, runner_results)
        for level, message in runner_result.log_lines
    ]
    if log_rows:
        db.add_all(log_rows)
        db.flush()

    completed = datetime.utcnow()
    passed = sum(1 for r in runner_results if r.status == "PASSED")
    failed = sum(1 for r in runner_results if r.status == "FAILED")
    skipped = len(runner_results) - passed - failed

    run.status = "COMPLETED"
    run.completed_at = completed
    db.flush()
    db.refresh(run)

    logger.info(
        "run-tests: run_id=%s total=%s passed=%s failed=%s skipped=%s",
        run.run_id, len(runner_results), passed, failed, skipped,
    )

    return {
        "run": schemas.TestRunRead.model_validate(run),
        "total": len(runner_results),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "results": [schemas.TestRunResultRead.model_validate(r) for r in created_results],
    }


def discover_automation_tests_flow(path: str) -> list[dict]:
    return discover_automation_tests(path)


def list_test_runs_flow(
    application_id: str | None, module_id: str | None, status: str | None, page: int, page_size: int, db: Session
) -> dict:
    page, page_size = _paginate(page, page_size)
    filters = []
    if application_id:
        filters.append(TestRun.application_id == application_id)
    if module_id:
        filters.append(TestRun.module_id == module_id)
    if status:
        filters.append(TestRun.status == status)

    stmt = select(TestRun).where(*filters)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(TestRun.started_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return _paginated(items, total, page, page_size, schemas.TestRunRead)


def get_test_run_flow(run_id: str, db: Session) -> TestRun:
    obj = db.get(TestRun, run_id)
    if not obj:
        raise HTTPException(404, f"Test run {run_id} not found")
    return obj


def cancel_test_run_flow(run_id: str, db: Session) -> TestRun:
    obj = get_test_run_flow(run_id, db)
    runner_service.cancel_execution(run_id)
    obj.status = "CANCELLED"
    obj.completed_at = datetime.utcnow()
    db.flush()
    db.refresh(obj)
    return obj


# ═══════════════════════════════════════════════════════════════════════
# Test Run Results
# ═══════════════════════════════════════════════════════════════════════
def create_test_run_result_flow(payload: schemas.TestRunResultCreate, db: Session) -> TestRunResult:
    obj = TestRunResult(**payload.model_dump())
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_test_run_results_flow(
    run_id: str | None, testcase_id: str | None, status: str | None, page: int, page_size: int, db: Session
) -> dict:
    page, page_size = _paginate(page, page_size)
    filters = []
    if run_id:
        filters.append(TestRunResult.run_id == run_id)
    if testcase_id:
        filters.append(TestRunResult.testcase_id == testcase_id)
    if status:
        filters.append(TestRunResult.status == status)

    stmt = select(TestRunResult).where(*filters)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(TestRunResult.started_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return _paginated(items, total, page, page_size, schemas.TestRunResultRead)


def get_test_run_result_flow(execution_id: str, db: Session) -> TestRunResult:
    obj = db.get(TestRunResult, execution_id)
    if not obj:
        raise HTTPException(404, f"Execution result {execution_id} not found")
    return obj


def update_test_run_result_flow(execution_id: str, payload: schemas.TestRunResultUpdate, db: Session) -> TestRunResult:
    obj = get_test_run_result_flow(execution_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.flush()
    db.refresh(obj)
    return obj


def delete_test_run_result_flow(execution_id: str, db: Session) -> None:
    obj = get_test_run_result_flow(execution_id, db)
    db.delete(obj)
    db.flush()


# ═══════════════════════════════════════════════════════════════════════
# Execution Logs — append-only
# ═══════════════════════════════════════════════════════════════════════
def create_execution_logs_flow(payload: schemas.ExecutionLogBulkCreate, db: Session) -> list[ExecutionLog]:
    if not payload.logs:
        return []
    objs = [
        ExecutionLog(execution_id=payload.execution_id, log_level=entry.log_level, message=entry.message)
        for entry in payload.logs
    ]
    db.add_all(objs)
    db.flush()
    for obj in objs:
        db.refresh(obj)
    return objs


def list_execution_logs_flow(execution_id: str, db: Session) -> list[ExecutionLog]:
    return db.scalars(
        select(ExecutionLog).where(ExecutionLog.execution_id == execution_id).order_by(ExecutionLog.created_at.asc())
    ).all()


# ═══════════════════════════════════════════════════════════════════════
# Attachments
# ═══════════════════════════════════════════════════════════════════════
def create_attachment_flow(payload: schemas.AttachmentCreate, db: Session) -> Attachment:
    obj = Attachment(**payload.model_dump())
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_attachments_flow(execution_id: str | None, page: int, page_size: int, db: Session) -> dict:
    page, page_size = _paginate(page, page_size)
    filters = []
    if execution_id:
        filters.append(Attachment.execution_id == execution_id)

    stmt = select(Attachment).where(*filters)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(Attachment.uploaded_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return _paginated(items, total, page, page_size, schemas.AttachmentRead)


def get_attachment_flow(attachment_id: str, db: Session) -> Attachment:
    obj = db.get(Attachment, attachment_id)
    if not obj:
        raise HTTPException(404, f"Attachment {attachment_id} not found")
    return obj


def update_attachment_flow(attachment_id: str, payload: schemas.AttachmentUpdate, db: Session) -> Attachment:
    obj = get_attachment_flow(attachment_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.flush()
    db.refresh(obj)
    return obj


def delete_attachment_flow(attachment_id: str, db: Session) -> None:
    obj = get_attachment_flow(attachment_id, db)
    db.delete(obj)
    db.flush()


# ═══════════════════════════════════════════════════════════════════════
# Bugs
# ═══════════════════════════════════════════════════════════════════════
def create_bug_flow(payload: schemas.BugCreate, db: Session) -> Bug:
    obj = Bug(**payload.model_dump())
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_bugs_flow(
    testcase_id: str | None,
    execution_id: str | None,
    status: str | None,
    severity: str | None,
    page: int,
    page_size: int,
    db: Session,
) -> dict:
    page, page_size = _paginate(page, page_size)
    filters = []
    if testcase_id:
        filters.append(Bug.testcase_id == testcase_id)
    if execution_id:
        filters.append(Bug.execution_id == execution_id)
    if status:
        filters.append(Bug.status == status)
    if severity:
        filters.append(Bug.severity == severity)

    stmt = select(Bug).where(*filters)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(Bug.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return _paginated(items, total, page, page_size, schemas.BugRead)


def get_bug_flow(bug_id: str, db: Session) -> Bug:
    obj = db.get(Bug, bug_id)
    if not obj:
        raise HTTPException(404, f"Bug {bug_id} not found")
    return obj


# ═══════════════════════════════════════════════════════════════════════
# Dashboard
# ═══════════════════════════════════════════════════════════════════════
def dashboard_summary_flow(db: Session) -> dict:
    total_testcases = db.scalar(select(func.count()).select_from(TestCase)) or 0
    smoke_count = db.scalar(
        select(func.count()).select_from(TestCase).where(func.json_contains(TestCase.test_types, json.dumps("Smoke")))
    ) or 0
    regression_count = db.scalar(
        select(func.count()).select_from(TestCase).where(func.json_contains(TestCase.test_types, json.dumps("Regression")))
    ) or 0

    total_results = db.scalar(select(func.count()).select_from(TestRunResult)) or 0
    passed_results = db.scalar(select(func.count()).select_from(TestRunResult).where(TestRunResult.status == "PASSED")) or 0
    failed_results = db.scalar(select(func.count()).select_from(TestRunResult).where(TestRunResult.status == "FAILED")) or 0

    pass_percentage = round((passed_results / total_results) * 100, 2) if total_results else 0.0
    fail_percentage = round((failed_results / total_results) * 100, 2) if total_results else 0.0

    latest_runs = db.scalars(select(TestRun).order_by(TestRun.started_at.desc()).limit(5)).all()
    recent_failures = db.scalars(
        select(TestRunResult).where(TestRunResult.status == "FAILED").order_by(TestRunResult.completed_at.desc()).limit(5)
    ).all()

    return {
        "total_testcases": total_testcases,
        "smoke_count": smoke_count,
        "regression_count": regression_count,
        "pass_percentage": pass_percentage,
        "fail_percentage": fail_percentage,
        "latest_runs": [schemas.LatestRun.model_validate(r) for r in latest_runs],
        "recent_failures": [schemas.RecentFailure.model_validate(r) for r in recent_failures],
    }


def execution_history_flow(days: int, db: Session) -> list[dict]:
    since = datetime.utcnow() - timedelta(days=days)
    day_col = func.date(TestRunResult.completed_at)
    passed_expr = func.sum(case((TestRunResult.status == "PASSED", 1), else_=0))
    failed_expr = func.sum(case((TestRunResult.status == "FAILED", 1), else_=0))

    rows = db.execute(
        select(day_col.label("day"), passed_expr.label("passed"), failed_expr.label("failed"), func.count().label("total"))
        .where(TestRunResult.completed_at.isnot(None), TestRunResult.completed_at >= since)
        .group_by(day_col)
        .order_by(day_col.asc())
    ).all()

    return [
        schemas.ExecutionHistoryPoint(date=row.day, passed=row.passed or 0, failed=row.failed or 0, total=row.total or 0)
        for row in rows
    ]
