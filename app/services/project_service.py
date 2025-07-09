import uuid
from sqlalchemy.orm import Session
from app.db.models import Project, Tag
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.repositories.project import ProjectRepository
from app.repositories.tag import TagRepository
from fastapi import HTTPException, status


class ProjectService:
    def __init__(self, db: Session):
        self.project_repo = ProjectRepository(db)
        self.tag_repo = TagRepository(db)

    def get_project(self, project_id: uuid.UUID) -> Project:
        project = self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    def get_all_projects(self, skip: int = 0, limit: int = 100) -> list[Project]:
        return self.project_repo.get_all(skip=skip, limit=limit)

    def get_projects_by_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[Project]:
        return self.project_repo.get_projects_by_user(user_id, skip=skip, limit=limit)

    def search_projects(self, query: str, skip: int = 0, limit: int = 100) -> list[Project]:
        return self.project_repo.search_by_text(query, ['name', 'description'], skip=skip, limit=limit)

    def create_project(self, project_in: ProjectCreate, current_user_id: uuid.UUID, tag_ids: list[uuid.UUID] = []) -> Project:
        project_data = project_in.model_dump()
        project_data["user_id"] = current_user_id

        new_project = self.project_repo.create(project_data)

        for tag_id in tag_ids:
            tag = self.tag_repo.get_by_id(tag_id)
            if not tag:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag with ID {tag_id} not found.")
            new_project.tags.append(tag)

        return new_project


    def update_project(self, project_id: uuid.UUID, project_in: ProjectUpdate, current_user_id: uuid.UUID) -> Project:
        project = self.get_project(project_id)
        if project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this project")

        with self.project_repo.db.begin_nested():
            updated_project = self.project_repo.update(project, project_in.model_dump(exclude_unset=True))
            return updated_project

    def delete_project(self, project_id: uuid.UUID, current_user_id: uuid.UUID):
        project = self.get_project(project_id)
        if project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this project")

        with self.project_repo.db.begin_nested():
            self.project_repo.delete(project)

    def add_tags_to_project(self, project_id: uuid.UUID, tag_ids: list[uuid.UUID], current_user_id: uuid.UUID) -> Project:
        project = self.get_project(project_id)
        if project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this project")

        for tag_id in tag_ids:
            tag = self.tag_repo.get_by_id(tag_id)
            if not tag:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag with ID {tag_id} not found.")
            if tag not in project.tags:
                project.tags.append(tag)
        updated_project = self.project_repo.update(project, {})
        return updated_project


    def remove_tags_from_project(self, project_id: uuid.UUID, tag_ids: list[uuid.UUID], current_user_id: uuid.UUID) -> Project:
        project = self.get_project(project_id)
        if project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this project")

        for tag_id in tag_ids:
            tag_to_remove = next((t for t in project.tags if t.id == tag_id), None)
            if tag_to_remove:
                project.tags.remove(tag_to_remove)

        updated_project = self.project_repo.update(project, {})
        return updated_project

