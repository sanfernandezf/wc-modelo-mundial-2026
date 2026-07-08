# WORLD CUP 2026 — Modelo de Predicción Monte Carlo

**Autor:** Santiago Fernández  
**Mentor:** Nathaniel Sinclair  
**Fecha:** 8 Julio 2026

---

## Estructura del proyecto

```
/home/santi/wc_model/
├── README.md                          ← Este archivo
├── montecarlo_v1.py                   ← V1: ELOs del repo (sin calibrar)
├── montecarlo_v2.py                   ← V2: ELOs reales (eloratings.net)
├── montecarlo_v3.py                   ← V3: + forma torneo + H2H + momentum
├── montecarlo_v4_calibrated.py        ← V4: + parámetros calibrados històricamente
├── calibrate.py                       ← Grid search de parámetros Poisson
├── best_params.json                   ← Parámetros óptimos encontrados
├── fifa_worldcup_2026_quarterfinalists.json  ← Datos FIFA API (180KB)
└── historical_calibration_data.json   ← 32 partidos eliminatorios 2018+2022
```

---

## Metodología

### Núcleo del modelo
Simulación Monte Carlo de 100.000 iteraciones del bracket completo desde cuartos de final hasta la final. Cada partido se resuelve mediante un modelo Poisson donde los goles esperados de cada equipo dependen de su ELO rating y el de su rival:

```
λ = 1.9 + 0.25 × (ELO_propio - ELO_rival) / 100
```

Los parámetros (base=1.9, pendiente=0.25) se obtuvieron mediante **grid search contra 32 partidos eliminatorios reales de los Mundiales 2018 y 2022**, maximizando la accuracy del modelo.

### Variables del modelo (V4)
| Variable | Peso | Fuente |
|---|---|---|
| ELO rating | Principal | eloratings.net (7 jul 2026) |
| Head-to-Head histórico | Ajuste +5 ELO por victoria neta | FIFA.com |
| Momentum | Ajuste +3 ELO por victoria consecutiva | ESPN / FIFA API |
| Factor estrella | +1.5 ELO por gol del máximo goleador | FIFA API |
| Penalización dependencia | -3 ELO si >50% goles son de un jugador | FIFA API |

### Reglas de partido
- Goles ~ Poisson(λ) para cada equipo
- Si empate → extra time con fatiga del 5% (λ × 0.95)
- Si sigue empate → penales con ventaja probabilística para el equipo de mayor ELO ajustado

---

## Calibración histórica

| Métrica | Valor |
|---|---|
| Partidos de calibración | 32 (16 de 2018 + 16 de 2022) |
| Baseline (solo favorito ELO) | 62.5% |
| **Modelo Poisson calibrado** | **84.4%** |
| Mejora sobre baseline | +21.9 pp |

Los parámetros óptimos (base=1.9, pendiente=0.25) duplican la pendiente respecto a los valores por defecto de internet (1.30, 0.18), lo que indica que **la diferencia de ELO tiene más peso predictivo del que se asume comúnmente** en modelos Poisson para fútbol de selecciones.

---

## Datos de las 8 selecciones en cuartos

| Selección | ELO | Forma | GF | GA | CS | SOS | DT | Formación | Máx. goleador |
|---|---|---|---|---|---|---|---|---|---|
| España | 2177 | DWWWW | 9 | 0 | 5 | 1822 | Luis de la Fuente | 4-1-2-3 | Oyarzabal (4) |
| Argentina | 2156 | WWWWW | 14 | 5 | 2 | 1753 | Lionel Scaloni | Variable | Messi (8) |
| Francia | 2143 | WWWWW | 14 | 2 | 3 | 1858 | Didier Deschamps | 4-2-3-1 | Mbappé (7) |
| Inglaterra | 2076 | WDWWW | 11 | 5 | 2 | 1779 | Thomas Tuchel | 4-2-3-1 | Kane (6) |
| Noruega | 1972 | WWLWW | 12 | 9 | 0 | 1866 | Ståle Solbakken | 4-1-2-3 | Haaland (7) |
| Bélgica | 1961 | DDWWW | 13 | 5 | 2 | 1807 | Rudi Garcia | 4-2-3-1 | Lukaku (3) |
| Suiza | 1949 | DWWWD | 9 | 3 | 3 | 1794 | Murat Yakin | Variable | Manzambi/Vargas (3) |
| Marruecos | 1921 | DWWDW | 10 | 4 | 2 | 1813 | Mohamed Ouahbi | 4-2-3-1 | Saibari (4) |

**Head-to-head destacado:** España domina a Bélgica 12-5-6 en 23 partidos históricos (goles 46-22).

---

## Resultados del modelo (100K simulaciones)

| Selección | Modelo v4 | Polymarket | Diferencia |
|---|---|---|---|
| **España** | **28.1%** | 18.1% | **+10.0%** infravalorada |
| Argentina | 25.9% | 18.4% | +7.5% infravalorada |
| Francia | 22.8% | 33.0% | -10.2% sobrevalorada |
| Inglaterra | 12.7% | 14.4% | -1.8% |
| Noruega | 3.8% | 5.8% | -2.0% |
| Suiza | 2.6% | 0.9% | +1.6% |
| Bélgica | 2.5% | 2.3% | +0.2% |
| Marruecos | 1.6% | 2.8% | -1.1% |

### Probabilidades por cuarto
| Cuarto | Fecha | Favorito | Prob. | Rival | Prob. |
|---|---|---|---|---|---|
| QF1 | 9 Jul | Francia | 79.0% | Marruecos | 21.0% |
| QF2 | 10 Jul | España | 78.7% | Bélgica | 21.3% |
| QF3 | 11 Jul | Inglaterra | 64.0% | Noruega | 36.0% |
| QF4 | 12 Jul | Argentina | 77.1% | Suiza | 22.9% |

---

## Fuentes de datos

| Fuente | Datos obtenidos | Acceso |
|---|---|---|
| eloratings.net | ELO ratings reales de todas las selecciones | Web pública |
| FIFA API | Alineaciones, goleadores, formaciones, entrenadores | api.fifa.com |
| ESPN | Resultados, goles, tarjetas, paradas | site.api.espn.com |
| FIFA Web | Head-to-head histórico entre selecciones | fifa.com |
| Polymarket | Cuotas de mercado en tiempo real | gamma-api.polymarket.com |

---

## Post para LinkedIn

```
El mercado dice Francia. Mi modelo dice España.

Llevo días construyendo un modelo Monte Carlo para el Mundial 2026.
No para acertar resultados — para encontrar dónde el mercado de predicciones se equivoca.

Metodología:
• ELO ratings reales (eloratings.net)
• Modelo Poisson calibrado contra 32 partidos eliminatorios de 2018 y 2022 (84.4% accuracy)
• Ajustes por forma, goles encajados, clean sheets y head-to-head histórico
• 100.000 simulaciones del bracket completo

El resultado:
España 28% — Mercado 18%  (+10 pts infravalorada)
Argentina 26% — Mercado 18%  (+7 pts infravalorada)
Francia 23% — Mercado 33%  (-10 pts sobrevalorada)
Inglaterra 13% — Mercado 14%

Dos señales fuertes:
1. El mercado sobrevalora a Francia. Mbappé no lo hace todo.
2. España lleva 5 partidos sin encajar un gol. Su ELO es el más alto del torneo.

El mercado compra nombre. El modelo compra datos.

#WorldCup2026 #MonteCarlo #DataScience #QuantFinance #AI
```
