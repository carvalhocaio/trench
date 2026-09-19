# Trench Web

Interface web do Trench, construída com Next.js 16 (App Router), React 19, TypeScript e Tailwind v4.

O acesso à API do backend (FastAPI) acontece somente no servidor: Server Components para leitura e Server Actions para escrita. O navegador nunca chama o FastAPI diretamente, então não há necessidade de CORS.

## Desenvolvimento

Com o backend rodando (`make run` na raiz do repositório):

```bash
pnpm install
pnpm dev
```

Configure `web/.env.local` a partir de `web/.env.example` se a API não estiver em `http://localhost:8000`.

## Scripts

- `pnpm dev` — inicia o servidor de desenvolvimento.
- `pnpm build` — build de produção.
- `pnpm lint` — checa o código com eslint.
- `pnpm typecheck` — gera os tipos de rota do Next.js e roda o `tsc`.
- `pnpm test` — roda os testes com Vitest.
- `pnpm run types` — regenera `src/lib/api/schema.d.ts` a partir de `openapi.json` (gerado com `make web-types` na raiz do repositório).

## Autenticação

Não há autenticação: o uso é local, restrito à rede da equipe.
