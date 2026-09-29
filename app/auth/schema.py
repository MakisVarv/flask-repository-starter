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


class ChangePasswordSchema(Schema):
    new_password = fields.String(required=True, validate=validate.Length(min=8))


change_password_schema = ChangePasswordSchema()


class ChangeEmailSchema(Schema):
    current_password = fields.String(required=True)
    new_email = fields.Email(required=True)


change_email_schema = ChangeEmailSchema()


class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True)


forgot_password_schema = ForgotPasswordSchema()


class ResetPasswordSchema(Schema):
    token = fields.String(required=True)
    new_password = fields.String(
        required=True,
        validate=validate.Length(min=8),
    )


reset_password_schema = ResetPasswordSchema()


class ReauthenticateSchema(Schema):
    current_password = fields.String(required=True)


reauthenticate_schema = ReauthenticateSchema()
