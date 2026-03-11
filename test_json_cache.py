#!/usr/bin/env python3
"""
TEST_JSON_CACHE.PY — Test Suite para Caché Agresiva y JSON Estandarizado
=========================================================================
Verifica:
  1. Que la caché evita llamar a APIs externas dos veces por la misma consulta.
  2. Que los modelos devuelven JSON puro parseable (no texto libre).
  3. Que la función _call_nvidia_nim soporta force_json=True.

Ejecución: python test_json_cache.py
"""

import os
import sys
import json
import time
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Asegurar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# TEST 1: Módulo de Caché (api_cache.py)
# ============================================================

class TestAPICache(unittest.TestCase):
    """Tests para el sistema de caché agresiva."""

    def setUp(self):
        """Usar un archivo temporal de caché para cada test."""
        self.temp_cache = tempfile.NamedTemporaryFile(
            suffix='.json', delete=False, mode='w', dir=tempfile.gettempdir()
        )
        self.temp_cache.write('{}')
        self.temp_cache.close()
        
        # Monkey-patch el path de la caché
        import api_cache
        self._original_cache_file = api_cache.CACHE_FILE
        api_cache.CACHE_FILE = self.temp_cache.name

    def tearDown(self):
        """Restaurar el path original y limpiar."""
        import api_cache
        api_cache.CACHE_FILE = self._original_cache_file
        try:
            os.unlink(self.temp_cache.name)
        except OSError:
            pass

    def test_01_cache_miss_then_hit(self):
        """Primera llamada = MISS (ejecuta función). Segunda = HIT (devuelve caché)."""
        from api_cache import cached_api_call
        
        call_count = 0
        
        @cached_api_call(ttl_hours=12)
        def fake_exa_search(query, limit=5):
            nonlocal call_count
            call_count += 1
            return [{"title": f"Result for {query}", "source": "exa"}]
        
        # Primera llamada — MISS
        result1 = fake_exa_search("tendencias tech 2026", limit=5)
        self.assertEqual(call_count, 1, "Primera llamada debe ejecutar la función real")
        self.assertEqual(len(result1), 1)
        
        # Segunda llamada con MISMOS argumentos — HIT
        result2 = fake_exa_search("tendencias tech 2026", limit=5)
        self.assertEqual(call_count, 1, "Segunda llamada NO debe ejecutar la función real (cache hit)")
        self.assertEqual(result1, result2, "Los resultados deben ser idénticos")
        
        print("   ✅ TEST 1 PASSED: Exa no se llama dos veces por la misma consulta")

    def test_02_different_queries_different_cache(self):
        """Queries distintas deben tener entradas de caché independientes."""
        from api_cache import cached_api_call
        
        call_count = 0
        
        @cached_api_call(ttl_hours=12)
        def fake_google_news(query, lang="es"):
            nonlocal call_count
            call_count += 1
            return [{"title": f"News: {query}", "lang": lang}]
        
        fake_google_news("crypto news", lang="es")
        fake_google_news("AI trends", lang="en")
        self.assertEqual(call_count, 2, "Distintas queries deben generar llamadas separadas")
        
        # Repetir ambas — HIT
        fake_google_news("crypto news", lang="es")
        fake_google_news("AI trends", lang="en")
        self.assertEqual(call_count, 2, "Repetir las queries no debe generar llamadas adicionales")
        
        print("   ✅ TEST 2 PASSED: Queries distintas tienen caché independiente")

    def test_03_cache_expiry_ttl(self):
        """Entradas expiradas deben regenerarse."""
        from api_cache import cached_api_call, _load_cache, _save_cache
        
        call_count = 0
        
        @cached_api_call(ttl_hours=0.001)  # TTL de ~3.6 segundos
        def fake_api(query):
            nonlocal call_count
            call_count += 1
            return [{"title": query}]
        
        fake_api("test_expiry")
        self.assertEqual(call_count, 1)
        
        # Forzar expiración manipulando el timestamp
        cache = _load_cache()
        for key in cache:
            cache[key]["cached_at"] = time.time() - 3700  # 1h+ expirada
        _save_cache(cache)
        
        fake_api("test_expiry")
        self.assertEqual(call_count, 2, "Entrada expirada debe regenerarse")
        
        print("   ✅ TEST 3 PASSED: TTL expira y fuerza re-fetch")

    def test_04_cache_file_persistence(self):
        """La caché debe persistir en disco entre instancias."""
        from api_cache import cached_api_call, _load_cache
        
        @cached_api_call(ttl_hours=12)
        def fake_persist(query):
            return [{"data": query}]
        
        fake_persist("persist_test")
        
        # Verificar que el archivo existe y tiene contenido
        cache = _load_cache()
        self.assertGreater(len(cache), 0, "La caché debe tener al menos una entrada")
        
        print("   ✅ TEST 4 PASSED: Caché persiste en disco")

    def test_05_cache_handles_empty_result(self):
        """Resultados vacíos no deben crashear la caché."""
        from api_cache import cached_api_call
        
        @cached_api_call(ttl_hours=12)
        def fake_empty_api():
            return []
        
        result = fake_empty_api()
        self.assertEqual(result, [])
        
        print("   ✅ TEST 5 PASSED: Resultados vacíos manejados correctamente")


