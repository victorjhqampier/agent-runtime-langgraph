from fastapi import Request, HTTPException, status
from fastapi.security import SecurityScopes
from jose import jwt, jwk
from jose.exceptions import ExpiredSignatureError, JWTError
import requests
import os
from typing import Any, Dict, Optional
import logging
from dotenv import load_dotenv

load_dotenv()


class CognitoAuthorizer:
    def __init__(self):
        region = os.getenv("COGNITO_JWKS_REGION")
        pool_id = os.getenv("COGNITO_JWKS_POOL_ID")

        if not region or not pool_id:
            raise ValueError("Environment variables COGNITO_JWKS_REGION and COGNITO_JWKS_POOL_ID are required")

        self.jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"
        self.issuer = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"
        self.jwks: Optional[Dict] = None
        self.logger = logging.getLogger(__name__)

    def _get_jwks(self) -> Dict:
        if self.jwks is None:
            try:
                self.logger.warning(f"[WARNING] New HTTP request to {self.jwks_url}")
                response = requests.get(self.jwks_url, timeout=10)
                response.raise_for_status()
                self.jwks = response.json()
            except requests.RequestException as e:
                self.logger.error(f"Failed to fetch JWKS: {str(e)}")
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service is temporarily unavailable")
        return self.jwks

    def _get_signing_key(self, token_header: Dict) -> Any:
        jwks = self._get_jwks()
        kid = token_header.get("kid")
        if not kid:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing kid in header", headers={"WWW-Authenticate": "Bearer"})

        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return jwk.construct(key)

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: signing key not found")

    def __call__(self, security_scopes: SecurityScopes, request: Request) -> dict:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization token not provided", headers={"WWW-Authenticate": "Bearer"})

        try:
            # Extraer el token del header
            parts = auth_header.split()
            if len(parts) != 2:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format", headers={"WWW-Authenticate": "Bearer"})

            scheme, token = parts
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization scheme", headers={"WWW-Authenticate": "Bearer"})

            if not token.strip():
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization token not provided", headers={"WWW-Authenticate": "Bearer"})

            # Decodificar el header del token sin verificar
            token_header = jwt.get_unverified_header(token)

            # Obtener la llave de firma
            signing_key: Any = self._get_signing_key(token_header)

            # Decodificar y validar el token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=None,  # Se puede especificar el client_id si es necesario
                issuer=self.issuer,
                options={
                    "verify_aud": False,  # Desactivar verificación de audience
                    "verify_exp": True,  # Verificar expiración
                    "verify_iss": True,  # Verificar issuer
                },
            )

            # Verificar scopes
            token_scopes = set(payload.get("scope", "").split())
            required_scopes = set(security_scopes.scopes)
            missing_scopes = required_scopes - token_scopes

            if missing_scopes:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized")

            return {
                "sub": payload.get("sub"),
                "username": payload.get("username"),
                # "email": payload.get('email'),
                # "granted_scopes": list(token_scopes),
                # "token_use": payload.get('token_use'),
                # "auth_time": payload.get('auth_time'),
                "exp": payload.get("exp"),
            }

        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired", headers={"WWW-Authenticate": "Bearer"})
        except JWTError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}", headers={"WWW-Authenticate": "Bearer"})
        except HTTPException:
            # Preserve expected auth/status responses raised in this flow.
            raise
        except Exception as e:
            self.logger.error(f"Error validating token: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error while validating token")
