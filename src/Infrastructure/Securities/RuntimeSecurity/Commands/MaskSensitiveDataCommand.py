import re

from Infrastructure.Securities.RuntimeSecurity.SecuritySettings import SecuritySettings


class MaskSensitiveDataCommand:
    _SECRET_PATTERNS = (
        re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key|authorization)\s*[:=]\s*[^\s,;]+"),
        re.compile(r"(?i)bearer\s+[a-z0-9._~+/-]+=*"),
    )

    def __init__(self, settings: SecuritySettings | None = None) -> None:
        self._settings = settings or SecuritySettings()

    def mask_text(self, value: str) -> str:
        if not self._settings.pii_redaction_enabled:
            return value
        masked = value
        for pattern in self._SECRET_PATTERNS:
            masked = pattern.sub(self._settings.sensitive_value_mask, masked)
        return masked

    def mask_payload(self, payload: object) -> object:
        if isinstance(payload, str):
            return self.mask_text(payload)
        if isinstance(payload, dict):
            return {key: self.mask_payload(value) for key, value in payload.items()}
        if isinstance(payload, list):
            return [self.mask_payload(value) for value in payload]
        return payload
