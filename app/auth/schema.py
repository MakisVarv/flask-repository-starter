from marshmallow import Schema, fields, validate


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
