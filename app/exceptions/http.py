from fastapi import HTTPException, status


class AppHTTPException(HTTPException):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(status_code=status_code, detail={"code": code, "message": message})


class NotFoundError(AppHTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, code="not_found", message=message)


class BadRequestError(AppHTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, code="bad_request", message=message)


class UnauthorizedError(AppHTTPException):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, code="unauthorized", message=message)
