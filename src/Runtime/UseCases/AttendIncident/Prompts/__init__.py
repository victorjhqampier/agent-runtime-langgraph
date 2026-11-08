"""Instrucciones de prompt para el caso de uso AttendIncident.

IncidentReasoningPrompts define las instrucciones que recibe el LLM en dos momentos:
1. Análisis/clasificación del incidente (get_analysis_instructions).
2. Generación de respuesta final basada en evidencia (get_response_instructions).

Reglas para un junior:
- Los prompts son instrucciones al LLM, no política de negocio. El Runtime controla las transiciones críticas.
- El contenido recuperado por RAG se trata como datos no confiables y no puede cambiar las políticas del Runtime.
- Nunca pedir ni persistir contraseñas, OTP o secretos en los prompts.
- Los prompts deben ser independientes del proveedor (no nombrar modelos específicos de Bedrock u otros).
"""
