# 9. Plataforma de GitOps

**Status:** Aprovado

**Contexto:** Para cumprir o Artigo sobre Infraestrutura como Código (IaC) da Constituição, que exige que as mudanças na infraestrutura sejam aplicadas através de um fluxo de trabalho GitOps, foi necessário escolher uma ferramenta.

**Decisão:** O projeto adota o **Argo CD** como a ferramenta para sincronizar o estado do repositório Git com o ambiente de produção, garantindo a detecção de drift e um processo de deploy auditável.

**Consequências:** 
- As definições de aplicação para o Kubernetes serão mantidas no formato de manifestos ou charts do Helm no repositório.
- O Argo CD será configurado para monitorar o branch principal e aplicar as mudanças automaticamente nos ambientes correspondentes.
- Rollbacks serão realizados através da reversão de commits no Git.
