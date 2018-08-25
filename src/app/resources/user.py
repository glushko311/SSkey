from flask import make_response, request, session as sess
from flask_restplus import Resource
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from .. import app, api
from ..base import Session
from ..models import User, Password
from ..marshmallow_schemes import UserSchema, PasswordSchema, SearchSchema, SearchPasswordUrlSchema
from ..swagger_models import user_post, password_api_model, user_login, user_put, search_password, search_password_url

session = Session()


@api.representation('/json')
class UserResource(Resource):
    def get(self):
        """Get user's data."""
        current_user_email = sess.get('email', 'not set')
        try:
            user_data = User.filter_by_email(current_user_email, session)
        except SQLAlchemyError as err:
            return str(err), 500
        return UserSchema().dump(user_data), 200

    @api.expect(user_put)
    def put(self):
        """Update user's data."""
        current_user_email = sess.get('email', 'not set')
        args = request.get_json()
        try:
            current_user = User.filter_by_email(current_user_email, session)
            for arg_key in args.keys():
                if arg_key != 'password':
                    current_user.__setattr__(arg_key, args[arg_key])
            session.add(current_user)
            session.commit()
            return f'User {current_user.username} UPDATED', 200
        except SQLAlchemyError as err:
            return err, 500

    def delete(self):
        """Remove user with all his data."""
        current_user_email = sess.get('email', 'not set')
        try:
            current_user = User.filter_by_email(current_user_email, session)
            session.query(User).filter(User.email == current_user_email).delete()
            session.commit()
            return f'User {current_user.username} DELETED', 200
        except SQLAlchemyError as err:
            return str(err), 500


@api.representation('/json')
class UserPasswordsResource(Resource):
    def get(self):
        """
        Get list of user's passwords.

        User defines by sess email, returns a list of passwords for current logged in user.
        :return: list of passwords or 500 SQLAlchemyError
        """
        try:
            current_user_email = sess.get('email')
            current_user = User.filter_by_email(current_user_email, session)
            passwords = session.query(Password).filter(Password.user_id == current_user.id).all()
            passwords_serialized = []
            for password in passwords:
                passwords_serialized.append(password.serialize)
            return {'Your passwords': passwords_serialized}, 200  # OK
        except SQLAlchemyError as err:
            return str(err), 500  # Internal Server Error

    @api.expect(password_api_model)
    def post(self):
        """
        Create a new user's password.

        Create a new password for current logged in user, without specifying any parameters.
        :return: 200 OK or 500 SQLAlchemyError
        """
        json_data = request.get_json()
        if not json_data or not isinstance(json_data, dict):
            return 'No input data provided', 400  # Bad Request

        # Validate and deserialize input
        try:
            data = PasswordSchema().load(json_data)
        except ValidationError as err:
            return str(err), 422  # Unprocessable Entity

        current_user_email = sess.get('email', 'not set')
        current_user = User.filter_by_email(current_user_email, session)

        # create a new password
        try:
            session.add(Password(current_user.id, data))
            session.commit()
            return 'PASSWORD ADDED', 200  # OK
        except SQLAlchemyError as err:
            return str(err), 500  # Internal Server Error


@api.representation('/json')
class UserPasswordsSearchResource(Resource):
    @api.expect(search_password)
    def post(self):
        """
        Search for passwords by its description.

        Get json data, tries to find any matches in current logged in user list of passwords by its title and comment.
        :return: list with passwords that fit or 404 Error or 400 if no data provided or 422 ValidationError
        """
        json_data = request.get_json()
        if not json_data or not isinstance(json_data, dict):
            return 'No input data provided', 400  # Bad Request

        # Validate and deserialize input
        try:
            data = SearchSchema().load(json_data)
        except ValidationError as err:
            return str(err), 422  # Unprocessable Entity
        current_user_email = sess.get('email', 'not set')
        current_user = User.filter_by_email(current_user_email, session)
        all_passwords = session.query(Password).filter(Password.user_id == current_user.id).all()
        filtered_passwords = list()
        for password in all_passwords:
            if data.get("condition") in password.title or data.get("condition") in password.comment:
                filtered_passwords.append(password.serialize)

        if filtered_passwords:
            return filtered_passwords
        else:
            return 'No matches found', 404


@api.representation('/json')
class UserPasswordsSearchUrlResource(Resource):
    @api.expect(search_password_url)
    def post(self):
        """Get all user passwords for the particular site."""
        json_data = request.get_json()

        if not json_data or not isinstance(json_data, dict):
            return 'No input data provided', 400
        # Input data validation by Marshmallow schema
        try:
            data = SearchPasswordUrlSchema().load(json_data)
        except ValidationError as err:
            return str(err), 422

        current_user_email = sess.get('email', 'not set')

        try:
            current_user = User.filter_by_email(current_user_email, session)
            # Hard search without wildcard percent sign
            filtered_passwords = session.query(Password).filter(Password.user_id == current_user.id,
                                                                Password.url.like(f'{data.get("url")}'))
        except SQLAlchemyError as err:
            return str(err), 500

        passwords_by_url = []
        for password in filtered_passwords:
            passwords_by_url.append(password.serialize)
        if passwords_by_url:
            return passwords_by_url, 200
        else:
            return 'No matches found', 200


@api.representation('/json')
class UserPasswordsNumberResource(Resource):

    def get(self, pass_id):
        """
        Get particular password by pass_id.

        Get password from current logged in user by pass_id.
        :param pass_id: id of specific user's password
        :return: password or 500 SQLAlchemyError
        """
        try:
            current_user_email = sess.get('email', 'not set')
            current_user = User.filter_by_email(current_user_email, session)
            password = Password.find_pass(current_user.id, pass_id, session)
            if not password:
                return 'Password Not Found', 404  # Not Found
            return {'password': password.serialize}, 200  # OK
        except SQLAlchemyError as err:
            return str(err), 500  # Internal Server Error

    @api.expect(password_api_model)
    def put(self, pass_id):
        """
        Update password data.

        You can update all data of password or just a part of it.
        :param pass_id: id of password data you'd like to update of
        :return: 200 OK or 500 SQLAlchemyError
        """
        json_data = request.get_json()
        try:
            data = PasswordSchema().load(json_data)
        except ValidationError as err:
            return str(err), 422  # Unprocessable Entity
        try:
            if not Password.is_password_exists(pass_id):
                return 'Password Not Found', 404
            password = Password.filter_pass_by_id(pass_id, session)
            previous_pass = password.title

            for arg_key in data.keys():
                if arg_key != 'password':
                    password.__setattr__(arg_key, data[arg_key])
                else:
                    password.crypt_password(data[arg_key])
            session.add(password)
            session.commit()
            return f'Data for {previous_pass} has been updated successfully', 200
        except SQLAlchemyError as err:
            return str(err), 500

    def delete(self, pass_id):
        """
        Delete specific password.

        Delete password from current logged in user by pass_id.
        :param pass_id: id of specific user's password
        :return: 200 OK or 404 Password Not Found or 500 SQLAlchemyError
        """
        try:
            current_user_email = sess.get('email', 'not set')
            current_user = User.filter_by_email(current_user_email, session)
            password = Password.find_pass(current_user.id, pass_id, session)
            if password:
                session.query(Password) \
                    .filter(Password.user_id == current_user.id) \
                    .filter(Password.pass_id == pass_id) \
                    .delete()
                session.commit()
                return f'Password ID {pass_id} DELETED', 200  # OK
            else:
                return 'Password Not Found', 404  # Not Found
        except SQLAlchemyError as err:
            return str(err), 500  # Internal Server Error
