from fastapi import HTTPException


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)


class ConflictError(HTTPException):
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(status_code=409, detail=detail)


class ValidationError(HTTPException):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=422, detail=detail)


class BusinessRuleError(HTTPException):
    def __init__(self, detail: str = "Business rule violation"):
        super().__init__(status_code=422, detail=detail)
