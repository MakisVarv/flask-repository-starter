PERMISSIONS: list[dict[str, str]] = [
    # Users
    {"name": "user.read", "description": "Read user information"},
    {"name": "user.create", "description": "Create users"},
    {"name": "user.update", "description": "Update users"},
    {"name": "user.delete", "description": "Delete users"},
    {"name": "user.change_role", "description": "Change a user's role"},
    # Roles
    {"name": "role.read", "description": "Read roles"},
    {"name": "role.create", "description": "Create roles"},
    {"name": "role.update", "description": "Update roles"},
    {"name": "role.delete", "description": "Delete roles"},
    {
        "name": "role.assign_permission",
        "description": "Assign or remove permissions from roles",
    },
    # Permissions
    {"name": "permission.read", "description": "Read permissions"},
    # Dashboard
    {"name": "dashboard.read", "description": "View dashboard"},
]
