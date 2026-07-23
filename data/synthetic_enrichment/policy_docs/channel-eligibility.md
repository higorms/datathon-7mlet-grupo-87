# Elegibilidade de canal (sintetico)

**Versao:** `policy-synth-v1`

## Canais permitidos para decisao automatizada

| Canal | Elegivel | Acao em caso de uso |
| --- | --- | --- |
| `cellular` | Sim | Politica contextual completa |
| `telephone` | Sim | Politica contextual completa |
| `email` | Nao | `SAFE_FALLBACK_INVALID_CHANNEL` → `arm_control` |
| `unknown` | Nao | `SAFE_FALLBACK_INVALID_CHANNEL` → `arm_control` |

## Justificativa

Canais digitais assincronos (`email`) nao possuem confirmacao imediata de adequacao
no cenario sintetico. O fallback para `arm_control` evita exposicao indevida a
incentivos financeiros.

## Reason codes associados

- `SAFE_FALLBACK_INVALID_CHANNEL`: canal fora da lista permitida.
- `SAFE_FALLBACK_FORCED`: operador forcou fallback via `force_safe_fallback=true`.
- `SAFE_FALLBACK_HIGH_RISK`: jovem + cold-start + macro `stress`.
