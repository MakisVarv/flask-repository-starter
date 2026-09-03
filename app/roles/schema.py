from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from app.permissions.schema import PermissionSchema


class RoleSchema(Schema):
    """Role response schema."""

    id = fields.UUID()

    name = fields.String()

    description = fields.String(allow_none=True)

    level = fields.Integer()

    permissions = fields.Nested(
        PermissionSchema,
        many=True,
    )


class CreateRoleSchema(Schema):

    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50),
    )

    description = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(min=1, max=255),
    )

    level = fields.Integer(required=True, validate=validate.Range(min=1, max=100))


class UpdateRoleSchema(Schema):
    name = fields.String(
        required=False,
        validate=validate.Length(min=1, max=50),
    )

    description = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(min=1, max=255),
    )
    level = fields.Integer(required=False, validate=validate.Range(min=1, max=100))

    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        if "name" not in data and "description" not in data and "level" not in data:
            raise ValidationError("At least one field must be provided.")


class AddPermissionSchema(Schema):

    permission_id = fields.UUID(required=True)


add_permission_schema = AddPermissionSchema()

role_schema = RoleSchema()

roles_schema = RoleSchema(many=True)

create_role_schema = CreateRoleSchema()

update_role_schema = UpdateRoleSchema()
