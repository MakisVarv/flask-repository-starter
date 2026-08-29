from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from app.roles.schema import RoleSchema


class UserSchema(Schema):
    """User response schema."""

    id = fields.UUID()

    first_name = fields.String()

    last_name = fields.String()

    email = fields.Email()

    phone = fields.String(allow_none=True)

    is_active = fields.Boolean()

    role = fields.Nested(RoleSchema)


user_schema = UserSchema()

users_schema = UserSchema(many=True)


class CreateUserSchema(Schema):
    """Schema used to create a user."""

    first_name = fields.String(required=True)

    last_name = fields.String(required=True)

    email = fields.Email(required=True)

    password = fields.String(
        required=True,
        validate=validate.Length(min=8),
    )

    phone = fields.String(
        required=False,
        allow_none=True,
    )

    role_id = fields.UUID(required=True)


create_user_schema = CreateUserSchema()


class UpdateUserSchema(Schema):

    first_name = fields.String()
    last_name = fields.String()
    email = fields.Email()

    phone = fields.String(
        allow_none=True,
    )

    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        if not data:
            raise ValidationError("At least one field must be provided.")


class AssignRoleSchema(Schema):

    role_id = fields.UUID(required=True)


assign_role_schema = AssignRoleSchema()
update_user_schema = UpdateUserSchema()


class UserQuerySchema(Schema):
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1),
    )

    page_size = fields.Integer(
        load_default=10,
        validate=validate.Range(min=1, max=100),
    )
    search = fields.String(load_default=None)
    sort = fields.String(load_default="id")
    role = fields.String(load_default=None)
    is_active = fields.Boolean(load_default=None)

    @validates_schema
    def validate_sort(self, data, **kwargs):
        sort = data["sort"]
        field_name = sort.removeprefix("-")

        allowed_fields = {
            "id",
            "first_name",
            "last_name",
            "email",
            "role",
            "is_active",
        }

        if field_name not in allowed_fields:
            raise ValidationError({"sort": [f"Invalid sort field: {field_name}"]})


user_query_schema = UserQuerySchema()
