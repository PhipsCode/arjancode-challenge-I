from typing import Any, Protocol, Sequence
from sqlalchemy.orm import Session
from .models import (
    SearchEntryEntity,
    SearchResultEntity,
    search_entry_result_association,
    to_dict,
)


class ResultsSpec(Protocol):
    name: str
    symbol: str
    asset_type: str
    currency: str

    def model_dump(self) -> dict[str, Any]: ...


def get_or_create_entry(db: Session, search_input: str) -> SearchEntryEntity:
    search_entry_entity = db.get(SearchEntryEntity, search_input)
    if search_entry_entity:
        return search_entry_entity
    search_entry = SearchEntryEntity(input=search_input)
    db.add(search_entry)
    db.flush()  # this generates the ID immediately
    return search_entry


def get_or_create_result(db: Session, result: ResultsSpec) -> SearchResultEntity:
    existing_result = (
        db.query(SearchResultEntity)
        .filter_by(
            symbol=result.symbol,
            asset_type=result.asset_type,
            currency=result.currency,
        )
        .first()
    )
    if existing_result:
        return existing_result
    search_result = SearchResultEntity(**result.model_dump())
    db.add(search_result)
    db.flush()
    return search_result


def link_entry_to_results(
    db: Session,
    search_entry: SearchEntryEntity,
    search_results: list[SearchResultEntity],
):
    for search_result in search_results:
        stmt = search_entry_result_association.insert().values(
            search_entry_id=search_entry.id, search_result_id=search_result.id
        )
        db.execute(stmt)


def save_search_results(db: Session, search_input: str, results: Sequence[ResultsSpec]):
    search_entry = get_or_create_entry(db, search_input)
    search_results = [get_or_create_result(db, result) for result in results]
    link_entry_to_results(db, search_entry, search_results)
    db.commit()


def get_search_inputs(db: Session) -> list[str]:
    return [str(entry.input) for entry in db.query(SearchEntryEntity).all()]


def get_search_results(db: Session, search_input: str) -> list[dict[str, Any]]:
    search_entry = db.query(SearchEntryEntity).filter_by(input=search_input).first()
    if not search_entry:
        return []
    return [to_dict(result) for result in search_entry.results]
