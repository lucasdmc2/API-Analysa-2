"""
Custom exception classes following RFC 7807 Problem Details
"""

from typing import Optional


class APIException(Exception):
    """Base API exception following RFC 7807"""
    
    def __init__(
        self,
        error_type: str,
        title: str,
        detail: str,
        status_code: int = 500,
        instance: Optional[str] = None,
    ):
        self.error_type = error_type
        self.title = title
        self.detail = detail
        self.status_code = status_code
        self.instance = instance
        super().__init__(detail)


# Validation Errors (400)
class ValidationError(APIException):
    def __init__(self, detail: str, error_type: str = "validation-error"):
        super().__init__(
            error_type=error_type,
            title="Dados de entrada inválidos",
            detail=detail,
            status_code=400,
        )


class InvalidFileFormatError(APIException):
    def __init__(self, detail: str = "Formato de arquivo não suportado"):
        super().__init__(
            error_type="invalid-file-format",
            title="Formato de arquivo não suportado",
            detail=detail,
            status_code=400,
        )


class FileTooLargeError(APIException):
    def __init__(self, detail: str = "Arquivo muito grande"):
        super().__init__(
            error_type="file-too-large",
            title="Arquivo muito grande",
            detail=detail,
            status_code=400,
        )


# Authentication Errors (401)
class TokenMissingError(APIException):
    def __init__(self):
        super().__init__(
            error_type="token-missing",
            title="Token de acesso ausente",
            detail="Header Authorization com Bearer token é obrigatório",
            status_code=401,
        )


class TokenInvalidError(APIException):
    def __init__(self, detail: str = "Token de acesso inválido"):
        super().__init__(
            error_type="token-invalid",
            title="Token de acesso inválido",
            detail=detail,
            status_code=401,
        )


class TokenExpiredError(APIException):
    def __init__(self, detail: str = "Token de acesso expirado"):
        super().__init__(
            error_type="token-expired",
            title="Token de acesso expirado",
            detail=detail,
            status_code=401,
        )


# Authorization Errors (403)
class InsufficientScopeError(APIException):
    def __init__(self, required_scope: str):
        super().__init__(
            error_type="insufficient-scope",
            title="Escopo insuficiente",
            detail=f"Operação requer escopo '{required_scope}'",
            status_code=403,
        )


class TenantAccessDeniedError(APIException):
    def __init__(self):
        super().__init__(
            error_type="tenant-access-denied",
            title="Acesso ao tenant negado",
            detail="Acesso aos dados deste tenant não é permitido",
            status_code=403,
        )


# Not Found Errors (404)
class ResourceNotFoundError(APIException):
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            error_type="resource-not-found",
            title="Recurso não encontrado",
            detail=f"{resource_type} com ID '{resource_id}' não foi encontrado",
            status_code=404,
        )


class PatientNotFoundError(APIException):
    def __init__(self, patient_id: str):
        super().__init__(
            error_type="patient-not-found",
            title="Paciente não encontrado",
            detail=f"Paciente com ID '{patient_id}' não foi encontrado",
            status_code=404,
        )


class ReportNotFoundError(APIException):
    def __init__(self, report_id: str):
        super().__init__(
            error_type="report-not-found",
            title="Laudo não encontrado",
            detail=f"Laudo com ID '{report_id}' não foi encontrado",
            status_code=404,
        )


# Conflict Errors (409)
class DuplicateResourceError(APIException):
    def __init__(self, resource_type: str, detail: str):
        super().__init__(
            error_type="duplicate-resource",
            title="Recurso duplicado",
            detail=detail,
            status_code=409,
        )


class ProcessingInProgressError(APIException):
    def __init__(self, document_id: str):
        super().__init__(
            error_type="processing-in-progress",
            title="Processamento em andamento",
            detail=f"Documento '{document_id}' já está sendo processado",
            status_code=409,
        )


# Rate Limiting (429)
class RateLimitExceededError(APIException):
    def __init__(self, detail: str = "Limite de requisições excedido"):
        super().__init__(
            error_type="rate-limit-exceeded",
            title="Limite de requisições excedido",
            detail=detail,
            status_code=429,
        )


# Processing Errors (422)
class OCRQualityLowError(APIException):
    def __init__(self, detail: str = "Qualidade OCR insuficiente"):
        super().__init__(
            error_type="ocr-quality-low",
            title="Qualidade OCR insuficiente",
            detail=detail,
            status_code=422,
        )


class NoTablesFoundError(APIException):
    def __init__(self):
        super().__init__(
            error_type="no-tables-found",
            title="Nenhuma tabela encontrada",
            detail="Não foi possível identificar tabelas de resultados no documento",
            status_code=422,
        )


class ExtractionConfidenceLowError(APIException):
    def __init__(self, confidence: float):
        super().__init__(
            error_type="extraction-confidence-low",
            title="Confiança da extração baixa",
            detail=f"Confiança da extração ({confidence:.2f}) abaixo do limiar mínimo",
            status_code=422,
        )


# Server Errors (500)
class ProcessingFailedError(APIException):
    def __init__(self, detail: str = "Falha no processamento"):
        super().__init__(
            error_type="processing-failed",
            title="Falha no processamento",
            detail=detail,
            status_code=500,
        )


class DeterminismFailureError(APIException):
    def __init__(self):
        super().__init__(
            error_type="determinism-failure",
            title="Falha no determinismo",
            detail="Outputs diferentes para o mesmo input - bug crítico detectado",
            status_code=500,
        )


# Service Unavailable (503)
class OCRServiceUnavailableError(APIException):
    def __init__(self):
        super().__init__(
            error_type="ocr-service-unavailable",
            title="Serviço OCR indisponível",
            detail="Serviço de OCR está temporariamente indisponível",
            status_code=503,
        )


class DatabaseUnavailableError(APIException):
    def __init__(self):
        super().__init__(
            error_type="database-unavailable",
            title="Banco de dados indisponível",
            detail="Banco de dados está temporariamente indisponível",
            status_code=503,
        )


# Timeout Errors (504)
class ProcessingTimeoutError(APIException):
    def __init__(self, timeout_seconds: int):
        super().__init__(
            error_type="processing-timeout",
            title="Timeout no processamento",
            detail=f"Processamento excedeu limite de {timeout_seconds} segundos",
            status_code=504,
        )