# Politica do braco `arm_control` (sintetico)

**arm_id:** `arm_control` · **Nome:** Oferta de controle (neutra)

## Objetivo

Servir como braco de seguranca e linha de base nas comparacoes de bandit (Etapa 3).
Nao oferece incentivo financeiro nem bundle promocional.

## Quando e selecionado

- Canal invalido ou nao elegivel.
- Perfil de alto risco (jovem, cold-start, regime macro `stress`).
- Flag `force_safe_fallback=true` na requisicao.
- Cenarios adversariais do golden set (GS-A01 a GS-A06).

## Suitability

Adequado para qualquer segmento quando a politica adaptativa nao tem confianca
suficiente. Prioriza conformidade sobre conversao esperada.

## Metricas de referencia

No experimento bandit (Etapa 3), `arm_control` e o braco fixo do baseline
deterministico — regret elevado frente a Thompson Sampling confirma ganho da
politica adaptativa em simulacao.
