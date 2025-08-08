import pytest

from src.tasks_manager.tasks.cleanup import delete_expired_tokens


@pytest.fixture
def db_session_mock(mocker):
    db = mocker.MagicMock()
    mocker.patch(
        "src.tasks_manager.tasks.cleanup.PostgreSQLSessionLocal", return_value=db
    )
    return db


def test_delete_expired_tokens_success(db_session_mock):
    db_session_mock.query().filter().delete.side_effect = [2, 3]
    delete_expired_tokens()

    assert db_session_mock.commit.called
    assert db_session_mock.close.called

    db_session_mock.query.assert_any_call()
    db_session_mock.query().filter().delete.assert_called()
    db_session_mock.commit.assert_called_once()
    db_session_mock.rollback.assert_not_called()


def test_delete_expired_tokens_failure(db_session_mock):
    db_session_mock.query().filter().delete.side_effect = Exception("DB error")

    with pytest.raises(Exception, match="DB error"):
        delete_expired_tokens()

    assert db_session_mock.rollback.called
    assert db_session_mock.close.called
