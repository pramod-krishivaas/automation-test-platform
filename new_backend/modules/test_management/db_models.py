"""
test_management/db_models.py
──────────────────────────────
SQLAlchemy ORM models — one class per table, mirroring the MySQL DDL in
migrations/versions/0001_initial_schema.py 1:1.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CHAR, JSON, Boolean, ForeignKey, Integer, Numeric, String, Text, TIMESTAMP, text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Application(Base):
    __tablename__ = "applications"

    application_id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_name: Mapped[str] = mapped_column(String(150), nullable=False)
    platform: Mapped[str] = mapped_column(String(30), nullable=False)
    package_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )


class Module(Base):
    __tablename__ = "modules"

    module_id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("applications.application_id", ondelete="CASCADE"), nullable=False
    )
    module_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    status: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )


class Priority(Base):
    __tablename__ = "priorities"

    priority_id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    priority_name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str | None] = mapped_column(String(30), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))


class TestCase(Base):
    __tablename__ = "test_cases"

    testcase_id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    testcase_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    application_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("applications.application_id"), nullable=False)
    module_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("modules.module_id"), nullable=False)
    priority_id: Mapped[str | None] = mapped_column(CHAR(36), ForeignKey("priorities.priority_id"), nullable=True)
    # List[str], e.g. ["Smoke", "Regression"]. Always reassign the whole list on update
    # rather than mutating in place — SQLAlchemy won't detect in-place JSON mutation
    # without sqlalchemy.ext.mutable, and we don't need that overhead here.
    test_types: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    polarity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    automation_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("1"))
    status: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )


class TestRun(Base):
    __tablename__ = "test_runs"

    run_id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    application_id: Mapped[str | None] = mapped_column(CHAR(36), ForeignKey("applications.application_id"), nullable=True)
    module_id: Mapped[str | None] = mapped_column(CHAR(36), ForeignKey("modules.module_id"), nullable=True)
    test_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    environment: Mapped[str | None] = mapped_column(String(100), nullable=True)
    build_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    execution_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    triggered_by: Mapped[str | None] = mapped_column(String(150), nullable=True)
    status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

    results: Mapped[list["TestRunResult"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class TestRunResult(Base):
    __tablename__ = "test_run_results"

    execution_id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str | None] = mapped_column(CHAR(36), ForeignKey("test_runs.run_id", ondelete="CASCADE"), nullable=True)
    testcase_id: Mapped[str | None] = mapped_column(CHAR(36), ForeignKey("test_cases.testcase_id"), nullable=True)
    status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    execution_time: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    os_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(100), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    allure_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

    run: Mapped["TestRun"] = relationship(back_populates="results")


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    log_id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("test_run_results.execution_id", ondelete="CASCADE"), nullable=True
    )
    log_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    message: Mapped[str | None] = mapped_column(LONGTEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


class Attachment(Base):
    __tablename__ = "attachments"

    attachment_id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("test_run_results.execution_id", ondelete="CASCADE"), nullable=True
    )
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


class Bug(Base):
    __tablename__ = "bugs"

    bug_id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str | None] = mapped_column(CHAR(36), ForeignKey("test_run_results.execution_id"), nullable=True)
    testcase_id: Mapped[str | None] = mapped_column(CHAR(36), ForeignKey("test_cases.testcase_id"), nullable=True)
    bug_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    jira_ticket: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
