#!/usr/bin/env python3
"""
CALIBRACIÓN DEL MODELO POISSON contra datos históricos (2018, 2022)
Una vez que el subagente genere historical_calibration_data.json,
esto prueba todas las combinaciones de parámetros y encuentra la óptima.
"""
import json, math, random
from collections import defaultdict

def rand_poisson(lmbda):
    if lmbda < 1e-10: return 0
    L = math.exp(-lmbda)
    k = 0; p = 1.0
    while p > L: k += 1; p *= random.random()
    return k - 1

def expected_goals(elo_t, elo_o, base, slope):
    """Goles esperados según Elo"""
    return max(0.15, min(6.0, base + slope * (elo_t - elo_o) / 100))

def simulate_match_with_params(elo_h, elo_a, base, slope):
    lh = expected_goals(elo_h, elo_a, base, slope)
    la = expected_goals(elo_a, elo_h, base, slope)
    gh, ga = rand_poisson(lh), rand_poisson(la)
    if gh != ga: return gh, ga
    # Extra time (fatiga 5%)
    gh_et = rand_poisson(expected_goals(elo_h * 0.95, elo_a, base * 0.9, slope))
    ga_et = rand_poisson(expected_goals(elo_a * 0.95, elo_h, base * 0.9, slope))
    if gh + gh_et != ga + ga_et: return gh + gh_et, ga + ga_et
    # Penales (~50%, leve sesgo ELO)
    p = 0.5 + (elo_h - elo_a) / 2000
    return (gh + gh_et + 1, ga + ga_et) if random.random() < p else (gh + gh_et, ga + ga_et + 1)

def calibrate():
    """Prueba todas las combinaciones de parámetros"""
    with open('/home/santi/wc_model/historical_calibration_data.json') as f:
        data = json.load(f)
    
    matches = data.get('matches', [])
    print(f"Partidos de calibración: {len(matches)}")
    print(f"Rangos: {data.get('ranges', {})}")
    print()
    
    # Grid search: base y pendiente
    best_acc = 0
    best_params = {}
    results = []
    
    for base_int in range(5, 21):        # 0.5 a 2.0
        for slope_int in range(5, 31, 2): # 0.05 a 0.30
            base = base_int / 10.0
            slope = slope_int / 100.0
            
            correct = 0
            total = 0
            total_abs_error = 0
            
            random.seed(42)
            for m in matches:
                elo_h = m['elo_pre_tournament']['home']
                elo_a = m['elo_pre_tournament']['away']
                actual_h = m['score']['home']
                actual_a = m['score']['away']
                
                # Simular N veces para tener probabilidad
                sims = 1000
                h_wins = 0
                for _ in range(sims):
                    gh, ga = simulate_match_with_params(elo_h, elo_a, base, slope)
                    if gh > ga: h_wins += 1
                
                # El modelo predice que gana el equipo con más wins en sims
                pred_h_wins = h_wins > sims / 2
                actual_h_wins = actual_h > actual_a
                
                if pred_h_wins == actual_h_wins:
                    correct += 1
                total += 1
            
            acc = correct / total * 100 if total > 0 else 0
            results.append((base, slope, acc))
            
            if acc > best_acc:
                best_acc = acc
                best_params = {'base': base, 'slope': slope}
    
    # Mostrar top 10
    results.sort(key=lambda x: -x[2])
    print("TOP 10 COMBINACIONES (base, pendiente, accuracy):")
    print("Base  Pendiente  Accuracy")
    for base, slope, acc in results[:10]:
        arrow = " <<<" if (base == best_params['base'] and slope == best_params['slope']) else ""
        print(f"{base:4.1f}   {slope:.2f}     {acc:5.1f}%{arrow}")
    
    print(f"\nMEJOR: base={best_params['base']}, pendiente={best_params['slope']} -> {best_acc:.1f}% accuracy")
    
    # Baseline: siempre favorito ELO gana
    elo_correct = 0
    for m in matches:
        elo_fav = m['elo_pre_tournament']['home'] >= m['elo_pre_tournament']['away']
        actual_h_wins = m['score']['home'] > m['score']['away']
        if elo_fav == actual_h_wins:
            elo_correct += 1
    elo_acc = elo_correct / len(matches) * 100
    print(f"Baseline (solo favorito ELO gana): {elo_acc:.1f}%")
    print(f"Mejora del modelo: {best_acc - elo_acc:+.1f}%")
    
    # Guardar mejores parámetros
    with open('/home/santi/wc_model/best_params.json', 'w') as f:
        json.dump(best_params, f, indent=2)
    print(f"\nParámetros guardados en best_params.json")
    
    return best_params

if __name__ == '__main__':
    calibrate()
