from fastapi import Request, Security, HTTPException, status
from fastapi.security import SecurityScopes


class ArifyAuthorizer:
    def __init__(self):
        self.header_name = "axscope"

    def __call__(self, security_scopes: SecurityScopes, request: Request) -> dict:
        """
        - Recibe los scopes requeridos en el endpoint (security_scopes.scopes).
        - Lee el header self.header_name del request.
        - Verifica si el header está presente y contiene todos los scopes solicitados.
        - Lanza 401 si no hay header, 403 si faltan scopes.
        - Retorna un dict con la lista de scopes hallados (o lo que necesites).
        """
        scopes_header = request.headers.get(self.header_name)
        if not scopes_header:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Falta el header '{self.header_name}'", headers={"WWW-Authenticate": "Bearer"})

        # Ejemplo: "read:messages write:messages read:reports"
        granted_scopes = set(scopes_header.split())

        required_scopes = set(security_scopes.scopes)
        missing = required_scopes - granted_scopes
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Faltan scopes requeridos para '{self.header_name}'")

        return {"granted_scopes": list(granted_scopes)}


# How to use
# @app.get("/messages")
# def read_messages(
#     # Este endpoint exige el scope "read:messages"
#     header_info: dict = Security(
#         arify_authorizer,
#         scopes=[Scopes.READ_MESSAGES]
#     )
# ):
