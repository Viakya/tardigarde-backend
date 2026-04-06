class AppError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ValidationError(AppError):
    status_code = 400


class AuthenticationError(AppError):
    status_code = 401


class ConflictError(AppError):
    status_code = 409
