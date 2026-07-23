# Gravação de Demo — Contingência

> Template para documentar a gravação de backup da demonstração ao vivo.
> Preencher antes do Demo Day.

| Campo | Valor |
| --- | --- |
| **Data da gravação** | _A preencher_ |
| **Duração** | ~3 min |
| **Arquivo** | _A preencher (ex.: `demo-recording.mp4` ou link externo)_ |
| **SHA-256** | _A preencher após gerar o arquivo_ |
| **Cenários cobertos** | GS-T01 (típico), GS-A03 (alto risco), GS-A04 (suitability) + auditoria |

## Instruções

1. Executar os cenários documentados em [`docs/demo-plan.md`](../demo-plan.md).
2. Gravar a tela com `asciinema`, OBS ou gravador nativo.
3. Calcular hash: `sha256sum demo-recording.mp4`.
4. Preencher a tabela acima e commitar este arquivo.

## Comandos da gravação

Ver [`docs/demo-plan.md`](../demo-plan.md) §3 para os curls exatos dos 3 cenários.
