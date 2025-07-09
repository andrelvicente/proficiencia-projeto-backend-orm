import uuid
from sqlalchemy.orm import Session
from app.db.models import Tag
from app.schemas.tag import TagCreate, TagUpdate
from app.repositories.tag import TagRepository
from fastapi import HTTPException, status

class TagService:
    def __init__(self, db: Session):
        self.tag_repo = TagRepository(db)

    def get_tag(self, tag_id: uuid.UUID) -> Tag:
        tag = self.tag_repo.get_by_id(tag_id)
        if not tag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
        return tag

    def get_all_tags(self, skip: int = 0, limit: int = 100) -> list[Tag]:
        return self.tag_repo.get_all(skip=skip, limit=limit)

    def search_tags(self, query: str, skip: int = 0, limit: int = 100) -> list[Tag]:
        return self.tag_repo.search_by_text(query, ['name'], skip=skip, limit=limit)

    def create_tag(self, tag_in: TagCreate) -> Tag:
        if self.tag_repo.get_by_name(tag_in.name):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tag with this name already exists")
        new_tag = self.tag_repo.create(tag_in.model_dump())
        return new_tag

    def update_tag(self, tag_id: uuid.UUID, tag_in: TagUpdate) -> Tag:
        tag = self.get_tag(tag_id)
        updated_tag = self.tag_repo.update(tag, tag_in.model_dump(exclude_unset=True))
        return updated_tag

    def delete_tag(self, tag_id: uuid.UUID):
        tag = self.get_tag(tag_id)
        self.tag_repo.delete(tag)
