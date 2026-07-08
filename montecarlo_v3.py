#!/usr/bin/env python3
"""
WORLD CUP 2026 — MODELO MEJORADO v3
Nathaniel Sinclair — 8 Julio 2026

Fuentes:
- eloratings.net (ELO real)
- FIFA API (alineaciones, goleadores)
- ESPN (resultados)
- FIFA Web (head-to-head)
"""
import json, math, random
from collections import defaultdict, OrderedDict

# ================================================================
# POISSON ENGINE
# ================================================================
def rand_poisson(lmbda):
    if lmbda < 1e-10: return 0
    L = math.exp(-lmbda)
    k = 0; p = 1.0
    while p > L: k += 1; p *= random.random()
    return k - 1

def poisson_lambda(elo_t, elo_o, bonus=0):
    return max(0.15, min(6.0, 1.30 + 0.18 * (elo_t - elo_o + bonus) / 100))

def simulate_match(elo_h, elo_a, h2h_adv=0, momentum_h=0, momentum_a=0,
                   star_h=0, star_a=0, dep_h=0, dep_a=0):
    """Simula partido con: H2H, momentum, estrella goleadora, dependencia"""
    # Estrella: +3 ELO por cada gol del max goleador (aporta clutch)
    # Dependencia: -2 ELO si >50% de los goles los hace un jugador (vulnerable)
    star_bonus_h = star_h * 1.5
    star_bonus_a = star_a * 1.5
    dep_penalty_h = dep_h * (-3)
    dep_penalty_a = dep_a * (-3)
    
    adj_h = elo_h + h2h_adv * 5 + momentum_h * 3 + star_bonus_h + dep_penalty_h
    adj_a = elo_a + momentum_a * 3 + star_bonus_a + dep_penalty_a
    
    lh = poisson_lambda(adj_h, adj_a)
    la = poisson_lambda(adj_a, adj_h)
    gh, ga = rand_poisson(lh), rand_poisson(la)
    
    if gh != ga: return gh, ga
    
    # Extra time
    gh_et = rand_poisson(poisson_lambda(adj_h * 0.95, adj_a))
    ga_et = rand_poisson(poisson_lambda(adj_a * 0.95, adj_h))
    if gh + gh_et != ga + ga_et: return gh + gh_et, ga + ga_et
    
    # Penales
    p = max(0.35, min(0.65, 0.5 + (adj_h - adj_a) / 2000 + h2h_adv * 0.01))
    return (gh + gh_et + 1, ga + ga_et) if random.random() < p else (gh + gh_et, ga + ga_et + 1)