# ============================================================
# TEST 2: JSON Estandarizado (Parseo Estricto)
# ============================================================

class TestJSONStandardization(unittest.TestCase):
    """Tests para la estandarización de respuestas JSON de los LLMs."""

    def test_06_nvidia_nim_force_json_parameter(self):
        """_call_nvidia_nim debe aceptar force_json=True y pasar response_format."""
        # Importar desde main.py
        from main import _call_nvidia_nim
        
        # Mock del cliente OpenAI
        with patch('main.OpenAI') as MockOpenAI:
            mock_client = MagicMock()
            MockOpenAI.return_value = mock_client
            
            # Simular respuesta JSON válida
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"titulo": "Test Title", "slug": "test-title"}'
            mock_client.chat.completions.create.return_value = mock_response
            
            result, success = _call_nvidia_nim(
                "Generate article metadata",
                "z-ai/glm4.7",
                "",
                "fake-nvidia-key",
                max_tokens=1024,
                force_json=True
            )
            
            # Verificar que se pasó response_format
            call_kwargs = mock_client.chat.completions.create.call_args
            self.assertIn('response_format', call_kwargs.kwargs,
                         "force_json=True debe pasar response_format al API")
            self.assertEqual(call_kwargs.kwargs['response_format'], {"type": "json_object"})
            
            # Verificar que el resultado es parseable como JSON
            parsed = json.loads(result)
            self.assertEqual(parsed["titulo"], "Test Title")
            
            print("   ✅ TEST 6 PASSED: NVIDIA NIM soporta force_json=True y devuelve JSON puro")

    def test_07_nvidia_nim_without_force_json(self):
        """_call_nvidia_nim sin force_json NO debe pasar response_format."""
        from main import _call_nvidia_nim
        
        with patch('main.OpenAI') as MockOpenAI:
            mock_client = MagicMock()
            MockOpenAI.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "A long article about technology..." * 20
            mock_client.chat.completions.create.return_value = mock_response
            
            result, success = _call_nvidia_nim(
                "Write an article",
                "z-ai/glm4.7",
                "",
                "fake-nvidia-key"
            )
            
            call_kwargs = mock_client.chat.completions.create.call_args
            self.assertNotIn('response_format', call_kwargs.kwargs,
                            "Sin force_json, no debe pasar response_format")
            
            print("   ✅ TEST 7 PASSED: NVIDIA NIM sin force_json no inyecta response_format")

    def test_08_planificar_articulo_uses_json_mime(self):
        """planificar_articulo() debe usar response_mime_type='application/json'."""
        # Verificar leyendo el código fuente directamente
        import inspect
        from main import planificar_articulo
        
        source = inspect.getsource(planificar_articulo)
        self.assertIn('response_mime_type="application/json"', source,
                      "planificar_articulo DEBE usar response_mime_type para garantizar JSON")
        self.assertIn('json.loads', source,
                      "planificar_articulo DEBE parsear la respuesta con json.loads")
        
        print("   ✅ TEST 8 PASSED: planificar_articulo() usa JSON estricto de Gemini")

    def test_09_trend_hunter_uses_json_response(self):
        """trend_hunter.py debe usar response_mime_type para generación de títulos."""
        import inspect
        from trend_hunter import TrendHunter
        
        # Verificar _generate_long_tail_idea
        source_lt = inspect.getsource(TrendHunter._generate_long_tail_idea)
        self.assertIn('response_mime_type="application/json"', source_lt,
                      "_generate_long_tail_idea DEBE usar JSON response mode")
        self.assertIn('json.loads', source_lt,
                      "_generate_long_tail_idea DEBE parsear con json.loads")
        
        # Verificar _generate_news_topic_llm
        source_news = inspect.getsource(TrendHunter._generate_news_topic_llm)
        self.assertIn('response_mime_type="application/json"', source_news,
                      "_generate_news_topic_llm DEBE usar JSON response mode")
        
        print("   ✅ TEST 9 PASSED: trend_hunter.py usa JSON estricto en todas las funciones de título")

    def test_10_stocks_writer_uses_json_for_titles(self):
        """stocks_writer.py debe usar JSON para la generación de títulos financieros."""
        # Leer el archivo fuente directamente
        stocks_path = os.path.join(os.path.dirname(__file__), 'stocks_writer.py')
        with open(stocks_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Verificar que ya no usa el patrón frágil BEST:
        self.assertNotIn("startswith('BEST:')", source,
                         "stocks_writer.py NO DEBE usar parseo frágil con BEST:")
        
        # Verificar que usa JSON
        self.assertIn('response_mime_type="application/json"', source,
                      "stocks_writer.py DEBE usar response_mime_type para títulos")
        self.assertIn('json.loads', source,
                      "stocks_writer.py DEBE parsear títulos con json.loads")
        
        print("   ✅ TEST 10 PASSED: stocks_writer.py usa JSON estricto para títulos")


# ============================================================
# EJECUTOR
# ============================================================

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🧪 TEST SUITE: Caché Agresiva + JSON Estandarizado")
    print("=" * 60 + "\n")
    
    unittest.main(verbosity=2)
