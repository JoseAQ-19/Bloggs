import pytest
from llm_router import LLMRouter
import os
from unittest.mock import patch, Mock

class FakeResponse:
    def __init__(self, content):
        self.choices = [Mock()]
        self.choices[0].message.content = content

class FakeClientParams:
    def __init__(self):
        self.chat = Mock()
        self.chat.completions.create = Mock()

def test_omniroute_success():
    """
    Test para validar que call_omniroute funciona llamando al cliente OpenAI apuntando al gateway OmniRoute.
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
    Test para validar que si OmniRoute falla (ej. servicio offline), route_call escala limpiamente al fallback_func sin lanzar excepción.
    """
    mock_omni_error = Exception("Connection Refused to http://localhost:8000/v1")
    
    def mock_fallback(prompt, system_prompt):
        return "Respuesta desde el proveedor fallback secundario. " * 10

    with patch("llm_router.LLMRouter.call_omniroute", return_value=None):
        result = LLMRouter.route_call("test prompt", "system prompt", fallback_func=mock_fallback)

    assert result is not None
    assert "fallback secundario" in result
