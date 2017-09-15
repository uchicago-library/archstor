class Error(Exception):
    err_name = "Error"
    status_code = 500
    message = ""

    def __init__(self, message=None):
        if message is not None:
            self.message = message

    def to_dict(self):
        return {"message": self.message,
                "error_name": self.err_name}


class UserError(Error):
    error_name = "UserError"
    status_code = 400


class ServerError(Error):
    error_name = "ServerError"
    status_code = 500


class NotFoundError(Error):
    error_name = "NotFoundError"
    status_code = 404


class ObjectNotFoundError(NotFoundError):
    error_name = "ObjectNotFoundError"


class ObjectAlreadyExistsError(UserError):
    error_name = "ObjectAlreadyExistsError"


class FunctionalityOmittedError(Error):
    error_name = "FunctionalityOmittedError"
    status_code = 501
