from views import api
from werkzeug.exceptions import NotFound,Conflict,Forbidden,Unauthorized,HTTPException,BadRequest
from sqlalchemy.exc import IntegrityError,StatementError

@api.errorhandler(BadRequest)
def handle_statement_error(error):
    """Error handler for BadRequest"""
    message = 'Bad Request: {}'.format(error)
    return {'message': message}, 400

@api.errorhandler(Unauthorized)
def handle_unauthorized(error):
    """Error handler for IntegrityError"""
    message = 'Unauthorized: {}'.format(error)
    return {'message': message}, 401

@api.errorhandler(Forbidden)
def handle_forbidden(error):
    """Error handler for IntegrityError"""
    message = 'Forbidden: {}'.format(error)
    return {'message': message}, 403

@api.errorhandler(NotFound)
def handle_not_found(error):
    """Error handler for NotFound"""
    message = 'Not Found: {}'.format(error)
    return {'message': message}, 404

@api.errorhandler(Conflict)
def handle_conflict(error):
    """Error handler for Conflict"""
    message = 'Conflict: {}'.format(error)
    return {'message': message}, 409

@api.errorhandler(KeyError)
def handle_key_error(error):
    """Error handler for KeyError"""
    message = 'A KeyError occurred: {}'.format(error)
    return {'message': message}, 422

@api.errorhandler(IntegrityError)
def handle_integrity_error(error):
    """Error handler for IntegrityError"""
    message = 'An IntegrityError occurred: {}'.format(error)
    return {'message': message}, 500

@api.errorhandler(StatementError)
def handle_statement_error(error):
    """Error handler for StatementError"""
    message = 'A StatementError occurred: {}'.format(error)
    return {'message': message}, 500

@api.errorhandler(TypeError)
def handle_type_error(error):
    """Error handler for TypeError"""
    message = 'A TypeError occurred: {}'.format(error)
    return {'message': message}, 500

@api.errorhandler
def default_error_handler(error):
    message = 'An unhandled exception occurred.'
    if isinstance(error, HTTPException):
        code = error.code
        message = error.description
    else:
        code = 500
        return {'Error' : error}, code
    return {'Error' : message}, code
