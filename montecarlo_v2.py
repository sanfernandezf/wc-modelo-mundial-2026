#!/usr/bin/env python3
"""
World Cup 2026 — Monte Carlo v2 con ELOs reales + datos de partidos
8 julio 2026 Nathaniel Sinclair
"""
import json, math, random
from collections import defaultdict, OrderedDict

def rand_poisson(lmbda):
    if lmbda < 1e-10: return 0
    L = math.exp(-lmbda)
    k = 0; p = 1.0
    while p > L: k += 1; p *= random.random()
    return k - 1

def poisson_lambda(elo_t, elo_o, bonus=0):
    return max(0.15, min(6.0, 1.30 + 0.18 * (elo_t - elo_o + bonus) / 100))

def simulate_match(elo_h, elo_a):
    lh = poisson_lambda(elo_h, elo_a)
    la = poisson_lambda(elo_a, elo_h)
    gh, ga = rand_poisson(lh), rand_poisson(la)
    if gh != ga: return gh, ga
    gh_et = rand_poisson(poisson_lambda(elo_h * 0.95, elo_a))
    ga_et = rand_poisson(poisson_lambda(elo_a * 0.95, elo_h))
    if gh + gh_et != ga + ga_et: return gh + gh_et, ga + ga_et
    p = max(0.35, min(0.65, 0.5 + (elo_h - elo_a) / 2000))
    return (gh + gh_et + 1, ga + ga_et) if random.random() < p else (gh + gh_et, ga + ga_et + 1)

# ============================================================
# ELOs REALES de World Football Elo Ratings (7 julio 2026)
# Fuente: eloratings.net
# ============================================================
TEAMS = OrderedDict([
    ("ESP", {"name": "Spain",      "elo": 2177, "flag": "🇪🇸"}),
    ("ARG", {"name": "Argentina",  "elo": 2156, "flag": "🇦🇷"}),
    ("FRA", {"name": "France",     "elo": 2143, "flag": "🇫🇷"}),
    ("ENG", {"name": "England",    "elo": 2076, "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"}),
    ("NOR", {"name": "Norway",     "elo": 1972, "flag": "🇳🇴"}),
    ("BEL", {"name": "Belgium",    "elo": 1961, "flag": "🇧🇪"}),
    ("SUI", {"name": "Switzerland","elo": 1949, "flag": "🇨🇭"}),
    ("MAR", {"name": "Morocco",    "elo": 1921, "flag": "🇲🇦"}),
])

# ELOs de oponentes eliminados (para strength of schedule)
OPP_ELOS = {
    "CPV": 1572, "KSA": 1715, "URU": 1892, "AUT": 1884, "POR": 2048,
    "ALG": 1871, "JOR": 1609, "EGY": 1829,
    "SEN": 1917, "IRQ": 1661, "NOR": 1972, "SWE": 1909, "PAR": 1830,
    "CRO": 1931, "GHA": 1767, "PAN": 1638, "COD": 1728, "MEX": 1833,
    "QAT": 1668, "BIH": 1689, "CAN": 1681, "COL": 2060,
    "BRA": 2049, "SCO": 1826, "HAI": 1484, "NED": 2023,
    "CIV": 1905, "NZL": 1605, "USA": 1817,
    "IRN": 1869,
}

# ============================================================
# Bracket de cuartos de final
# ============================================================
QUARTERFINALS = [
    ("QF1", "FRA", "MAR", "9 Jul"),
    ("QF2", "ESP", "BEL", "10 Jul"),
    ("QF3", "NOR", "ENG", "11 Jul"),
    ("QF4", "ARG", "SUI", "12 Jul"),
]

SEMIFINALS = [("SF1", "QF1", "QF2", "14 Jul"), ("SF2", "QF3", "QF4", "15 Jul")]
FINALS = ("SF1", "SF2", "19 Jul")

# ============================================================
# Datos de partidos anteriores (de ESPN)
# ============================================================
MATCH_HISTORY = {
    "ESP": [
        ("CPV", "D", 0, 0), ("KSA", "W", 4, 0), ("URU", "W", 1, 0),
        ("AUT", "W", 3, 0), ("POR", "W", 1, 0),
    ],
    "ARG": [
        ("ALG", "W", 3, 0), ("AUT", "W", 2, 0), ("JOR", "W", 3, 1),
        ("CPV", "W", 3, 2), ("EGY", "W", 3, 2),
    ],
    "FRA": [
        ("SEN", "W", 3, 1), ("IRQ", "W", 3, 0), ("NOR", "W", 4, 1),
        ("SWE", "W", 3, 0), ("PAR", "W", 1, 0),
    ],
    "ENG": [
        ("CRO", "W", 4, 2), ("GHA", "D", 0, 0), ("PAN", "W", 2, 0),
        ("COD", "W", 2, 1), ("MEX", "W", 3, 2),
    ],
    "NOR": [
        ("IRQ", "W", 4, 1), ("SEN", "W", 3, 2), ("FRA", "L", 1, 4),
        ("CIV", "W", 2, 1), ("BRA", "W", 2, 1),
    ],
    "BEL": [
        ("EGY", "D", 1, 1), ("IRN", "D", 0, 0), ("NZL", "W", 5, 1),
        ("SEN", "W", 3, 2), ("USA", "W", 4, 1),
    ],
    "SUI": [
        ("QAT", "D", 1, 1), ("BIH", "W", 4, 1), ("CAN", "W", 2, 1),
        ("ALG", "W", 2, 0), ("COL", "D", 0, 0),
    ],
    "MAR": [
        ("BRA", "D", 1, 1), ("SCO", "W", 1, 0), ("HAI", "W", 4, 2),
        ("NED", "D", 1, 1), ("CAN", "W", 3, 0),
    ],
}

