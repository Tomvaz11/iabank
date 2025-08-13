# Output: Geração de Cenários de Teste de Aceitação do Usuário (UAT) v1.0

Com base exclusivamente no Blueprint Arquitetural fornecido, aqui estão os cenários de teste de aceitação do usuário (UAT) para a aplicação Fotix.

---

### **ID do Cenário:** `UAT_FOTIX_001`
*   **Título do Cenário:** Fluxo Completo: Scan com Configurações Padrão e Remoção de Duplicatas
*   **Fluxo Testado:** Configuração do Scan -> Execução -> Visualização de Resultados -> Confirmação da Remoção.
*   **Componentes do Blueprint Envolvidos:** `SettingsView`, `ProgressView`, `ResultsView`, `ScanService`, `BackupService`.
*   **Pré-condições:**
    *   O usuário possui uma pasta no seu computador contendo pelo menos dois arquivos de imagem idênticos (ex: `foto.jpg` e `foto_copia.jpg`) e um arquivo único.
*   **Passos para Execução:**
    1.  Abrir a aplicação Fotix. A `SettingsView` é exibida.
    2.  Clicar no botão para selecionar diretórios e escolher a pasta preparada na pré-condição.
    3.  Verificar que as opções "Busca Recursiva" e "Incluir arquivos ZIP" estão marcadas por padrão.
    4.  Clicar no botão "Iniciar Varredura".
    5.  Observar a transição para a `ProgressView`. Uma barra de progresso deve ser exibida e um log de atividades deve mostrar os arquivos sendo analisados.
    6.  Aguardar a conclusão da varredura. A aplicação deve transicionar para a `ResultsView`.
    7.  Na `ResultsView`, verificar se um conjunto de duplicatas contendo os dois arquivos idênticos (`foto.jpg` e `foto_copia.jpg`) é exibido.
    8.  Verificar se um dos arquivos está pré-selecionado como "a manter" (keeper) e o outro como "a remover", com base na lógica de `keeper_selection`.
    9.  Clicar no botão "Confirmar Remoção".
*   **Resultado Esperado:**
    *   Uma mensagem de sucesso é exibida, informando que os arquivos foram movidos para o backup e o espaço economizado.
    *   Ao verificar a pasta original no sistema de arquivos, apenas o arquivo "keeper" permanece. O arquivo marcado para remoção não está mais na pasta.
*   **Critério de Passagem:** O ciclo completo de detecção e remoção funciona como esperado, e o arquivo duplicado é removido da pasta de origem.

---

### **ID do Cenário:** `UAT_FOTIX_002`
*   **Título do Cenário:** Scan Não Recursivo
*   **Fluxo Testado:** Configuração do Scan (não recursivo) -> Execução -> Validação dos Resultados.
*   **Componentes do Blueprint Envolvidos:** `SettingsView`, `ScanService`, `ResultsView`.
*   **Pré-condições:**
    *   O usuário tem uma pasta `PAI`.
    *   Dentro de `PAI`, há dois arquivos idênticos: `A.jpg` e `B.jpg`.
    *   Dentro de `PAI`, há uma subpasta `FILHA`.
    *   Dentro de `FILHA`, há dois arquivos idênticos: `C.jpg` e `D.jpg`.
*   **Passos para Execução:**
    1.  Abrir a aplicação e navegar para a `SettingsView`.
    2.  Selecionar a pasta `PAI` para a varredura.
    3.  **Desmarcar** a caixa de seleção "Busca Recursiva".
    4.  Manter a opção "Incluir arquivos ZIP" marcada.
    5.  Clicar em "Iniciar Varredura".
    6.  Aguardar a conclusão e observar a `ResultsView`.
*   **Resultado Esperado:**
    *   A `ResultsView` exibe **apenas um** conjunto de duplicatas, contendo `A.jpg` e `B.jpg`.
    *   O conjunto de duplicatas `C.jpg` e `D.jpg` (da subpasta `FILHA`) **não** é exibido.
*   **Critério de Passagem:** A aplicação respeita a configuração "não recursiva" e ignora os arquivos em subdiretórios.

---

### **ID do Cenário:** `UAT_FOTIX_003`
*   **Título do Cenário:** Scan com Exclusão de Arquivos ZIP
*   **Fluxo Testado:** Configuração do Scan (sem ZIPs) -> Execução -> Validação dos Resultados.
*   **Componentes do Blueprint Envolvidos:** `SettingsView`, `ScanService`, `ResultsView`.
*   **Pré-condições:**
    *   O usuário tem uma pasta contendo um arquivo `imagem.zip`.
    *   Dentro de `imagem.zip` existem dois arquivos idênticos: `foto_zip_1.png` e `foto_zip_2.png`.
    *   Na mesma pasta (fora do ZIP), não há outros arquivos duplicados.
