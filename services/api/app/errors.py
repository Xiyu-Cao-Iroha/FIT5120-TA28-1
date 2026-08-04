class ApiError(Exception):
    """Base for the API error contract (requirements section 9.4)."""

    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class InvalidLocationError(ApiError):
    def __init__(self, message: str = "Invalid coordinates, or origin and destination are identical."):
        super().__init__(400, "INVALID_LOCATION", message)


class OutsideServiceAreaError(ApiError):
    def __init__(self, message: str = "Destination is outside the configured Melbourne CBD service area."):
        super().__init__(422, "OUTSIDE_SERVICE_AREA", message)


class NoRouteFoundError(ApiError):
    def __init__(self, message: str = "No candidate walking route is available for this origin and destination."):
        super().__init__(404, "NO_ROUTE_FOUND", message)


class RateLimitedError(ApiError):
    def __init__(self, message: str = "Request limit exceeded. Please retry shortly."):
        super().__init__(429, "RATE_LIMITED", message)


class DataSourceUnavailableError(ApiError):
    def __init__(self, message: str = "No sufficiently fresh open-data snapshot is available."):
        super().__init__(503, "DATA_SOURCE_UNAVAILABLE", message)
