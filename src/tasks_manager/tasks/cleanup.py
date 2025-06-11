from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.database import ActivationTokenModel, RefreshTokenModel
from src.database.session import PostgreSQLSessionLocal
from src.tasks_manager.celery_app import celery_app


@celery_app.task(name="src.tasks_manager.tasks.cleanup.delete_expired_tokens")
def delete_expired_tokens():
    db: Session = PostgreSQLSessionLocal()
    now = datetime.now(timezone.utc)

    try:
        deleted_activation = (
            db.query(ActivationTokenModel)
            .filter(ActivationTokenModel.expires_at < now)
            .delete(synchronize_session=False)
        )

        deleted_refresh = (
            db.query(RefreshTokenModel)
            .filter(RefreshTokenModel.expires_at < now)
            .delete(synchronize_session=False)
        )

        db.commit()
        print(
            f"Deleted: {deleted_activation} activation tokens, {deleted_refresh} refresh tokens"
        )
    finally:
        db.close()
