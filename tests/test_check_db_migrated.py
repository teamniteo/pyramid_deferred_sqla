"""Test check_db_migrated function."""

from pyramid.config import Configurator
from pyramid_deferred_sqla import check_db_migrated
from unittest import mock

import base64
import pytest
import urllib


def test_SKIP_CHECK_DB_MIGRATED() -> None:
    """Support skipping the check with a config flag."""
    config = Configurator()
    config.registry.settings["SKIP_CHECK_DB_MIGRATED"] = "true"

    assert check_db_migrated(config) is None


@mock.patch("pyramid_deferred_sqla.alembic")
def test_skip_when_running_an_alembic_command(alembic: mock.MagicMock) -> None:
    """Pyramid env is bootstrapped when running alembic commands.

    We need to skip checking when this is the case, because then you cannot
    ever migrate the database.
    """
    alembic.context = mock.Mock(spec="config".split())
    config = Configurator()
    global_config = {}

    assert check_db_migrated(config) is None


@mock.patch("pyramid_deferred_sqla.alembic")
@mock.patch("pyramid_deferred_sqla.EnvironmentContext")
@mock.patch("pyramid_deferred_sqla.ScriptDirectory")
@mock.patch("pyramid_deferred_sqla.MigrationContext")
@mock.patch("pyramid_deferred_sqla.sys")
def test_database_outdated(
    sys: mock.MagicMock,
    MigrationContext: mock.MagicMock,
    ScriptDirectory: mock.MagicMock,
    EnvironmentContext: mock.MagicMock,
    alembic: mock.MagicMock,
) -> None:
    """Database is outdated when head version doesn't match current version.
    """
    alembic.context = None
    config = mock.Mock(spec="registry".split())
    config.registry.settings = {"sqlalchemy.engine": mock.Mock(spec="connect".split())}
    config.registry.settings[
        "sqlalchemy.engine"
    ].connect.return_value.__enter__ = mock.Mock(return_value=(mock.Mock(), None))
    config.registry.settings[
        "sqlalchemy.engine"
    ].connect.return_value.__exit__ = mock.Mock(return_value=None)

    EnvironmentContext.return_value.get_head_revision.return_value = "foo"
    MigrationContext.configure.return_value.get_current_revision.return_value = "bar"

    check_db_migrated(config)
    sys.exit.assert_called_with(
        "ERROR: The latest Alembic migration applied to the DB is bar, but I "
        "found a more recent migration on the filesystem: foo. Please upgrade "
        "your DB to Alembic 'head' or skip this check by setting SKIP_CHECK_DB_MIGRATED=1."
    )


@mock.patch("pyramid_deferred_sqla.alembic")
@mock.patch("pyramid_deferred_sqla.EnvironmentContext")
@mock.patch("pyramid_deferred_sqla.ScriptDirectory")
@mock.patch("pyramid_deferred_sqla.MigrationContext")
def test_database_up_to_date(
    MigrationContext: mock.MagicMock,
    ScriptDirectory: mock.MagicMock,
    EnvironmentContext: mock.MagicMock,
    alembic: mock.MagicMock,
) -> None:
    """Database is up-to-date when head version matches current version."""
    alembic.context = None
    config = mock.Mock(spec="registry".split())
    config.registry.settings = {"sqlalchemy.engine": mock.Mock(spec="connect".split())}
    config.registry.settings[
        "sqlalchemy.engine"
    ].connect.return_value.__enter__ = mock.Mock(return_value=(mock.Mock(), None))
    config.registry.settings[
        "sqlalchemy.engine"
    ].connect.return_value.__exit__ = mock.Mock(return_value=None)

    EnvironmentContext.return_value.get_head_revision.return_value = "foo"
    MigrationContext.configure.return_value.get_current_revision.return_value = "foo"

    assert check_db_migrated(config) is None
