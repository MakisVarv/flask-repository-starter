from marshmallow import Schema, ValidationError, fields, validate, validates_schema


class PermissionSchema(Schema):
    """Permission response schema."""

    id = fields.UUID()

    name = fields.String()

    description = fields.String(allow_none=True)


class CreatePermissionSchema(Schema):

    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50),
    )

    description = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(min=1, max=255),
    )


class UpdatePermissionSchema(Schema):
    name = fields.String(
        required=False,
        validate=validate.Length(min=1, max=50),
    )

    description = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(min=1, max=255),
    )

    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        if "name" not in data and "description" not in data:
            raise ValidationError("At least one field must be provided.")


permission_schema = PermissionSchema()

permissions_schema = PermissionSchema(many=True)

create_permission_schema = CreatePermissionSchema()

update_permission_schema = UpdatePermissionSchema()
