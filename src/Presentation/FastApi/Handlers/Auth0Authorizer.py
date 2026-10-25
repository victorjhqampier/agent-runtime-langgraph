import os
import requests
from typing import Dict, List
from fastapi import HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt, JWTError
from jose.utils import base64url_decode


class Auth0Authorizer:
    def __init__(self):
        self.jwks_url = os.getenv("JWKS_URL")  # p.ej. "https://<tu-tenant>/well-known/jwks.json"
        self.issuer = os.getenv("ISSUER")  # p.ej. "https://<tu-tenant>/"
        self.audience = os.getenv("AUDIENCE")  # p.ej. "https://mi-api"

        alg_str = os.getenv("ALGORITHMS", "RS256")
        self.algorithms = [algo.strip() for algo in alg_str.split(",")]

        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl=os.getenv("TOKEN_URL", "token"), scopes={})

        # Para no pedir la JWKS en cada request, podemos cachearla en memoria.
        self._cached_jwks = None

    # Obtiene las claves públicas (JWKS) desde self.jwks_url
    def _fetch_jwks(self) -> Dict:
        if not self._cached_jwks:
            if not self.jwks_url:
                raise RuntimeError("JWKS_URL no está configurada.")
            resp = requests.get(self.jwks_url)
            resp.raise_for_status()
            self._cached_jwks = resp.json()  # { "keys": [ ... ] }
        return self._cached_jwks

    # Toma el JWT y extrae su 'kid' del header
    def _get_rsa_key(self, token: str) -> Dict:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No se pudo obtener el 'kid' del token", headers={"WWW-Authenticate": "Bearer"})

        jwks = self._fetch_jwks()
        for key in jwks["keys"]:
            if key["kid"] == kid:
                return {"kty": key["kty"], "kid": key["kid"], "use": key["use"], "n": key["n"], "e": key["e"]}

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"No se encontró una JWK que coincida con kid={kid}", headers={"WWW-Authenticate": "Bearer"})

    def __call__(self, security_scopes: SecurityScopes, request: Request) -> Dict:
        """
        Esta función mágica hace que la clase sea "llamable" como dependencia.
        - Se inyecta 'security_scopes': los scopes que el endpoint requiere.
        - Se inyecta 'token' a través de Security(self.oauth2_scheme).
        - Valida el token, firma, issuer, audience, scopes.
        - Retorna el payload si es válido.
        - Lanza HTTPException(401 o 403) en caso de error.
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization token not provided", headers={"WWW-Authenticate": "Bearer"})

        parts = auth_header.split()
        if len(parts) != 2:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format", headers={"WWW-Authenticate": "Bearer"})

        scheme, token = parts
        if scheme.lower() != "bearer" or not token.strip():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization token", headers={"WWW-Authenticate": "Bearer"})

        # 1) Obtener la clave pública que corresponde al kid del token
        rsa_key = self._get_rsa_key(token)

        # 2) Intentar decodificar y validar firmas y claims
        try:
            payload = jwt.decode(
                token,
                rsa_key,  # Clave pública
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=self.issuer,
            )
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o firma incorrecta", headers={"WWW-Authenticate": "Bearer"})

        # 3) Validar scopes (si el endpoint los solicita)
        #    En Auth0, normalmente vienen en "permissions".
        required = security_scopes.scopes
        token_scopes = payload.get("permissions", [])

        # Si el endpoint declaró scopes en Security(..., scopes=["X", "Y", ...])
        # verificamos que todos estén presentes:
        missing = [scope for scope in required if scope not in token_scopes]
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Faltan scopes requeridos: {missing}", headers={"WWW-Authenticate": "Bearer"})

        # 4) Si todo es correcto, devolvemos el payload
        return payload


# ------- example how to Use
# @app.get("/messages")
# def read_messages(payload: dict = Security(authorizer, scopes=[Scopes.READ])):