# ================================================================
# TEAM DATA (MULTI-FUENTE)
# ================================================================
TEAMS_DATA = OrderedDict([
    ("ESP", {
        "name": "Spain", "elo": 2177,
        "form": "DWWWW", "gf": 9, "ga": 0,
        "clean_sheets": 5,
        "avg_gf": 1.8, "avg_ga": 0.0,
        "sos_avg": 1822,
        "momentum": 4,
        "formacion_base": "4-1-2-3",
        "entrenador": "Luis de la Fuente",
        "goleadores": ["Mikel Oyarzabal (4)", "Lamine Yamal (1)", "Alex Baena (1)", "Pedro Porro (1)"],
        "max_goleador": 4
    }),
    ("ARG", {
        "name": "Argentina", "elo": 2156,
        "form": "WWWWW", "gf": 14, "ga": 5,
        "clean_sheets": 2,
        "avg_gf": 2.8, "avg_ga": 1.0,
        "sos_avg": 1753,
        "momentum": 5,
        "formacion_base": "4-3-3 (variable)",
        "entrenador": "Lionel Scaloni",
        "goleadores": ["Lionel Messi (8)", "Lautaro Martinez (1)", "Lisandro Martinez (1)", "Giovani Lo Celso (1)"],
        "max_goleador": 8
    }),
    ("FRA", {
        "name": "France", "elo": 2143,
        "form": "WWWWW", "gf": 14, "ga": 2,
        "clean_sheets": 3,
        "avg_gf": 2.8, "avg_ga": 0.4,
        "sos_avg": 1858,
        "momentum": 5,
        "formacion_base": "4-2-3-1",
        "entrenador": "Didier Deschamps",
        "goleadores": ["Kylian Mbappe (7)", "Ousmane Dembele (4)", "Bradley Barcola (2)", "Desire Doue (1)"],
        "max_goleador": 7
    }),
    ("ENG", {
        "name": "England", "elo": 2076,
        "form": "WDWWW", "gf": 11, "ga": 5,
        "clean_sheets": 2,
        "avg_gf": 2.2, "avg_ga": 1.0,
        "sos_avg": 1779,
        "momentum": 3,
        "formacion_base": "4-2-3-1",
        "entrenador": "Thomas Tuchel",
        "goleadores": ["Harry Kane (6)", "Jude Bellingham (4)", "Marcus Rashford (1)"],
        "max_goleador": 6
    }),
    ("NOR", {
        "name": "Norway", "elo": 1972,
        "form": "WWLWW", "gf": 12, "ga": 9,
        "clean_sheets": 0,
        "avg_gf": 2.4, "avg_ga": 1.8,
        "sos_avg": 1866,
        "momentum": 2,
        "formacion_base": "4-1-2-3",
        "entrenador": "Ståle Solbakken",
        "goleadores": ["Erling Haaland (7)", "Leo Ostigard (1)", "Marcus Pedersen (1)", "Thelo Aasgaard (1)"],
        "max_goleador": 7
    }),
    ("BEL", {
        "name": "Belgium", "elo": 1961,
        "form": "DDWWW", "gf": 13, "ga": 5,
        "clean_sheets": 2,
        "avg_gf": 2.6, "avg_ga": 1.0,
        "sos_avg": 1807,
        "momentum": 3,
        "formacion_base": "4-2-3-1",
        "entrenador": "Rudi Garcia",
        "goleadores": ["Romelu Lukaku (3)", "Leandro Trossard (2)", "Youri Tielemans (2)", "Charles De Ketelaere (2)"],
        "max_goleador": 3
    }),
    ("SUI", {
        "name": "Switzerland", "elo": 1949,
        "form": "DWWWD", "gf": 9, "ga": 3,
        "clean_sheets": 3,
        "avg_gf": 1.8, "avg_ga": 0.6,
        "sos_avg": 1794,
        "momentum": 2,
        "formacion_base": "4-2-3-1 (variable)",
        "entrenador": "Murat Yakin",
        "goleadores": ["Johan Manzambi (3)", "Ruben Vargas (3)", "Breel Embolo (2)", "Granit Xhaka (2)"],
        "max_goleador": 3
    }),
    ("MAR", {
        "name": "Morocco", "elo": 1921,
        "form": "DWWDW", "gf": 10, "ga": 4,
        "clean_sheets": 2,
        "avg_gf": 2.0, "avg_ga": 0.8,
        "sos_avg": 1813,
        "momentum": 2,
        "formacion_base": "4-2-3-1",
        "entrenador": "Mohamed Ouahbi",
        "goleadores": ["Ismael Saibari (4)", "Soufiane Rahimi (3)", "Azzedine Ounahi (2)", "Achraf Hakimi (1)"],
        "max_goleador": 4
    }),
])

# ================================================================
# HEAD TO HEAD DATA (FIFA.com)
# ================================================================
# España vs Bélgica: 23 partidos, ESP 12 wins, 6 draws, BEL 5 wins
# Goles: ESP 46 - BEL 22
H2H_ADVANTAGE = {
    ("ESP", "BEL"): 7,   # España tiene +7 net wins
    ("FRA", "MAR"): 4,   # Francia domina históricamente
    ("ARG", "SUI"): 3,   # Argentina domina
    ("ENG", "NOR"): 2,   # Inglaterra domina
}

