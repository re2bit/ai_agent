import logging

class EndpointFilter(logging.Filter):
    def __init__(self, excluded_endpoints: list[str]) -> None:
        self.excluded_endpoints = excluded_endpoints
    def filter(self, record: logging.LogRecord) -> bool:
        return record.args and len(record.args) >= 3 and record.args[2] not in self.excluded_endpoints

def apply_log_filter(exclude_endpoints: list[str] = []):
    logging.getLogger("uvicorn.access").addFilter(EndpointFilter(exclude_endpoints))