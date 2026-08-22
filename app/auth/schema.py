from marshmallow import Schema, ValidationError, fields, validate, validates_schema


class LoginSchema(Schema):
    email = fields.Email(required=True)

    password = fields.String(required=True)


login_schema = LoginSchema()


class RegisterSchema(Schema):

    first_name = fields.String(required=True)

    last_name = fields.String(required=True)

    email = fields.Email(required=True)

    password = fields.String(required=True, validate=validate.Length(min=8))

    phone = fields.String(
        required=False,
        allow_none=True,
    )


register_schema = RegisterSchema()


class UpdateMeSchema(Schema):
    first_name = fields.String(required=False)
    last_name = fields.String(required=False)
    phone = fields.String(
        required=False,
        allow_none=True,
    )

    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        if not data:
            raise ValidationError("At least one field must be provided.")


update_me_schema = UpdateMeSchema()
