import pytest
from llm_router import LLMRouter
import os
import json
from unittest.mock import patch, Mock

class FakeResponse:
    def __init__(self, content):
        self.choices = [Mock()]
        self.choices[0].message.content = content

class FakeClientParams:
    def __init__(self):
        self.chat = Mock()
        self.chat.completions.create = Mock()

def test_api_retry_success_after_failure():
    """
    Test para validar que el sistema de reintentos (Exponential Backoff) sobrevive a errores transitorios 
    de HTTP 429 como exige la Tarea 1.1 del PRD.
    """
    mock_client = FakeClientParams()

    # Simula lanzar una excepción (ej 429 Rate Limit) la primera vez, y devolver éxito la segunda
    rate_limit_error = Exception("HTTP 429 Rate Limit Exceeded")
    setattr(rate_limit_error, "status_code", 429)

    mock_client.chat.completions.create.side_effect = [
        rate_limit_error,
        FakeResponse(
            "Este es un texto de prueba lo suficientemente largo para pasar la validacion de reasoning que pide mas de 200 caracteres. "
            * 5
        ),
    ]

    with patch("llm_router.OpenAI", return_value=mock_client), patch.dict(
        os.environ,
        {"MODELS_TOKEN_CEU": "fake_token_largo_valido12345", "TOKEN_MODELS": ""},
    ):
        result = LLMRouter.call_capa_cero("test prompt", "system prompt", model_type="reasoning")

    # Debe recuperarse del primer error 429 y devolver contenido válido
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 400


def test_omniroute_success():
    """
    Test para validar que call_omniroute funciona como proveedor primario cuando responde con éxito.
    """
    mock_client = FakeClientParams()
    expected_text = "OmniRoute es un AI Gateway local eficiente y ultrarrápido para modelos de lenguaje. " * 6
    mock_client.chat.completions.create.return_value = FakeResponse(expected_text)

    with patch("llm_router.OpenAI", return_value=mock_client):
        result = LLMRouter.call_omniroute("test prompt", "system prompt", model_type="reasoning")

    assert result is not None
    assert "OmniRoute" in result


def test_omniroute_fallback_on_failure():
    """
    Test para validar que si OmniRoute falla (ej. servicio offline), route_call escala limpiamente al fallback sin lanzar excepción.
    """
    mock_omni_error = Exception("Connection Refused to http://localhost:8000/v1")
    
    def mock_fallback(prompt, system_prompt):
        return "Respuesta desde el proveedor fallback secundario. " * 10

    with patch("llm_router.LLMRouter.call_omniroute", side_effect=mock_omni_error), \
         patch("llm_router.LLMRouter.call_capa_cero", return_value=None):
        result = LLMRouter.route_call("test prompt", "system prompt", fallback_func=mock_fallback)

    assert result is not None
    assert "fallback secundario" in result