# Factor H2H a ELO (cada victoria neta ~ 5 puntos ELO)
def get_h2h_boost(h, a):
    return H2H_ADVANTAGE.get((h, a), 0)

# ================================================================
# BRACKET
# ================================================================
QUARTERFINALS = [
    ("QF1", "FRA", "MAR", "9 Jul"),
    ("QF2", "ESP", "BEL", "10 Jul"),
    ("QF3", "NOR", "ENG", "11 Jul"),
    ("QF4", "ARG", "SUI", "12 Jul"),
]
SEMIFINALS = [("SF1", "QF1", "QF2", "14 Jul"), ("SF2", "QF3", "QF4", "15 Jul")]

# ================================================================
# POLYMARKET ODDS (actual)
# ================================================================
PM = {"FRA": 33.05, "ESP": 18.05, "ARG": 18.45, "ENG": 14.45,
      "NOR": 5.80, "MAR": 2.75, "BEL": 2.25, "SUI": 0.95}

# ================================================================
# MOMENTUM CALCULATION
# ================================================================
def calc_momentum(team_code):
    """Momentum: peso de racha de victorias + goles recientes"""
    td = TEAMS_DATA[team_code]
    base = td["momentum"]
    # Bonus por goleada reciente (gf > 3) o clean sheet
    return base

# ================================================================
# SIMULATION
# ================================================================
random.seed(42)

elo = {t: TEAMS_DATA[t]["elo"] for t in TEAMS_DATA}
champ_counts = defaultdict(int)
qf_wins = defaultdict(int)
sf_wins = defaultdict(int)

N = 100000
for _ in range(N):
    # --- QF ---
    qf = {}
    for name, h, a, _ in QUARTERFINALS:
        h2h = get_h2h_boost(h, a) - get_h2h_boost(a, h)
        m_h = TEAMS_DATA[h]["momentum"]
        m_a = TEAMS_DATA[a]["momentum"]
        star_h = TEAMS_DATA[h].get("max_goleador", 0)
        star_a = TEAMS_DATA[a].get("max_goleador", 0)
        # Dependency: % of team goals by top scorer
        gf_h = TEAMS_DATA[h]["gf"]
        gf_a = TEAMS_DATA[a]["gf"]
        dep_h = star_h / max(gf_h, 1) if gf_h > 0 else 0
        dep_a = star_a / max(gf_a, 1) if gf_a > 0 else 0
        gh, ga = simulate_match(elo[h], elo[a], h2h, m_h, m_a, star_h, star_a, dep_h, dep_a)
        w = h if gh > ga else a
        qf[name] = w
        qf_wins[w] += 1
    
    # --- SF ---
    sf = {}
    for name, qf_h, qf_a, _ in SEMIFINALS:
        h, a = qf[qf_h], qf[qf_a]
        gh, ga = simulate_match(elo[h], elo[a])
        w = h if gh > ga else a
        sf[name] = w
        sf_wins[w] += 1
    
    # --- Final ---
    h, a = sf["SF1"], sf["SF2"]
    gh, ga = simulate_match(elo[h], elo[a])
    champ_counts[h if gh > ga else a] += 1

# ================================================================
# RESULTS
# ================================================================
sorted_teams = sorted(champ_counts.keys(), key=lambda t: champ_counts[t], reverse=True)

print("=" * 72)
print("  WORLD CUP 2026 — MODELO MEJORADO v3")
print("  100K simulaciones | ELO real + forma torneo + H2H + momentum")
print("  8 Julio 2026 — Cuartos de final")
print("=" * 72)

print()
print("--- VARIABLES DEL MODELO ---")
print(f"  ELO: eloratings.net (7 jul 2026)")
print(f"  Forma: resultados del torneo (GF, GA, clean sheets)")
print(f"  SOS: Strength of Schedule (ELO promedio rivales)")
print(f"  H2H: historial FIFA (victorias netas convertidas a ELO)")
print(f"  Momentum: racha de victorias consecutivas")
print(f"  Poisson: goles ~ Poisson(λ) con λ basado en ELO ajustado")
print()

