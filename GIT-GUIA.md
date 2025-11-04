Objetivo

- Te guiar, passo a passo, para usar Git com segurança e eficiência no IABANK, com explicações práticas, analogias simples e exemplos de comandos prontos para copiar.

Visão Geral

- Git é um “controle de versão” que guarda o histórico do seu código como fotos no tempo, permite trabalhar em paralelo com “ramificações” (branches) e colaborar sem medo de perder trabalho. (Analogia: um caderno com múltiplas vias e um “desfazer infinito”; Exemplo: voltar seu código para como estava ontem com `git checkout`/`git restore`.)

Setup Inicial

- Configure sua identidade e dicas de cor: `git config --global user.name "Seu Nome"` e `git config --global user.email "voce@exemplo.com"`; `git config --global color.ui auto` (Analogia: assinar cada página do caderno; Exemplo: commits mostram seu nome correto.)
- Use os comandos modernos: `git switch` (trocar/criar branch) e `git restore` (reverter arquivos) no lugar do antigo `git checkout`. (Analogia: botões separados no elevador; Exemplo: `git switch -c feat/minha-feature`.)
- Alias útil de histórico: `git config --global alias.lg "log --oneline --decorate --graph --all"` (Analogia: mapa do metrô do seu histórico; Exemplo: `git lg` para ver branches e merges.)

Conceitos-Chave

- Working directory, Staging (index), Commit: você edita → seleciona mudanças → tira a “foto”. (Analogia: preparar ingredientes, montar na bandeja, assar; Exemplo: `git add arquivo.py` → `git commit -m "feat: nova rota"`.)
- Branch: uma linha do tempo paralela para uma tarefa. (Analogia: realidade alternativa temporária; Exemplo: `git switch -c feat/autenticacao`.)
- Remote: cópia do repositório hospedada (GitHub/GitLab). (Analogia: backup/servidor central; Exemplo: `git push origin feat/autenticacao`.)
- HEAD: ponteiro para “onde você está”. (Analogia: marcador de página; Exemplo: `git show HEAD` para ver o último commit.)

Fluxo Recomendado (GitHub Flow enxuto)

- Sempre trabalhe em branches curtas a partir de `main`; abra PR e faça merge/squash após review. (Analogia: pequenas entregas em esteira; Exemplo: `git switch main && git pull && git switch -c feat/contas-listar`.)
- Atualize sua branch com `main` antes de abrir PR: `git fetch origin && git rebase origin/main` (ou `git merge origin/main`). (Analogia: sincronizar relógio antes da reunião; Exemplo: resolve conflitos antes do review.)

Commits de Qualidade

