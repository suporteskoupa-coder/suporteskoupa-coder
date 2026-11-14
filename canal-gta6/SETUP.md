# Instalação no Windows (uma vez só)

0. **Atalho:** dentro da pasta `canal-gta6`, rode `powershell -ExecutionPolicy Bypass -File .\instalar.ps1` — ele faz os passos 1 e 2 sozinho.
1. Abra o **PowerShell** e instale as ferramentas:
   ```powershell
   winget install Gyan.FFmpeg Python.Python.3.12 Git.Git
   ```
   Feche e abra o PowerShell de novo depois disso.
2. Baixe o projeto e prepare o ambiente:
   ```powershell
   git clone <URL-do-repo> canal-gta6
   cd canal-gta6
   py -3.12 -m venv .venv
   .venv\Scripts\pip install -e .[dev]
   .venv\Scripts\pytest -q        # tem que terminar com "passed"
   ```
3. Instale o Claude Code e abra-o dentro da pasta `canal-gta6`.

# Configuração do PS5 (antes de jogar)

- **Configurações → Capturas e transmissões → Capturas**
  - Tipo de arquivo de vídeo: **MP4** (não WebM).
  - Resolução: **2160p** (4K) se a TV for 4K; senão 1080p.
  - Gravação manual: inicie pelo botão **Criar** → **Iniciar nova gravação** (máx. 1 h por arquivo).
  - Desligue a gravação de áudio do microfone/chat.
- **Configurações → Tela e vídeo → HDR: Desligado** enquanto gravar.
- **No jogo:** rádio dos carros **desligada** (direitos autorais); efeitos e som ambiente ligados.

# Toda vez que gravar

1. Copie os arquivos do PS5 para um pendrive/HD (formato exFAT) e depois para `canal-gta6\entrada\`.
2. Anote em uma linha o que tem em cada arquivo (ex.: "passeio de noite na praia", "missão do barco").
3. Abra o Claude Code na pasta e diga: **"processa os vídeos novos"** + suas anotações.
4. Pegue o pacote pronto em `saida\` e publique.