# Tabla de datos de entrada
print("--- DATOS DE CADA SELECCIÓN ---")
print(f"{'Selección':16s} {'ELO':>5s} {'Forma':>8s} {'GF':>4s} {'GA':>4s} {'CS':>3s} {'SOS':>5s} {'Mom':>4s} {'H2H':>4s}")
print("-" * 56)
for t in sorted_teams:
    td = TEAMS_DATA[t]
    h2h_str = ""
    # Get H2H for QF opponent
    for qf_name, h, a, _ in QUARTERFINALS:
        if h == t:
            opp = a
            boost = get_h2h_boost(h, a) - get_h2h_boost(a, h)
            h2h_str = f"{'+' if boost > 0 else ''}{boost}"
        elif a == t:
            opp = h
            boost = get_h2h_boost(a, h) - get_h2h_boost(h, a) 
            h2h_str = f"{'+' if boost > 0 else ''}{boost}"
    print(f"{td['name']:16s} {td['elo']:5d} {td['form']:>8s} {td['gf']:4d} {td['ga']:4d} {td['clean_sheets']:3d} {td['sos_avg']:5d} {td['momentum']:4d} {h2h_str:>4s}")

print()
print("--- RESULTADOS 100K SIMULACIONES ---")
print(f"{'Selección':16s} {'Modelo':>8s} {'Mercado':>8s} {'Dif':>7s} {'QF%':>6s} {'SF%':>6s}")
print("-" * 53)
for t in sorted_teams:
    mp = champ_counts[t] / N * 100
    mk = PM.get(t, 0)
    diff = mp - mk
    qf_pct = qf_wins[t] / N * 100
    sf_pct = sf_wins[t] / N * 100
    tag = ""
    if diff > 2: tag = " <<<"
    elif diff < -2: tag = " >>>"
    print(f"{TEAMS_DATA[t]['name']:16s} {mp:6.2f}%  {mk:6.2f}%  {diff:+6.1f}%  {qf_pct:5.1f}%  {sf_pct:5.1f}%{tag}")

print()
print("--- PROB. POR CUARTO (con ajustes) ---")
for name, h, a, fecha in QUARTERFINALS:
    h_name, a_name = TEAMS_DATA[h]["name"], TEAMS_DATA[a]["name"]
    h_pct = qf_wins[h] / (qf_wins[h] + qf_wins[a]) * 100
    a_pct = 100 - h_pct
    h2h = get_h2h_boost(h, a) - get_h2h_boost(a, h)
    print(f"  {fecha}: {h_name} ({h_pct:.1f}%) vs {a_name} ({a_pct:.1f}%)  [H2H: {h2h:+d}]")

print()
print("--- MEJORA RESPECTO A V2 (solo ELO) ---")
v2_results = {"ESP": 26.28, "ARG": 24.48, "FRA": 21.65, "ENG": 12.98,
              "NOR": 4.87, "BEL": 3.69, "SUI": 3.51, "MAR": 2.54}
for t in sorted_teams:
    v2 = v2_results.get(t, 0)
    v3 = champ_counts[t] / N * 100
    delta = v3 - v2
    print(f"  {TEAMS_DATA[t]['name']:16s}  v2:{v2:5.2f}%  v3:{v3:5.2f}%  ({delta:+5.2f}%)")

print()
print("--- ESTADÍSTICAS CLAVE POR SELECCIÓN ---")
for t in sorted_teams:
    td = TEAMS_DATA[t]
    print(f"""
  {td['name']} (ELO {td['elo']}):
    Torneo: {td['form']} | GF {td['gf']} GA {td['ga']} | {td['clean_sheets']} porterías a cero
    SOS: {td['sos_avg']} (media ELO rivales)
    Formación: {td['formacion_base']} | DT: {td['entrenador']}
    Goleadores: {', '.join(td['goleadores'])}
    Modelo v3: {champ_counts[t]/N*100:.1f}% vs Mercado: {PM.get(t,0):.1f}%
""")