*   **Passos para Execução:**
    1.  Abrir a aplicação e navegar para a `SettingsView`.
    2.  Selecionar a pasta que contém o arquivo `imagem.zip`.
    3.  Manter a opção "Busca Recursiva" marcada.
    4.  **Desmarcar** a caixa de seleção "Incluir arquivos ZIP".
    5.  Clicar em "Iniciar Varredura".
    6.  Aguardar a conclusão e observar a tela de resultados.
*   **Resultado Esperado:**
    *   A aplicação exibe uma mensagem indicando que "Nenhuma duplicata foi encontrada" ou a `ResultsView` está vazia.
*   **Critério de Passagem:** A aplicação respeita a configuração e ignora o conteúdo de arquivos ZIP quando a opção está desmarcada.

---

### **ID do Cenário:** `UAT_FOTIX_004`
*   **Título do Cenário:** Scan com Inclusão de Arquivos ZIP
*   **Fluxo Testado:** Configuração do Scan (com ZIPs) -> Execução -> Validação dos Resultados.
*   **Componentes do Blueprint Envolvidos:** `SettingsView`, `ScanService`, `ResultsView`, `FileSystemService` (com `stream-unzip`).
*   **Pré-condições:**
    *   As mesmas do cenário `UAT_FOTIX_003` (uma pasta com um ZIP contendo duplicatas).
*   **Passos para Execução:**
    1.  Abrir a aplicação e navegar para a `SettingsView`.
    2.  Selecionar a pasta que contém o arquivo `imagem.zip`.
    3.  Manter a opção "Busca Recursiva" marcada.
    4.  **Manter marcada** a caixa de seleção "Incluir arquivos ZIP".
    5.  Clicar em "Iniciar Varredura".
    6.  Aguardar a conclusão e observar a `ResultsView`.
*   **Resultado Esperado:**
    *   A `ResultsView` exibe um conjunto de duplicatas contendo os arquivos `foto_zip_1.png` e `foto_zip_2.png` que estavam dentro do arquivo ZIP.
*   **Critério de Passagem:** A aplicação é capaz de escanear o conteúdo de arquivos ZIP e identificar duplicatas dentro deles.

---

### **ID do Cenário:** `UAT_FOTIX_005`
*   **Título do Cenário:** Scan de Pasta Sem Duplicatas
*   **Fluxo Testado:** Execução de um scan que não resulta em duplicatas.
*   **Componentes do Blueprint Envolvidos:** `SettingsView`, `ProgressView`, `ResultsView`, `ScanService`.
*   **Pré-condições:**
    *   O usuário possui uma pasta contendo vários arquivos, mas nenhum deles é uma cópia idêntica de outro.
*   **Passos para Execução:**
    1.  Abrir a aplicação e ir para a `SettingsView`.
    2.  Selecionar a pasta com arquivos únicos.
    3.  Clicar em "Iniciar Varredura".
    4.  Observar a `ProgressView` até a conclusão.
*   **Resultado Esperado:**
    *   A `ResultsView` é exibida com uma mensagem clara e visível para o usuário, como "Nenhuma duplicata encontrada.". A tela não deve mostrar uma tabela vazia ou uma mensagem de erro.
*   **Critério de Passagem:** A aplicação lida de forma graciosa com o caso de não encontrar duplicatas, fornecendo feedback claro ao usuário.

---

### **ID do Cenário:** `UAT_FOTIX_006`
*   **Título do Cenário:** Restauração de um Arquivo Removido
*   **Fluxo Testado:** Navegação para a tela de restauração -> Seleção de um arquivo -> Confirmação da Restauração.
*   **Componentes do Blueprint Envolvidos:** `RestoreView`, `BackupService` (ou um `RestoreService`).
*   **Pré-condições:**
    *   O cenário `UAT_FOTIX_001` (ou qualquer outro que removeu um arquivo) foi executado com sucesso.
    *   Existe pelo menos um arquivo no diretório de backup do Fotix (ex: `~/.fotix/backup/`).
    *   O arquivo original (ex: `foto_copia.jpg`) não existe mais em seu local de origem.
*   **Passos para Execução:**
    1.  Abrir a aplicação Fotix.
    2.  Navegar para a tela de restauração (`RestoreView`) através do menu principal ou de um botão na `MainWindow`.
    3.  Observar uma lista de arquivos que foram previamente removidos, exibindo informações como caminho original e data do backup.
    4.  Selecionar na lista o arquivo `foto_copia.jpg`.
    5.  Clicar no botão "Restaurar Selecionado(s)".
