from app.associations import role_permissions
from app.roles.model import Role
from app.roles.repository import RoleRepository
from app.roles.routes import role_bp
from app.roles.schema import RoleSchema
from app.roles.service import RoleService

__all__ = [
    "Role",
    "RoleService",
    "RoleSchema",
    "role_bp",
    "role_permissions",
    "RoleRepository",
]
