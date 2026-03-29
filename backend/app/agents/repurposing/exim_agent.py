"""
EXIM Trade Agent - Import/Export data for pharmaceutical APIs and formulations.

Provides trade volume data, sourcing insights, and country-level trends.
Uses realistic mock data based on public UN Comtrade and Indian DGFT patterns.
"""

from typing import Dict, Any, List, Optional
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("agents.exim")

# Realistic mock EXIM data based on public trade statistics
EXIM_DATABASE = {
    "metformin": {
        "molecule": "Metformin HCl",
        "hs_code": "29262000",
        "category": "Anti-diabetic API",
        "global_trade_volume_mt": 45000,
        "global_trade_value_usd": 850_000_000,
        "cagr_5yr": 6.2,
        "top_exporters": [
            {"country": "India", "volume_mt": 18500, "value_usd": 320_000_000, "share_pct": 41.1, "yoy_growth": 8.5},
            {"country": "China", "volume_mt": 15200, "value_usd": 250_000_000, "share_pct": 33.8, "yoy_growth": 4.2},
            {"country": "Germany", "volume_mt": 3800, "value_usd": 95_000_000, "share_pct": 8.4, "yoy_growth": 2.1},
            {"country": "France", "volume_mt": 2100, "value_usd": 58_000_000, "share_pct": 4.7, "yoy_growth": 1.8},
            {"country": "Italy", "volume_mt": 1800, "value_usd": 45_000_000, "share_pct": 4.0, "yoy_growth": 3.1},
        ],
        "top_importers": [
            {"country": "USA", "volume_mt": 12000, "value_usd": 280_000_000, "share_pct": 26.7, "yoy_growth": 5.3},
            {"country": "Germany", "volume_mt": 5500, "value_usd": 120_000_000, "share_pct": 12.2, "yoy_growth": 3.8},
            {"country": "Brazil", "volume_mt": 4200, "value_usd": 85_000_000, "share_pct": 9.3, "yoy_growth": 7.2},
            {"country": "Japan", "volume_mt": 3100, "value_usd": 75_000_000, "share_pct": 6.9, "yoy_growth": 2.5},
            {"country": "UK", "volume_mt": 2800, "value_usd": 65_000_000, "share_pct": 6.2, "yoy_growth": 4.1},
        ],
        "insights": [
            "India dominates global Metformin API exports with 41% market share",
            "Growing demand in Latin America (Brazil +7.2% YoY) driven by rising diabetes prevalence",
            "China-India price competition keeps margins tight for generic manufacturers",
            "US import dependence on India/China creates supply chain vulnerability",
        ],
        "trend": "Steady growth driven by global diabetes epidemic; 537M patients worldwide",
    },
    "atorvastatin": {
        "molecule": "Atorvastatin Calcium",
        "hs_code": "29362990",
        "category": "Statin / Lipid-lowering API",
        "global_trade_volume_mt": 12000,
        "global_trade_value_usd": 520_000_000,
        "cagr_5yr": 3.8,
        "top_exporters": [
            {"country": "India", "volume_mt": 5400, "value_usd": 195_000_000, "share_pct": 45.0, "yoy_growth": 5.2},
            {"country": "China", "volume_mt": 3600, "value_usd": 130_000_000, "share_pct": 30.0, "yoy_growth": 2.8},
            {"country": "Ireland", "volume_mt": 1200, "value_usd": 85_000_000, "share_pct": 10.0, "yoy_growth": 1.5},
            {"country": "Spain", "volume_mt": 800, "value_usd": 48_000_000, "share_pct": 6.7, "yoy_growth": 3.2},
        ],
        "top_importers": [
            {"country": "USA", "volume_mt": 4500, "value_usd": 180_000_000, "share_pct": 37.5, "yoy_growth": 2.1},
            {"country": "Germany", "volume_mt": 1800, "value_usd": 72_000_000, "share_pct": 15.0, "yoy_growth": 1.8},
            {"country": "Japan", "volume_mt": 1200, "value_usd": 55_000_000, "share_pct": 10.0, "yoy_growth": -0.5},
            {"country": "Brazil", "volume_mt": 900, "value_usd": 38_000_000, "share_pct": 7.5, "yoy_growth": 4.5},
        ],
        "insights": [
            "Patent expired in 2011; highly competitive generic market",
            "India is the largest API supplier globally at 45% share",
            "Japanese market declining due to shift to newer statins (rosuvastatin)",
            "Brazil showing strong growth as cardiovascular disease burden rises",
        ],
        "trend": "Mature market with stable demand; growth driven by emerging markets",
    },
    "ibuprofen": {
        "molecule": "Ibuprofen",
        "hs_code": "29163900",
        "category": "NSAID / Anti-inflammatory API",
        "global_trade_volume_mt": 65000,
        "global_trade_value_usd": 720_000_000,
        "cagr_5yr": 4.5,
        "top_exporters": [
            {"country": "India", "volume_mt": 28000, "value_usd": 280_000_000, "share_pct": 43.1, "yoy_growth": 6.8},
            {"country": "China", "volume_mt": 22000, "value_usd": 210_000_000, "share_pct": 33.8, "yoy_growth": 3.5},
            {"country": "Germany", "volume_mt": 5500, "value_usd": 85_000_000, "share_pct": 8.5, "yoy_growth": 2.0},
        ],
        "top_importers": [
            {"country": "USA", "volume_mt": 18000, "value_usd": 220_000_000, "share_pct": 27.7, "yoy_growth": 4.2},
            {"country": "Germany", "volume_mt": 8000, "value_usd": 95_000_000, "share_pct": 12.3, "yoy_growth": 2.8},
            {"country": "UK", "volume_mt": 5500, "value_usd": 65_000_000, "share_pct": 8.5, "yoy_growth": 3.5},
        ],
        "insights": [
            "One of the highest-volume APIs in global trade",
            "India and China together supply 77% of global Ibuprofen API",
            "OTC market expansion driving volume growth in emerging markets",
        ],
        "trend": "High-volume, price-sensitive market; OTC growth driving demand",
    },
    "sildenafil": {
        "molecule": "Sildenafil Citrate",
        "hs_code": "29349990",
        "category": "PDE5 Inhibitor API",
        "global_trade_volume_mt": 800,
        "global_trade_value_usd": 280_000_000,
        "cagr_5yr": 8.5,
        "top_exporters": [
            {"country": "India", "volume_mt": 420, "value_usd": 145_000_000, "share_pct": 52.5, "yoy_growth": 12.3},
            {"country": "China", "volume_mt": 220, "value_usd": 72_000_000, "share_pct": 27.5, "yoy_growth": 6.8},
            {"country": "Israel", "volume_mt": 80, "value_usd": 35_000_000, "share_pct": 10.0, "yoy_growth": 4.5},
        ],
        "top_importers": [
            {"country": "USA", "volume_mt": 250, "value_usd": 95_000_000, "share_pct": 31.3, "yoy_growth": 9.2},
            {"country": "EU (aggregate)", "volume_mt": 180, "value_usd": 68_000_000, "share_pct": 22.5, "yoy_growth": 5.8},
            {"country": "Brazil", "volume_mt": 85, "value_usd": 32_000_000, "share_pct": 10.6, "yoy_growth": 15.2},
        ],
        "insights": [
            "Dual indication (ED + PAH) drives robust API demand",
            "India dominates with 52.5% export share; Teva/Sun Pharma are key players",
            "Brazil fastest-growing import market (+15.2% YoY)",
            "PAH indication (as Revatio) expands total addressable market beyond ED",
        ],
        "trend": "Growing strongly; dual-indication market and generic entry boosting volumes",
    },
    "adalimumab": {
        "molecule": "Adalimumab (biosimilar API)",
        "hs_code": "30021500",
        "category": "Anti-TNF Monoclonal Antibody",
        "global_trade_volume_mt": 15,
        "global_trade_value_usd": 2_800_000_000,
        "cagr_5yr": 22.5,
        "top_exporters": [
            {"country": "India", "volume_mt": 4.5, "value_usd": 680_000_000, "share_pct": 30.0, "yoy_growth": 35.2},
            {"country": "South Korea", "volume_mt": 3.8, "value_usd": 750_000_000, "share_pct": 25.3, "yoy_growth": 28.5},
            {"country": "EU (aggregate)", "volume_mt": 3.2, "value_usd": 620_000_000, "share_pct": 21.3, "yoy_growth": 18.2},
            {"country": "USA", "volume_mt": 2.0, "value_usd": 480_000_000, "share_pct": 13.3, "yoy_growth": 45.0},
        ],
        "top_importers": [
            {"country": "USA", "volume_mt": 5.5, "value_usd": 1_200_000_000, "share_pct": 36.7, "yoy_growth": 42.0},
            {"country": "EU (aggregate)", "volume_mt": 4.2, "value_usd": 850_000_000, "share_pct": 28.0, "yoy_growth": 25.0},
            {"country": "Japan", "volume_mt": 1.8, "value_usd": 350_000_000, "share_pct": 12.0, "yoy_growth": 20.0},
        ],
        "insights": [
            "Fastest-growing biosimilar market globally after Humira patent expiry (2023 US)",
            "9 biosimilar competitors now approved in the US market",
            "India emerging as key biosimilar manufacturing hub (Biocon, Zydus, Intas)",
            "Price erosion of 50-80% vs originator creating massive volume growth",
            "Trade value still growing despite price erosion due to volume expansion",
        ],
        "trend": "Explosive growth post-patent expiry; biosimilar competition intensifying",
    },
    "semaglutide": {
        "molecule": "Semaglutide (peptide API)",
        "hs_code": "29371900",
        "category": "GLP-1 Receptor Agonist",
        "global_trade_volume_mt": 5,
        "global_trade_value_usd": 1_500_000_000,
        "cagr_5yr": 45.0,
        "top_exporters": [
            {"country": "Denmark", "volume_mt": 3.5, "value_usd": 1_100_000_000, "share_pct": 70.0, "yoy_growth": 52.0},
            {"country": "USA", "volume_mt": 0.8, "value_usd": 250_000_000, "share_pct": 16.0, "yoy_growth": 38.0},
            {"country": "India", "volume_mt": 0.3, "value_usd": 80_000_000, "share_pct": 6.0, "yoy_growth": 120.0},
        ],
        "top_importers": [
            {"country": "USA", "volume_mt": 2.5, "value_usd": 850_000_000, "share_pct": 50.0, "yoy_growth": 65.0},
            {"country": "EU (aggregate)", "volume_mt": 1.2, "value_usd": 380_000_000, "share_pct": 24.0, "yoy_growth": 42.0},
            {"country": "Japan", "volume_mt": 0.5, "value_usd": 150_000_000, "share_pct": 10.0, "yoy_growth": 55.0},
        ],
        "insights": [
            "Novo Nordisk dominates supply chain from Denmark (70% export share)",
            "Indian manufacturers (Sun Pharma, Dr. Reddy's) entering peptide API space",
            "US accounts for 50% of global imports driven by Ozempic/Wegovy demand",
            "Supply shortages creating opportunity for new API manufacturers",
            "Patent protection until 2031-2036 limits generic/biosimilar entry",
        ],
        "trend": "Explosive growth (45% CAGR) driven by obesity/diabetes dual indication; supply constraints",
    },
    "aspirin": {
        "molecule": "Acetylsalicylic Acid",
        "hs_code": "29182200",
        "category": "NSAID / Antiplatelet API",
        "global_trade_volume_mt": 80000,
        "global_trade_value_usd": 450_000_000,
        "cagr_5yr": 2.5,
        "top_exporters": [
            {"country": "China", "volume_mt": 45000, "value_usd": 200_000_000, "share_pct": 56.3, "yoy_growth": 1.8},
            {"country": "India", "volume_mt": 15000, "value_usd": 90_000_000, "share_pct": 18.8, "yoy_growth": 3.5},
            {"country": "Germany", "volume_mt": 8000, "value_usd": 65_000_000, "share_pct": 10.0, "yoy_growth": 1.2},
        ],
        "top_importers": [
            {"country": "USA", "volume_mt": 15000, "value_usd": 85_000_000, "share_pct": 18.8, "yoy_growth": 1.5},
            {"country": "Germany", "volume_mt": 10000, "value_usd": 60_000_000, "share_pct": 12.5, "yoy_growth": 2.0},
            {"country": "France", "volume_mt": 6000, "value_usd": 38_000_000, "share_pct": 7.5, "yoy_growth": 1.8},
        ],
        "insights": [
            "Highest-volume pharmaceutical API in global trade",
            "China dominates production with 56% of global exports",
            "Cardiovascular prevention indication sustains long-term demand",
            "Mature commodity market with low margins",
        ],
        "trend": "Stable, high-volume commodity; growth from cardiovascular prevention use",
    },
}

