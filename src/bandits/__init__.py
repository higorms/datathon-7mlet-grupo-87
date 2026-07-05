"""Etapa 3 - Baseline e estrategia algoritmica (multi-armed bandit).

Modulos:
    policies    - politicas: baseline fixo, epsilon-greedy, UCB1 (familia Nilos-UCB)
                  e Thompson Sampling (Beta-Bernoulli).
    environment - ambiente Bernoulli estacionario com recompensa-verdade derivada do
                  catalogo sintetico (Etapa 2) e modelo de recompensa atrasada.
    simulation  - laco de simulacao com feedback atrasado e cold-start; calcula
                  recompensa, regret, exploracao e conversao por rodada/semente.
    experiment  - orquestrador CLI: compara as politicas e gera relatorio + figuras.
"""
