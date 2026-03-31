import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI/CD (no display needed)
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os
import logging
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO)


class ChartEngine:
    """
    Motor de generación de gráficos visuales para Google Discover.
    Crea archivos PNG ligeros basados en datos reales de los artículos.
    Estilo: Dark Mode Premium (NovumWorld brand).
    """
    
    def __init__(self, output_dir="static/charts"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        # Configuración estética premium NovumWorld
        plt.rcParams.update({
            'figure.facecolor': '#0d1117',
            'axes.facecolor': '#161b22',
            'axes.edgecolor': '#30363d',
            'axes.labelcolor': '#c9d1d9',
            'text.color': '#c9d1d9',
            'xtick.color': '#8b949e',
            'ytick.color': '#8b949e',
            'grid.color': '#21262d',
            'grid.alpha': 0.6,
            'font.family': 'sans-serif',
            'font.size': 11,
        })

    def generate_line_chart(self, x_data, y_data, title, xlabel, ylabel, filename, color='#58a6ff'):
        """Genera un gráfico de líneas premium con estilo NovumWorld."""
        try:
            fig, ax = plt.subplots(figsize=(10, 5.5))
            
            # Línea principal con gradiente simulado
            ax.plot(x_data, y_data, marker='o', markersize=5, linestyle='-',
                    color=color, linewidth=2.5, zorder=3)
            
            # Área sombreada bajo la línea (efecto premium)
            ax.fill_between(x_data, y_data, alpha=0.08, color=color)
            
            # Anotación del último valor
            last_val = y_data[-1]
            ax.annotate(f'{last_val:,.1f}', xy=(x_data[-1], last_val),
                        xytext=(10, 10), textcoords='offset points',
                        fontsize=12, fontweight='bold', color=color,
                        arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
            
            ax.set_title(title, fontsize=15, fontweight='bold', pad=15, color='white')
            ax.set_xlabel(xlabel, fontsize=10, labelpad=8)
            ax.set_ylabel(ylabel, fontsize=10, labelpad=8)
            ax.grid(True, linestyle='--', alpha=0.3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Rotar etiquetas del eje X si son muchas
            if len(x_data) > 6:
                plt.xticks(rotation=45, ha='right')
            
            # Marca de agua NovumWorld
            fig.text(0.98, 0.02, 'NovumWorld.com', fontsize=8, color='#484f58',
                     ha='right', va='bottom', alpha=0.7, style='italic')
            
            plt.tight_layout()
            
            # Sanitizar filename
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)
            save_path = os.path.join(self.output_dir, f"{safe_name}.png")
            plt.savefig(save_path, bbox_inches='tight', dpi=120, facecolor=fig.get_facecolor())
            plt.close(fig)
            
            logging.info(f"✅ Gráfico guardado en: {save_path}")
            return f"/charts/{safe_name}.png"
        except Exception as e:
            logging.error(f"❌ Error generando gráfico {filename}: {e}")
            return None

    def generate_real_estate_trend(self, data, topic=""):
        """
        Genera gráficos de tendencia inmobiliaria a partir del reporte de FRED/INE.
        Devuelve una lista de etiquetas Markdown para inyectar en el artículo.
        
        Args:
            data: Dict devuelto por RealEstateDataFetcher.fetch_all()
            topic: String del tema (para generar nombres de archivo únicos)
        
        Returns:
            list[str]: Lista de strings Markdown con las imágenes generadas.
                       Ej: ["![Evolución HPI Florida](/charts/hpi_florida_2026.png)"]
        """
        markdown_tags = []
        timestamp = datetime.now().strftime("%Y%m")
        
        if not data:
            logging.warning("⚠️ Sin datos para generar gráficos inmobiliarios.")
            return markdown_tags

        # === GRÁFICO 1: Series regionales USA (FRED HPI) ===
        usa_regions = data.get("regional", {}).get("usa", [])
        for region in usa_regions:
            series = region.get("series", [])
            if len(series) >= 3:  # Mínimo 3 puntos para un gráfico útil
                x_dates = [s["date"] for s in series]
                y_values = [s["value"] for s in series]
                region_slug = re.sub(r'[^a-z0-9]', '_', region["name"].lower())
                
                filename = f"hpi_{region_slug}_{timestamp}"
                title = f"House Price Index — {region['name']} ({region['label']})"
                
                path = self.generate_line_chart(
                    x_data=x_dates,
                    y_data=y_values,
                    title=title,
                    xlabel="Date",
                    ylabel="HPI Index Points",
                    filename=filename,
                    color='#58a6ff'
                )
                
                if path:
                    alt_text = f"Evolución del índice de precios de vivienda en {region['name']}"
                    markdown_tags.append(f"![{alt_text}]({path})")
                    logging.info(f"📊 Gráfico regional USA generado: {region['name']}")

        # === GRÁFICO 2: Mortgage Rate trend (nacional USA) ===
        mortgage_series = self._get_mortgage_history()
        if mortgage_series and len(mortgage_series) >= 3:
            x_dates = [s["date"] for s in mortgage_series]
            y_values = [s["value"] for s in mortgage_series]
            
            path = self.generate_line_chart(
                x_data=x_dates,
                y_data=y_values,
                title="30-Year Fixed Mortgage Rate (USA — FRED)",
                xlabel="Date",
                ylabel="Rate (%)",
                filename=f"mortgage_30y_{timestamp}",
                color='#f97583'
            )
            
            if path:
                markdown_tags.append(f"![Evolución hipoteca 30 años USA]({path})")
                logging.info("📊 Gráfico hipoteca 30Y generado.")

        if markdown_tags:
            logging.info(f"🏆 Total gráficos inmobiliarios generados: {len(markdown_tags)}")
        else:
            logging.info("ℹ️ Sin datos regionales suficientes para gráficos. Solo datos nacionales disponibles.")
            
        return markdown_tags

    def _get_mortgage_history(self):
        """
        Helper: obtiene la serie temporal de mortgage rates para el gráfico nacional.
        Usa la misma API que RealEstateDataFetcher pero con más puntos.
        """
        try:
            from data_realestate import RealEstateDataFetcher
            fetcher = RealEstateDataFetcher()
            observations = fetcher.get_fred_series("MORTGAGE30US", limit=12)
            if observations:
                series = []
                for obs in reversed(observations):
                    if obs["value"] != ".":
                        series.append({
                            "date": obs["date"],
                            "value": float(obs["value"])
                        })
                return series
        except Exception as e:
            logging.warning(f"⚠️ No se pudo obtener serie de mortgage: {e}")
        return None


if __name__ == "__main__":
    # Test E2E
    engine = ChartEngine()
    
    # Test básico (línea manual)
    path = engine.generate_line_chart(
        ["Ene", "Feb", "Mar", "Abr", "May"],
        [3.8, 4.1, 3.9, 4.2, 4.5],
        "Evolución Euríbor 2026 (Proyectado)",
        "Meses",
        "Tasa (%)",
        "euribor_trend_test",
        color='#00ffcc'
    )
    print(f"Test básico: {path}")
    
    # Test con datos reales del fetcher
    try:
        from data_realestate import RealEstateDataFetcher
        fetcher = RealEstateDataFetcher()
        data = fetcher.fetch_all(topic="Florida housing market crash 2026")
        charts = engine.generate_real_estate_trend(data, topic="florida")
        print(f"\nGráficos generados: {len(charts)}")
        for chart in charts:
            print(f"  → {chart}")
    except Exception as e:
        print(f"Test regional: {e}")
