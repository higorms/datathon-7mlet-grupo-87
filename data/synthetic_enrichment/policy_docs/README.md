# Documentos sinteticos de politica comercial (RAG)

Politicas **ficticias** para o assistente com LLM da plataforma. Nao representam
regras reais de nenhuma instituicao financeira. Servem como corpus de recuperacao
(Azure AI Search) na arquitetura-alvo da Etapa 6.

| Arquivo | Conteudo |
| --- | --- |
| [`suitability-guidelines.md`](suitability-guidelines.md) | Diretrizes gerais de adequacao (suitability) |
| [`channel-eligibility.md`](channel-eligibility.md) | Canais elegiveis e fallbacks |
| [`offer-arm-control.md`](offer-arm-control.md) | Braço de controle (sem incentivo) |
| [`offer-arm-rate-boost.md`](offer-arm-rate-boost.md) | Taxa bonificada e restricoes |
| [`offer-arm-retention-plus.md`](offer-arm-retention-plus.md) | Retencao consultiva |

Indexacao alvo: Azure AI Search (`policy-suitability`) — ver [`docs/architecture-azure.md`](../../../docs/architecture-azure.md).