*   **Resultado Esperado:**
    *   Uma mensagem de sucesso é exibida, confirmando a restauração.
    *   O arquivo `foto_copia.jpg` reaparece em seu diretório original.
    *   O arquivo é removido da lista na `RestoreView`.
*   **Critério de Passagem:** A funcionalidade de restauração funciona corretamente, movendo um arquivo do backup de volta para seu local original.

---

### **ID do Cenário:** `UAT_FOTIX_007`
*   **Título do Cenário:** Scan em Múltiplos Diretórios Independentes
*   **Fluxo Testado:** Configuração do Scan com mais de um diretório -> Execução -> Validação de duplicatas entre diretórios.
*   **Componentes do Blueprint Envolvidos:** `SettingsView`, `ScanService`, `ResultsView`.
*   **Pré-condições:**
    *   O usuário possui duas pastas distintas, `PASTA_A` e `PASTA_B`.
    *   `PASTA_A` contém o arquivo `imagem.png`.
    *   `PASTA_B` contém uma cópia idêntica do mesmo arquivo, `imagem.png`.
*   **Passos para Execução:**
    1.  Abrir a aplicação e ir para a `SettingsView`.
    2.  Clicar para adicionar um diretório e selecionar `PASTA_A`.
    3.  Clicar novamente para adicionar outro diretório e selecionar `PASTA_B`.
    4.  Verificar que ambos os caminhos estão listados na interface.
    5.  Clicar em "Iniciar Varredura".
    6.  Aguardar a conclusão e observar a `ResultsView`.
*   **Resultado Esperado:**
    *   A `ResultsView` exibe um conjunto de duplicatas contendo os dois arquivos `imagem.png`, um de `PASTA_A` e outro de `PASTA_B`.
*   **Critério de Passagem:** A aplicação é capaz de aceitar múltiplos diretórios como entrada e encontrar duplicatas que existem entre eles.

---

### **ID do Cenário:** `UAT_FOTIX_008`
*   **Título do Cenário:** Revisão e Alteração Manual do Arquivo a Manter (Keeper)
*   **Fluxo Testado:** Visualização de Resultados -> Alteração da decisão automática -> Confirmação da Remoção.
*   **Componentes do Blueprint Envolvidos:** `ResultsView`, `ScanService`.
*   **Pré-condições:**
    *   Um scan foi concluído e a `ResultsView` está sendo exibida com um conjunto de duplicatas.
    *   O conjunto contém `foto_antiga.jpg` (criada em 2020) e `foto_nova.jpg` (criada em 2023), que são idênticas.
    *   A lógica automática (`keeper_selection`) marcou `foto_antiga.jpg` como "a manter" e `foto_nova.jpg` como "a remover".
*   **Passos para Execução:**
    1.  Na `ResultsView`, localizar o conjunto de duplicatas `foto_antiga.jpg` / `foto_nova.jpg`.
    2.  Observar que `foto_antiga.jpg` está marcada como "Manter".
    3.  Clicar em `foto_nova.jpg` e selecionar uma opção como "Marcar como principal" ou "Manter este".
    4.  Verificar que a interface atualiza, mostrando agora `foto_nova.jpg` como "a manter" e `foto_antiga.jpg` como "a remover".
    5.  Clicar no botão "Confirmar Remoção".
*   **Resultado Esperado:**
    *   O arquivo `foto_antiga.jpg` é removido/movido para o backup.
    *   O arquivo `foto_nova.jpg` permanece no diretório original.
*   **Critério de Passagem:** O usuário pode sobrepor a seleção automática do "keeper", e a aplicação respeita a decisão manual do usuário durante a remoção.

---

### **ID do Cenário:** `UAT_FOTIX_009`
*   **Título do Cenário:** Tentativa de Iniciar Scan Sem Selecionar Diretório
*   **Fluxo Testado:** Interação inválida na tela de configuração.
*   **Componentes do Blueprint Envolvidos:** `SettingsView`.
*   **Pré-condições:**
    *   A aplicação Fotix está aberta na `SettingsView`.
    *   Nenhum diretório foi selecionado para a varredura.
*   **Passos para Execução:**
    1.  Garantir que a lista de diretórios a escanear está vazia.
    2.  Clicar no botão "Iniciar Varredura".
*   **Resultado Esperado:**
    *   A varredura **não** inicia.
    *   Uma mensagem de erro ou aviso é exibida na interface, instruindo o usuário a selecionar pelo menos um diretório.
    *   A aplicação permanece na `SettingsView`, estável e responsiva.
*   **Critério de Passagem:** A aplicação valida a entrada do usuário antes de iniciar uma operação, prevenindo erros e fornecendo feedback útil.