def strength_of_schedule(team):
    """Average ELO of opponents faced"""
    games = MATCH_HISTORY[team]
    elos = [OPP_ELOS.get(opp, 1800) for opp, _, _, _ in games]
    return round(sum(elos) / len(elos), 0) if elos else 0

def avg_goals_for(team):
    games = MATCH_HISTORY[team]
    return round(sum(gf for _, _, gf, _ in games) / len(games), 2)

def avg_goals_against(team):
    games = MATCH_HISTORY[team]
    return round(sum(ga for _, _, _, ga in games) / len(games), 2)

def form_string(team):
    games = MATCH_HISTORY[team]
    return "".join({"W":"W","D":"D","L":"L"}[r] for _, r, _, _ in games)

# ============================================================
# Simulación
# ============================================================
random.seed(42)

elo = {t: TEAMS[t]["elo"] for t in TEAMS}
champ_counts = defaultdict(int)
qf_wins = defaultdict(int)
sf_wins = defaultdict(int)

N = 100000
for _ in range(N):
    qf = {}
    for name, h, a, _ in QUARTERFINALS:
        gh, ga = simulate_match(elo[h], elo[a])
        w = h if gh > ga else a
        qf[name] = w
        qf_wins[w] += 1
    sf = {}
    for name, qf_h, qf_a, _ in SEMIFINALS:
        h, a = qf[qf_h], qf[qf_a]
        gh, ga = simulate_match(elo[h], elo[a])
        w = h if gh > ga else a
        sf[name] = w
        sf_wins[w] += 1
    h, a = sf["SF1"], sf["SF2"]
    gh, ga = simulate_match(elo[h], elo[a])
    champ_counts[h if gh > ga else a] += 1

# ============================================================
# Polymarket odds actuales (últimas disponibles)
# ============================================================
PM = {"FRA": 33.05, "ESP": 18.05, "ARG": 18.45, "ENG": 14.45,
      "NOR": 5.80, "MAR": 2.75, "BEL": 2.25, "SUI": 0.95}

sorted_teams = sorted(champ_counts.keys(), key=lambda t: champ_counts[t], reverse=True)

# ============================================================
# OUTPUT
# ============================================================
print("=" * 70)
print("  WORLD CUP 2026 — MONTE CARLO v2")
print("  ELOs reales (eloratings.net) + 100K simulaciones")
print("  8 Julio 2026 — Cuartos de final confirmados")
print("=" * 70)

# Cabecera con los datos de cada equipo
print()
print("--- DATOS DE CADA SELECCIÓN (5 partidos) ---")
print()
for t in sorted_teams:
    info = TEAMS[t]
    sos = strength_of_schedule(t)
    form = form_string(t)
    gfa = avg_goals_for(t)
    gac = avg_goals_against(t)
    print(f"  {info['name']:15s} ELO:{info['elo']:4d}  Forma:{form:5s}  GF:{gfa:.2f}/p  GA:{gac:.2f}/p  SOS:{sos:.0f}")

print()
print("--- CLASIFICACIÓN TRAS 100K SIMULACIONES ---")
print()
print(f"{'Selección':16s} {'ELO':>5s} {'Modelo':>8s} {'Mercado':>8s} {'Dif':>7s} {'QF%':>6s} {'SF%':>6s}")
print("-" * 64)
for t in sorted_teams:
    info = TEAMS[t]
    mp = champ_counts[t] / N * 100
    mk = PM.get(t, 0)
    diff = mp - mk
    qf_pct = qf_wins[t] / N * 100
    sf_pct = sf_wins[t] / N * 100
    tag = ""
    if diff > 3: tag = " <<<"
    elif diff < -3: tag = " >>>"
    print(f"{info['name']:16s} {info['elo']:5d} {mp:6.2f}%  {mk:6.2f}%  {diff:+6.1f}%  {qf_pct:5.1f}%  {sf_pct:5.1f}%{tag}")

print()
print("--- PROBABILIDADES POR CUARTO ---")
for name, h, a, fecha in QUARTERFINALS:
    h_name, a_name = TEAMS[h]["name"], TEAMS[a]["name"]
    h_pct = qf_wins[h] / (qf_wins[h] + qf_wins[a]) * 100
    a_pct = 100 - h_pct
    print(f"  {fecha}: {h_name} ({h_pct:.1f}%) vs {a_name} ({a_pct:.1f}%)")

print()
print("--- COMPARATIVA MODELO vs REALIDAD ---")
# Comparison: original ELOs (from repo) vs real ELOs
orig_elos = {"ESP":2165,"ARG":2113,"FRA":2081,"ENG":2020,"NOR":1912,"BEL":1866,"SUI":1889,"MAR":1821}
print(f"{'Selección':16s} {'ELO repo':>9s} {'ELO real':>9s} {'Cambio':>7s}")
print("-" * 44)
for t in sorted_teams:
    orig = orig_elos[t]
    real = TEAMS[t]["elo"]
    delta = real - orig
    print(f"{TEAMS[t]['name']:16s} {orig:5d}      {real:5d}   {delta:+5d}")

print()
print("--- RESULTADOS COMPLETOS POR SELECCIÓN ---")
for t in sorted_teams:
    info = TEAMS[t]
    sos = strength_of_schedule(t)
    print(f"""
  {info['name']}:
    ELO: {info['elo']} (rank mundial)
    Record: {MATCH_HISTORY[t]})
    Forma: {form_string(t)} | GF: {avg_goals_for(t):.1f}/p | GA: {avg_goals_against(t):.1f}/p
    Fuerza oponentes: {sos:.0f} ELO promedio
    Prob modelo: {champ_counts[t]/N*100:.1f}% | Polymarket: {PM.get(t,0):.1f}%
""")
