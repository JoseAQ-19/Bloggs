import os
import requests
import logging
from datetime import datetime, timedelta

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# ═══════════════════════════════════════════════════════════════════
# REGIONAL SERIES MAPPING — Datos locales en lugar de solo nacionales
# ═══════════════════════════════════════════════════════════════════

# FRED: Series de precios de vivienda por estado/metro (Case-Shiller + FHFA HPI)
FRED_REGIONAL_SERIES = {
    # State-level FHFA House Price Index (All-Transactions)
    "florida":      {"hpi": "FLSTHPI",  "label": "Florida HPI"},
    "texas":        {"hpi": "TXSTHPI",  "label": "Texas HPI"},
    "california":   {"hpi": "CASTHPI",  "label": "California HPI"},
    "new york":     {"hpi": "NYSTHPI",  "label": "New York HPI"},
    "arizona":      {"hpi": "AZSTHPI",  "label": "Arizona HPI"},
    "nevada":       {"hpi": "NVSTHPI",  "label": "Nevada HPI"},
    "georgia":      {"hpi": "GASTHPI",  "label": "Georgia HPI"},
    "colorado":     {"hpi": "COSTHPI",  "label": "Colorado HPI"},
    "washington":   {"hpi": "WASTHPI",  "label": "Washington HPI"},
    "illinois":     {"hpi": "ILSTHPI",  "label": "Illinois HPI"},
    # Metro-level Case-Shiller (Top metros)
    "miami":        {"hpi": "MIXRNSA",  "label": "Miami Metro Case-Shiller"},
    "los angeles":  {"hpi": "LXXRNSA",  "label": "LA Metro Case-Shiller"},
    "new york city": {"hpi": "NYXRNSA", "label": "NYC Metro Case-Shiller"},
    "chicago":      {"hpi": "CHXRNSA",  "label": "Chicago Metro Case-Shiller"},
    "dallas":       {"hpi": "DAXRNSA",  "label": "Dallas Metro Case-Shiller"},
    "atlanta":      {"hpi": "ATXRNSA",  "label": "Atlanta Metro Case-Shiller"},
    "phoenix":      {"hpi": "PHXRNSA",  "label": "Phoenix Metro Case-Shiller"},
    "seattle":      {"hpi": "SEXRNSA",  "label": "Seattle Metro Case-Shiller"},
}

# INE: Tablas de Compraventa de Viviendas por Comunidad Autónoma
# Tabla 25971 con filtros por CCAA (códigos INE oficiales)
INE_REGIONAL_CODES = {
    "madrid":           "28",
    "cataluña":         "09",
    "catalunya":        "09",
    "andalucía":        "01",
    "andalucia":        "01",
    "valencia":         "10",
    "comunidad valenciana": "10",
    "país vasco":       "16",
    "pais vasco":       "16",
    "galicia":          "12",
    "castilla y león":  "07",
    "castilla la mancha": "08",
    "canarias":         "05",
    "baleares":         "04",
    "aragón":           "02",
    "murcia":           "14",
    "asturias":         "03",
    "navarra":          "15",
    "extremadura":      "11",
    "cantabria":        "06",
    "la rioja":         "17",
}