- Pequeninos e focados; mensagem clara usando Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:` etc. (Analogia: notas de rodapé organizadas; Exemplo: `fix: corrige validação de CPF no serializer`.)
- Commits fixup: `git commit --fixup <hash>` + `git rebase -i --autosquash origin/main` para “colar” correções no commit original. (Analogia: post-it que se junta à página certa; Exemplo: limpar o histórico antes do merge.)

Branches (criar, trocar, limpar)

- Criar: `git switch -c feat/usuarios-busca` (Analogia: abrir uma nova trilha; Exemplo: iniciar uma feature isolada.)
- Trocar: `git switch main` (Analogia: mudar de trilho; Exemplo: revisar hotfix.)
- Apagar após merge: `git branch -d feat/usuarios-busca` (ou `-D` se necessário). (Analogia: jogar fora um rascunho usado; Exemplo: evitar bagunça de branches antigas.)

Sincronização (fetch, pull, push)

- Buscar sem mudar arquivos: `git fetch` (Analogia: puxar notificações; Exemplo: ver o que mudou no remoto.)
- Atualizar branch local: `git pull --rebase` (preferível para histórico linear). (Analogia: encaixar suas mudanças no fim da fila; Exemplo: minimizar merges “ruidosos”.)
- Enviar sua branch: `git push -u origin feat/usuarios-busca` (Analogia: subir arquivo para o Drive; Exemplo: abrir PR.)

Merge vs Rebase

- Merge preserva histórico “ramificado”: `git merge origin/main` (Analogia: juntar duas estradas com um entroncamento; Exemplo: PR com vários commits mantidos.)
- Rebase reescreve para parecer linear: `git rebase origin/main` (Analogia: reorganizar páginas para leitura fluida; Exemplo: histórico limpo antes de abrir PR.)
- Squash merge no PR: ótimo para manter `main` com 1 commit por feature. (Analogia: comprimir um pacote; Exemplo: `feat: listar contas` vira um commit só na `main`.)

Resolver Conflitos

- Ao rebase/merge, edite arquivos com `<<<<<<<`, resolva e `git add arquivo`, depois `git rebase --continue` ou `git commit`. (Analogia: mediador juntando duas versões; Exemplo: aceitar a versão correta do `serializer`.)

Stash (guardar alterações temporariamente)

- Guardar: `git stash -u` (inclui não rastreados) e voltar limpo; restaurar: `git stash pop`. (Analogia: colocar rascunhos numa gaveta; Exemplo: pausar uma feature para resolver um hotfix.)
- Stash parcial: `git add -p` + `git stash --keep-index`. (Analogia: guardar só uma parte do material; Exemplo: separar mudanças que estão prontas.)

Restaurar e Desfazer (moderno)

- Desfazer mudanças não adicionadas: `git restore arquivo`. (Analogia: “Ctrl+Z” do arquivo; Exemplo: descartar um print de debug.)
- Tirar do staging: `git restore --staged arquivo`. (Analogia: tirar da bandeja; Exemplo: voltar ao rascunho antes do commit.)
- Reset de branch (tenha cuidado): `git reset --hard HEAD~1` remove o último commit local. (Analogia: rasgar a última página; Exemplo: apagar um commit errado feito agora.)

Segurança e Recuperação

- Reflog: `git reflog` mostra tudo que o HEAD já apontou; recuperar: `git checkout <hash>` ou `git reset --hard <hash>`. (Analogia: câmera de segurança do histórico; Exemplo: voltar de um `reset` acidental.)
- Push forçado com segurança: `git push --force-with-lease` (nunca `--force` puro). (Analogia: trocar tranca sem derrubar a porta de outros; Exemplo: após rebase da sua própria branch de PR.)

Bisect (achar bug rapidamente)

- `git bisect start`, `git bisect bad`, `git bisect good <hash-ou-tag>`, testar e marcar `good/bad` até achar o commit culpado; terminar com `git bisect reset`. (Analogia: jogo de quente/frio; Exemplo: descobrir qual commit quebrou os testes de autenticação.)

Tags e Releases

- Tag anotada: `git tag -a v1.2.0 -m "Release 1.2.0"` e `git push origin v1.2.0`. (Analogia: etiqueta de versão numa caixa; Exemplo: marcar uma release estável do backend.)
- Tags leves vs anotadas: prefira anotadas para releases. (Analogia: etiqueta com nota vs só um post-it; Exemplo: histórico com autor e mensagem da release.)

Arquivos Grandes (Git LFS)

- Use LFS para binários/imagens grandes: `git lfs install` e `git lfs track "*.png" "*.mp4"`, commit `.gitattributes`. (Analogia: guardar coisas pesadas no depósito; Exemplo: diagramas grandes em `docs/` sem inflar o repo.)
- Evite LFS para dependências compiladas; use gerenciadores de pacotes. (Analogia: não guardar material descartável no arquivo morto; Exemplo: não versionar `node_modules/`.)

Submódulos vs Subtrees

- Evite submódulos se possível; aumentam a complexidade. (Analogia: ter um mini-repo dentro de outro com chaves diferentes; Exemplo: dependências internas melhor como pacotes publicados.)
- Se precisar compartilhar código, prefira publicar biblioteca interna ou usar monorepo.

Hooks (automatizar checks)

- Pré-commit para lint/testes rápidos: via `pre-commit` ou scripts simples em `.git/hooks/pre-commit`. (Analogia: inspetor na porta; Exemplo: bloquear commit com `ruff` ou `eslint` falhando.)
- `commit-msg` para validar Conventional Commits. (Analogia: porteiro conferindo formato do bilhete; Exemplo: impedir `Update stuff` genérico.)

Histórico Limpo (fixup/autosquash)

- Marque correções: `git commit --fixup <hash>` e depois `git rebase -i --autosquash origin/main`. (Analogia: agrupar slips com o documento certo; Exemplo: juntar “corrige typo” ao commit “feat: rota contas”.)

Várias Tarefas (worktree)

- `git worktree add ../iabank-hotfix hotfix/bug-redis` para ter duas branches em pastas diferentes. (Analogia: duas mesas de trabalho; Exemplo: corrigir hotfix sem largar sua feature aberta.)

Visualizar Histórico

- Últimos commits: `git log --oneline -n 10`; um commit: `git show <hash>`; arquivos alterados: `git diff --name-only`. (Analogia: folhear o sumário; Exemplo: revisar o que será enviado no PR.)
- Gráfico: `git lg` (alias acima). (Analogia: mapa de linhas de metrô; Exemplo: entender de onde veio um merge.)

.gitignore e .gitattributes (monorepo IABANK)

- Ignore comuns:
  - Python: `__pycache__/`, `*.pyc`, `.venv/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage` (Analogia: lixo da cozinha; Exemplo: não versionar artefatos temporários.)
  - Node/Frontend: `node_modules/`, `dist/`, `.vite/`, `*.log` (Analogia: pasta de dependências baixadas; Exemplo: front React/Vite limpo.)
  - Infra/Terraform: `.terraform/`, `*.tfstate`, `*.tfstate.backup` (Analogia: arquivos de estado sensíveis; Exemplo: não expor estado no Git.)
  - IDE/SO: `.DS_Store`, `.idea/`, `.vscode/` (Analogia: preferências da sua mesa; Exemplo: cada dev tem as suas.)
- Atributos: em `.gitattributes`, `* text=auto` para normalizar quebras de linha. (Analogia: régua de formatação; Exemplo: evitar CRLF/LF bagunçando diffs.)

Trabalho Colaborativo (PRs e Reviews)

- Abra PR cedo (draft), escreva descrição clara e checklist; peça review; responda com commits pequenos. (Analogia: pedir revisão de um texto; Exemplo: “feat: listar contas (backend + contract)”.)
- Proteja `main` no remoto: exigir PR, revisões, checks verdes. (Analogia: catraca que só abre com validação; Exemplo: evitar push direto em produção.)

Rotina Diária Sugerida

- Atualize `main`: `git switch main && git pull --rebase`.
- Crie branch: `git switch -c feat/<tema-curto>`.
- Trabalhe em pequenos passos: `git add -p` e `git commit -m "feat: ..."`.
- Rebase com `main` se `main` avançar: `git fetch && git rebase origin/main`.
- Push e PR: `git push -u origin feat/<tema-curto>`; abra PR, resolva feedback; squash merge.
- Limpeza: `git switch main && git pull && git branch -d feat/<tema-curto>`.

Checklist de Segurança

- Nunca faça `git push --force` em `main`; só `--force-with-lease` e apenas na sua branch de PR. (Analogia: trava com chave; Exemplo: evitar sobrescrever trabalho de colegas.)
- Commits pequenos, mensagens claras; evite misturar refactor com feature. (Analogia: uma ideia por parágrafo; Exemplo: review mais fácil.)
- Use `git stash` e `git reflog` sem medo; são suas redes de segurança. (Analogia: salvar rascunhos e histórico de câmera; Exemplo: recuperar alterações esquecidas.)

Exemplos Concretos (IABANK)

- Criar feature de listagem de contas:
  - `git switch main && git pull --rebase`
  - `git switch -c feat/contas-listar`
  - Edite `backend/...views.py`, `frontend/.../AccountsList.tsx`
  - `git add -p && git commit -m "feat: listar contas (backend e frontend)"`
  - `git push -u origin feat/contas-listar` e abra PR (Analogia: criar, escrever, salvar, enviar para revisão; Exemplo: fluxo ponta-a-ponta.)
- Corrigir bug urgente:
  - `git switch -c fix/redis-timeout`
  - `git commit -m "fix: aumenta timeout do Redis"`
  - `git push -u origin fix/redis-timeout` e PR (Analogia: faixa expressa; Exemplo: hotfix isolado.)
- Encontrar commit que quebrou testes:
  - `git bisect start`
  - `git bisect bad` (no último commit com testes quebrados)
  - `git bisect good <hash-da-release-anterior>`
  - Rodar testes; marcar `git bisect good|bad` até identificar; `git bisect reset` (Analogia: quente/frio; Exemplo: localizar regressão.)

Cheatsheet Essencial

- Estado: `git status` (Analogia: termômetro do projeto; Exemplo: ver o que mudou.)
- Adicionar: `git add -p` (Analogia: escolher ingredientes; Exemplo: selecionar só partes prontas.)
- Commit: `git commit -m "feat: ..."` (Analogia: tirar foto; Exemplo: registrar um passo.)
- Histórico: `git lg` (Analogia: mapa; Exemplo: visualizar branches.)
- Branches: `git switch -c feat/x` / `git switch main` (Analogia: trocar de trilho; Exemplo: alternar tarefas.)
- Sincronizar: `git fetch` / `git pull --rebase` / `git push -u origin minha-branch` (Analogia: sincronizar relógio e publicar; Exemplo: subir PR.)
- Rebase/Merge: `git rebase origin/main` / `git merge origin/main` (Analogia: alinhar páginas; Exemplo: atualizar sua branch.)
- Conflitos: resolver, `git add`, `git rebase --continue` (Analogia: conciliar versões; Exemplo: finalizar integração.)
- Stash: `git stash -u` / `git stash pop` (Analogia: gaveta; Exemplo: pausar trabalho.)
- Recuperar: `git reflog` + `git reset --hard <hash>` (Analogia: câmera de segurança; Exemplo: desfazer desastre.)
- Limpar branch: `git branch -d feat/x` (Analogia: descartar rascunho; Exemplo: pós-merge.)

Se quiser, posso:
- Sugerir um `.gitignore` pronto para este monorepo.
- Criar um guia curto em `docs/git.md` com estes passos.
- Configurar hooks de pré-commit com lint/pytest/eslint.

Quando usar Spec‑Kit (ajustes importantes)

- Padrão de branch obrigatório: `NNN-nome-da-feature` (ex.: `001-listar-contas`). Os scripts do Spec‑Kit validam esse formato antes de rodar. Referências: `.specify/scripts/bash/common.sh` (função `check_feature_branch`) e `documentacao_oficial_spec-kit/README.md` (exemplo de criação de branch na inicialização).
- Criação de branch (exemplos adaptados):
  - `git switch -c 001-contas-listar` (em vez de `feat/contas-listar`).
  - `git switch -c 002-fix-redis-timeout` (em vez de `fix/redis-timeout`).
- Integração com o handshake do Spec‑Kit por feature:
  - Fluxo: `/speckit.specify` → `/speckit.clarify` → `/speckit.plan` → `/speckit.tasks` → implementação/PR.
  - Mantenha a branch de feature sincronizada com `main` usando `git fetch && git rebase origin/main` antes de abrir o PR.
  - Após merge/squash na `main`, apague a branch local com `git branch -d 00X-...`.

