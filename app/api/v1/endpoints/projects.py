from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.schemas.tag import TagOut # Para retorno de tags
from app.core.dependencies import get_db, get_current_user
from app.services.project_service import ProjectService
from app.db.models import User as DBUser

router = APIRouter()

# Helper para HATEOAS (simplificado)
def add_project_links(project: ProjectOut) -> dict:
    links = {
        "self": {"href": f"/api/v1/projects/{project.id}", "method": "GET"},
        "update": {"href": f"/api/v1/projects/{project.id}", "method": "PUT"},
        "delete": {"href": f"/api/v1/projects/{project.id}", "method": "DELETE"},
        "devices": {"href": f"/api/v1/projects/{project.id}/devices", "method": "GET"},
        "tags": {"href": f"/api/v1/projects/{project.id}/tags", "method": "GET"},
        "add_tags": {"href": f"/api/v1/projects/{project.id}/tags", "method": "POST"},
    }
    return project.model_dump(by_alias=True, exclude_unset=True) | {"_links": links}


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_project(project_in: ProjectCreate, 
                   tag_ids: list[uuid.UUID] = Query([]), # Para associar tags na criação
                   db: Session = Depends(get_db),
                   current_user: DBUser = Depends(get_current_user)):
    """
    Cria um novo projeto para o usuário autenticado.
    Permite associar tags existentes no momento da criação.
    """
    project_service = ProjectService(db)
    project = project_service.create_project(project_in, current_user.id, tag_ids=tag_ids)
    return add_project_links(ProjectOut.model_validate(project))

@router.get("/", response_model=list[dict])
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                  current_user: DBUser = Depends(get_current_user),
                  query: str | None = None):
    """
    Lista todos os projetos do usuário autenticado ou pesquisa por texto.
    """
    project_service = ProjectService(db)
    if query:
        projects = project_service.search_projects(query, skip=skip, limit=limit)
    else:
        projects = project_service.get_projects_by_user(current_user.id, skip=skip, limit=limit)
    
    return [add_project_links(ProjectOut.model_validate(p)) for p in projects]

@router.get("/{project_id}", response_model=dict)
def read_project(project_id: uuid.UUID, db: Session = Depends(get_db),
                 current_user: DBUser = Depends(get_current_user)):
    """
    Obtém detalhes de um projeto específico por ID.
    O usuário deve ser o proprietário do projeto.
    """
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this project")
    return add_project_links(ProjectOut.model_validate(project))

@router.put("/{project_id}", response_model=dict)
def update_project(project_id: uuid.UUID, project_in: ProjectUpdate, db: Session = Depends(get_db),
                   current_user: DBUser = Depends(get_current_user)):
    """
    Atualiza um projeto existente.
    O usuário deve ser o proprietário do projeto.
    """
    project_service = ProjectService(db)
    updated_project = project_service.update_project(project_id, project_in, current_user.id)
    return add_project_links(ProjectOut.model_validate(updated_project))

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: uuid.UUID, db: Session = Depends(get_db),
                   current_user: DBUser = Depends(get_current_user)):
    """
    Exclui um projeto.
    O usuário deve ser o proprietário do projeto.
    """
    project_service = ProjectService(db)
    project_service.delete_project(project_id, current_user.id)
    return {"message": "Project deleted successfully"}


# Endpoints para gerenciamento de Tags em Projetos (Many-to-Many)
@router.post("/{project_id}/tags", response_model=dict)
def add_tags_to_project(project_id: uuid.UUID, tag_ids: list[uuid.UUID], db: Session = Depends(get_db),
                        current_user: DBUser = Depends(get_current_user)):
    """
    Adiciona tags a um projeto existente.
    """
    project_service = ProjectService(db)
    project = project_service.add_tags_to_project(project_id, tag_ids, current_user.id)
    return add_project_links(ProjectOut.model_validate(project))

@router.delete("/{project_id}/tags", response_model=dict)
def remove_tags_from_project(project_id: uuid.UUID, tag_ids: list[uuid.UUID], db: Session = Depends(get_db),
                             current_user: DBUser = Depends(get_current_user)):
    """
    Remove tags de um projeto existente.
    """
    project_service = ProjectService(db)
    project = project_service.remove_tags_from_project(project_id, tag_ids, current_user.id)
    return add_project_links(ProjectOut.model_validate(project))

@router.get("/{project_id}/tags", response_model=list[TagOut])
def get_project_tags(project_id: uuid.UUID, db: Session = Depends(get_db),
                     current_user: DBUser = Depends(get_current_user)):
    """
    Lista as tags associadas a um projeto.
    """
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this project's tags")
    return project.tags