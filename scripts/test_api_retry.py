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
