from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from app.schemas.tag import TagCreate, TagOut, TagUpdate
from app.core.dependencies import get_db, get_current_user
from app.services.tag_service import TagService
from app.db.models import User as DBUser

router = APIRouter()

# Helper para HATEOAS (simplificado)
def add_tag_links(tag: TagOut) -> dict:
    links = {
        "self": {"href": f"/api/v1/tags/{tag.id}", "method": "GET"},
        "update": {"href": f"/api/v1/tags/{tag.id}", "method": "PUT"},
        "delete": {"href": f"/api/v1/tags/{tag.id}", "method": "DELETE"},
        # Opcional: links para listar projetos/dispositivos com esta tag
        # "projects_with_tag": {"href": f"/api/v1/projects/?tag_id={tag.id}", "method": "GET"},
        # "devices_with_tag": {"href": f"/api/v1/devices/?tag_id={tag.id}", "method": "GET"},
    }
    return tag.model_dump(by_alias=True, exclude_unset=True) | {"_links": links}


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_tag(tag_in: TagCreate, db: Session = Depends(get_db),
               current_user: DBUser = Depends(get_current_user)): # Tags podem ser criadas por qualquer usuário autenticado
    """
    Cria uma nova tag.
    """
    tag_service = TagService(db)
    tag = tag_service.create_tag(tag_in)
    return add_tag_links(TagOut.model_validate(tag))

@router.get("/", response_model=list[dict])
def read_tags(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
              current_user: DBUser = Depends(get_current_user),
              query: str | None = None):
    """
    Lista todas as tags ou pesquisa por nome.
    """
    tag_service = TagService(db)
    if query:
        tags = tag_service.search_tags(query, skip=skip, limit=limit)
    else:
        tags = tag_service.get_all_tags(skip=skip, limit=limit)
    
    return [add_tag_links(TagOut.model_validate(t)) for t in tags]

@router.get("/{tag_id}", response_model=dict)
def read_tag(tag_id: uuid.UUID, db: Session = Depends(get_db),
             current_user: DBUser = Depends(get_current_user)):
    """
    Obtém detalhes de uma tag específica por ID.
    """
    tag_service = TagService(db)
    tag = tag_service.get_tag(tag_id)
    return add_tag_links(TagOut.model_validate(tag))

@router.put("/{tag_id}", response_model=dict)
def update_tag(tag_id: uuid.UUID, tag_in: TagUpdate, db: Session = Depends(get_db),
               current_user: DBUser = Depends(get_current_user)):
    """
    Atualiza uma tag existente.
    """
    tag_service = TagService(db)
    updated_tag = tag_service.update_tag(tag_id, tag_in)
    return add_tag_links(TagOut.model_validate(updated_tag))

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: uuid.UUID, db: Session = Depends(get_db),
               current_user: DBUser = Depends(get_current_user)):
    """
    Exclui uma tag.
    """
    tag_service = TagService(db)
    tag_service.delete_tag(tag_id)
    return {"message": "Tag deleted successfully"}