class RealEstateDataFetcher:
    """
    Fetcher especializado en datos inmobiliarios 100% gratuitos (INE y FRED).
    Soporta hiper-localización por estado (USA) y CCAA (España).
    """
    
    def __init__(self):
        self.fred_api_key = os.getenv("FRED_API_KEY")
        self.ine_base_url = "https://servicios.ine.es/wstempus/js/es/DATOS_TABLA/"

    def _detect_regions(self, topic):
        """
        Escanea el topic/query del Scout para detectar nombres de regiones.
        Devuelve un dict con las regiones USA y España detectadas.
        """
        topic_lower = topic.lower() if topic else ""
        detected = {"usa_regions": [], "spain_regions": []}
        
        for region_name, series_info in FRED_REGIONAL_SERIES.items():
            if region_name in topic_lower:
                detected["usa_regions"].append({
                    "name": region_name,
                    "series_id": series_info["hpi"],
                    "label": series_info["label"]
                })
        
        for region_name, code in INE_REGIONAL_CODES.items():
            if region_name in topic_lower:
                detected["spain_regions"].append({
                    "name": region_name,
                    "code": code
                })
        
        return detected

    def get_fred_series(self, series_id, limit=5):
        """Obtiene datos de la Reserva Federal de St. Louis (FRED)."""
        if not self.fred_api_key:
            logging.warning("⚠️ FRED_API_KEY no encontrada. Saltando datos USA.")
            return None
            
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.fred_api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("observations", [])
            else:
                logging.error(f"❌ Error FRED ({series_id}): {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"💥 Excepción en FRED ({series_id}): {str(e)}")
            return None

    def get_ine_table(self, table_id, ccaa_code=None):
        """
        Obtiene datos del INE (España) vía JSON API.
        Si ccaa_code se proporciona, filtra resultados por Comunidad Autónoma.
        """
        url = f"{self.ine_base_url}{table_id}?nult=5"  # Últimos 5 datos
        
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                all_data = response.json()
                
                # Si no hay filtro regional, devolver todo
                if not ccaa_code:
                    return all_data
                
                # Filtrar por código de CCAA en el nombre de la serie
                filtered = []
                for series in all_data:
                    nombre = series.get("Nombre", "")
                    # El INE suele incluir el código de CCAA en el nombre o como metadato
                    cod_field = series.get("COD", "")
                    if ccaa_code in str(cod_field) or ccaa_code in nombre:
                        filtered.append(series)
                
                return filtered if filtered else all_data
            else:
                logging.error(f"❌ Error INE (Tabla {table_id}): {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"💥 Excepción en INE (Tabla {table_id}): {str(e)}")
            return None

    def fetch_all(self, topic=""):
        """
        Recopila un resumen de datos inmobiliarios para inyectar al LLM.
        Acepta un topic opcional para activar la hiper-localización automática.
        """
        data = {
            "usa": {},
            "spain": {},
            "regional": {"usa": [], "spain": []}
        }
        
        # Detectar regiones en el topic
        regions = self._detect_regions(topic)
        
        # --- USA DATA NACIONAL (FRED) ---
        mortgage_rates = self.get_fred_series("MORTGAGE30US")
        if mortgage_rates:
            data["usa"]["mortgage_30y_fixed"] = mortgage_rates[0]["value"]
            data["usa"]["last_update_rates"] = mortgage_rates[0]["date"]
            
        hpi = self.get_fred_series("CSUSHPINSA")  # Case-Shiller Nacional
        if hpi:
            data["usa"]["case_shiller_index"] = hpi[0]["value"]
            data["usa"]["hpi_date"] = hpi[0]["date"]

        # --- USA DATA REGIONAL (FRED) ---
        for region in regions.get("usa_regions", []):
            regional_hpi = self.get_fred_series(region["series_id"], limit=5)
            if regional_hpi:
                # Colectar serie temporal completa para gráficos
                series_data = []
                for obs in reversed(regional_hpi):
                    if obs["value"] != ".":
                        series_data.append({
                            "date": obs["date"],
                            "value": float(obs["value"])
                        })
                data["regional"]["usa"].append({
                    "name": region["name"].title(),
                    "label": region["label"],
                    "current_value": regional_hpi[0]["value"],
                    "current_date": regional_hpi[0]["date"],
                    "series": series_data
                })

        # --- SPAIN DATA NACIONAL (INE) ---
        # 25971: Transmisiones de derechos de la propiedad (Compraventa de viviendas)
        compraventa = self.get_ine_table("25971")
        if compraventa:
            for series in compraventa:
                if "Total" in series.get("Nombre", "") and "Viviendas" in series.get("Nombre", ""):
                    data["spain"]["compraventa_viviendas"] = series["Data"][0]["Valor"]
                    data["spain"]["date"] = series["Data"][0]["Anyo"]
                    break

        # --- SPAIN DATA REGIONAL (INE) ---
        for region in regions.get("spain_regions", []):
            regional_data = self.get_ine_table("25971", ccaa_code=region["code"])
            if regional_data:
                for series in regional_data:
                    nombre = series.get("Nombre", "")
                    if "Viviendas" in nombre:
                        data["regional"]["spain"].append({
                            "name": region["name"].title(),
                            "value": series["Data"][0]["Valor"],
                            "date": series["Data"][0]["Anyo"],
                            "series_name": nombre
                        })
                        break
        
        return data

    def format_for_llm(self, data):
        """Convierte los datos en un bloque de texto legible para el prompt."""
        if not data:
            return "No hay datos inmobiliarios actualizados disponibles hoy."
            
        report = "### 📊 REAL ESTATE HARVEST DATA (OFFICIAL SOURCES)\n"
        
        # Nacional USA
        if data.get("usa"):
            report += f"- **USA (FRED/FHFA)**: Last Mortgage Rate (30Y Fixed): {data['usa'].get('mortgage_30y_fixed', 'N/A')}% (Date: {data['usa'].get('last_update_rates', 'N/A')}).\n"
            report += f"- **USA (Case-Shiller HPI)**: {data['usa'].get('case_shiller_index', 'N/A')} points.\n"
        
        # Regional USA
        for region in data.get("regional", {}).get("usa", []):
            report += f"- **USA — {region['name']} ({region['label']})**: {region['current_value']} points (Date: {region['current_date']}).\n"
            
        # Nacional España
        if data.get("spain"):
            report += f"- **ESPAÑA (INE)**: Último dato de Compraventa de Viviendas: {data['spain'].get('compraventa_viviendas', 'N/A')} operaciones (Año: {data['spain'].get('date', 'N/A')}).\n"
            report += "- **NOTA**: El Euríbor actual debe ser verificado vía noticias frescas diarias.\n"

        # Regional España
        for region in data.get("regional", {}).get("spain", []):
            report += f"- **ESPAÑA — {region['name']}**: {region['value']} operaciones ({region['series_name']}, Año: {region['date']}).\n"
            
        return report


if __name__ == "__main__":
    # Test rápido — con y sin localización
    fetcher = RealEstateDataFetcher()
    
    # Test nacional
    print("=== TEST NACIONAL ===")
    results = fetcher.fetch_all()
    print(fetcher.format_for_llm(results))
    
    # Test localizado
    print("\n=== TEST LOCALIZADO (Florida + Madrid) ===")
    results_local = fetcher.fetch_all(topic="housing market crash Florida vs Madrid rental yield")
    print(fetcher.format_for_llm(results_local))