# Default data for unknown molecules
DEFAULT_EXIM = {
    "molecule": "Unknown",
    "hs_code": "N/A",
    "category": "Pharmaceutical API",
    "global_trade_volume_mt": 0,
    "global_trade_value_usd": 0,
    "cagr_5yr": 0,
    "top_exporters": [],
    "top_importers": [],
    "insights": ["No EXIM trade data available for this molecule. Data coverage includes major generic APIs."],
    "trend": "No data available",
}


class EXIMAgent:
    """EXIM Trade Agent - provides import/export data for pharmaceutical molecules."""

    async def get_trade_data(self, drug_name: str) -> Dict[str, Any]:
        """
        Get EXIM trade data for a drug molecule.

        Returns structured data with tables, charts, and insights.
        """
        key = drug_name.lower().strip()
        data = EXIM_DATABASE.get(key, DEFAULT_EXIM.copy())

        if data["molecule"] == "Unknown":
            data["molecule"] = drug_name

        tables = []
        charts = []

        # Build exporter table
        if data["top_exporters"]:
            tables.append({
                "title": f"Top Exporters - {data['molecule']}",
                "columns": [
                    {"key": "country", "label": "Country"},
                    {"key": "volume_mt", "label": "Volume (MT)"},
                    {"key": "value_usd", "label": "Value (USD)"},
                    {"key": "share_pct", "label": "Market Share"},
                    {"key": "yoy_growth", "label": "YoY Growth"},
                ],
                "rows": [
                    {
                        "country": e["country"],
                        "volume_mt": f"{e['volume_mt']:,.0f}",
                        "value_usd": f"${e['value_usd']:,.0f}",
                        "share_pct": f"{e['share_pct']}%",
                        "yoy_growth": f"{e['yoy_growth']:+.1f}%",
                    }
                    for e in data["top_exporters"]
                ]
            })

        # Build importer table
        if data["top_importers"]:
            tables.append({
                "title": f"Top Importers - {data['molecule']}",
                "columns": [
                    {"key": "country", "label": "Country"},
                    {"key": "volume_mt", "label": "Volume (MT)"},
                    {"key": "value_usd", "label": "Value (USD)"},
                    {"key": "share_pct", "label": "Market Share"},
                    {"key": "yoy_growth", "label": "YoY Growth"},
                ],
                "rows": [
                    {
                        "country": i["country"],
                        "volume_mt": f"{i['volume_mt']:,.0f}",
                        "value_usd": f"${i['value_usd']:,.0f}",
                        "share_pct": f"{i['share_pct']}%",
                        "yoy_growth": f"{i['yoy_growth']:+.1f}%",
                    }
                    for i in data["top_importers"]
                ]
            })

        # Build export share chart
        if data["top_exporters"]:
            charts.append({
                "chart_type": "bar",
                "title": f"Export Market Share - {data['molecule']}",
                "labels": [e["country"] for e in data["top_exporters"]],
                "datasets": [
                    {
                        "label": "Market Share (%)",
                        "data": [e["share_pct"] for e in data["top_exporters"]],
                        "color": "#00D4AA"
                    },
                    {
                        "label": "YoY Growth (%)",
                        "data": [e["yoy_growth"] for e in data["top_exporters"]],
                        "color": "#FFE600"
                    }
                ]
            })

        summary_parts = [
            f"**{data['molecule']}** ({data['category']})",
            f"Global Trade Volume: {data['global_trade_volume_mt']:,.0f} MT | Value: ${data['global_trade_value_usd']:,.0f}",
            f"5-Year CAGR: {data['cagr_5yr']}%",
            f"Trend: {data['trend']}",
            "",
            "**Key Insights:**",
        ]
        for insight in data["insights"]:
            summary_parts.append(f"- {insight}")

        return {
            "summary": "\n".join(summary_parts),
            "tables": tables,
            "charts": charts,
            "data": data,
            "status": "success"
        }
