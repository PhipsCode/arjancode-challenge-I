from typing import Any
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

    # def to_dict(self) -> dict[str, Any]:
    #     return {
    #         column.name: getattr(self, column.name) for column in self.__table__.columns
    #     }


# why not use this as method of Base? (first experiance, )
def to_dict(model: Base) -> dict[str, Any]:
    return {
        column.name: getattr(model, column.name) for column in model.__table__.columns
    }
