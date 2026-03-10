# Bedrock Foundation Labs

This folder contains foundation-level Bedrock labs and reusable patterns.

## Modules

- `embeddings/`: embedding generation and vector-ready pipelines.
- `Generation/`: baseline text generation examples.
- `multimodal-llms/`: image/video/text multimodal examples.
- `RAG/`: retrieval-augmented generation patterns.
  - `enterprise/`: full-stack production-ready RAG solutions.
- `Agents/`: Bedrock Agents starter patterns.
  - `enterprise/`: multi-agent systems and industry templates.
- `bedrock-flows/`: orchestration flow examples.
- `prompt-router/`: prompt routing and model selection patterns.
- `Fine-Tuning/`: model customization examples.
  - `enterprise/`: distributed training and QLoRA workflows.
- `AI-Image-Generation/`: image generation workflows.
- `infrastructure/`: production IaC stacks (CDK/Terraform).

## Who Should Use This

- Teams creating a technical baseline before building demos or production stacks.
- Engineers validating model behavior and Bedrock API integration paths.

## Suggested Execution Order

1. Start with `embeddings/` and `Generation/`.
2. Move to `RAG/` and `prompt-router/`.
3. Validate orchestration in `bedrock-flows/` and `Agents/`.
4. Extend into multimodal and fine-tuning modules.

## Production Promotion Criteria

- Reproducible environment setup.
- Config-driven model IDs or inference profile ARNs.
- Guardrail and IAM policy baseline in place.
- Observability hooks integrated.

See `../../../../docs/aws/bedrock-foundation-model-guide.md` for current model-access and inference-profile guidance.
