from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.sql.annotation import Annotated

intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]


class Base(DeclarativeBase):
    type_annotation_map = {
        intpk: mapped_column(primary_key=True, autoincrement=True),
    }
