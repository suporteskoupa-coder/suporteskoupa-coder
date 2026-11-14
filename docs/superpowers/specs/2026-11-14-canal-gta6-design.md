# Canal de GTA 6 sem comentários — Design

Data: 2026-11-14 · Lançamento do GTA 6: 19/11/2026 (PS5 e Xbox Series, sem PC)

## 1. Intenção

Ganhar dinheiro com um canal no YouTube de gameplay de GTA 6 **sem comentários**.
Divisão do trabalho:

- **Dono do canal (humano):** cria o canal, joga, grava pelo console, copia os arquivos para o PC, publica os vídeos.
- **Claude (no PC, via Claude Code local):** edita tudo, corta os Shorts, faz as thumbnails, escreve títulos, descrições e tags, define o calendário, lê as métricas e ajusta a estratégia.

## 2. Objetivos, não-objetivos e anti-objetivos

**Objetivos**
- Entrar no Programa de Parcerias do YouTube (YPP) o mais rápido possível.
  - Regra atual (fontes secundárias, confirmar na Central de Ajuda): 1.000 inscritos + 4.000 h de exibição em 12 meses **ou** 1.000 inscritos + 10 milhões de views em Shorts em 90 dias.
  - **Alerta:** há relatos de que, a partir de 01/02/2027, canais novos vão precisar do dobro (8.000 h ou 20 mi de views em Shorts). Não verifiquei na fonte oficial. Se for verdade, bater a meta antes de fevereiro vale muito.
- Publicar com regularidade desde a semana do lançamento.
- Um pipeline de edição repetível: arquivo bruto entra, pacote pronto para postar sai.

**Não-objetivos**
- Narração, rosto ou persona.
- Live (pode entrar depois, fora deste escopo).
- Upload automático (veja a seção 6).

**Anti-objetivos (é fracasso mesmo que "funcione")**
- Voz de IA, conteúdo gerado por IA se passando por gameplay, ou reaproveitar vídeo de outros canais. Isso coloca o canal na mira da política de "conteúdo inautêntico", que é aplicada ao canal inteiro.
- Spoiler da história em título ou thumbnail.
- Clickbait falso ("GTA 6 de graça", "vazamento").
- Rádio do jogo ligada nos vídeos (Content ID manda a receita para a gravadora).

## 3. Restrições

- **Hardware:** Windows, RTX 3060, 16 GB de RAM. Encode por GPU (NVENC h264/hevc). A 3060 **não** faz encode em AV1.
- **Captura: PS5 (decidido).** Até 1 h por gravação. 4K60 só com gravação manual configurada em 4K (há relatos conflitantes). **Gravar com HDR desligado** e conferir o limite real na primeira sessão.
- **Tempo do dono: 5 h por semana de jogo e gravação (decidido).** Dá cerca de 5 arquivos de 1 h por semana: material suficiente para 7 Shorts + 2 longos, desde que pelo menos 1 h seja de passeio contínuo.
- **Volume de arquivos:** de 10 a 20 GB por hora de gravação. Exige SSD ou HD com folga (sugestão: pelo menos 500 GB livres).
- **Política da Rockstar:** permite gameplay de fã, mas o texto fala em uso "não comercial" e ela pode derrubar vídeos caso a caso. Spoilers recebem tratamento mais duro.
- **YouTube:** violência explícita nos primeiros ~7 s tira o anúncio. Thumbnail e título passam por revisão própria.
- **Concorrência:** na semana do lançamento, canais grandes dominam "GTA 6 gameplay" e "walkthrough completo". Brigar de frente é perder.
- **Repositório:** este repo é o README público do perfil no GitHub. O projeto deve ir para um **repo privado próprio** (ex.: `canal-gta6`), criado pelo dono.

## 4. Abordagens consideradas

| Abordagem | Vantagem | Desvantagem | Decisão |
|---|---|---|---|
| **A. Claude Code no PC + edição por código (ffmpeg, Python)** | Rápida, repetível, sem upload, usa a GPU | Edição "funcional", sem o feeling de um editor humano | **Escolhida** |
| B. Edição na nuvem (sessão web) | Nada a instalar | Upload de 10–20 GB/h, container sem GPU e apagado depois | Descartada |
| C. Claude clicando num editor visual por controle de tela | Usa o editor que você conhece | Lenta, frágil, um clique errado estraga o projeto | Descartada; editor visual só para ajuste fino manual, se você quiser |

O dono disse "editar no editor do meu PC". A interpretação adotada: a edição roda **no PC**, mas por código, e não clicando numa timeline.

## 5. Estratégia de conteúdo

Vídeo sem comentário não tem idioma: o canal compete globalmente e também ataca a busca em português, que é menos disputada.
- Títulos em PT-BR + tradução de título e descrição em EN pelo recurso de idiomas do YouTube.

**Formatos, em ordem de prioridade:**

1. **Shorts (motor de inscritos).** De 3 a 5 por sessão gravada: física absurda, detalhes do mapa, perseguições, "você sabia". Começar com algo forte, sem violência explícita no primeiro segundo.
2. **Passeios longos e ambientes (motor de horas de exibição).** "Dirigindo por Vice City à noite / na chuva — 1 hora, 4K, sem comentários". São atemporais, prendem o espectador por muito tempo, não têm spoiler e quase não exigem edição.
3. **Guias de busca com texto na tela.** "Onde encontrar [carro/arma/local]", "todos os [colecionáveis] de [região]". A informação vai em texto sobreposto, então funciona sem narração. O alvo é a busca em PT-BR.
4. **Missões (walkthrough) — com cautela.** Uma missão por vídeo, título e thumbnail sem spoiler. É o formato mais saturado e com mais risco de derrubada pela Rockstar. Entra como complemento, não como base.

**Cadência inicial (calibrar depois com as métricas):**
- Semana 1: 1 Short por dia + 2 a 3 vídeos longos.
- Depois: 1 Short por dia + 2 vídeos longos por semana.

**Gravação: o que o dono precisa fazer em cada sessão:**
- Rádio do jogo desligada; som ambiente e efeitos ligados.
- HDR desligado; maior resolução estável em 60 fps.
- HUD: gravar normalmente. Se o jogo tiver opção de esconder o HUD, gravar os passeios "cinemáticos" sem ele.
- Anotar (até no celular) o que tem em cada arquivo: "missão X", "achei carro Y", "passeio praia noite". Economiza análise e melhora os títulos.

## 6. Pipeline de edição (o "como")

```
canal-gta6/
  entrada/            ← o dono copia os arquivos do console aqui
  saida/<data>-<slug>/
      video.mp4       ← longo, pronto para postar
      shorts/01.mp4…  ← 9:16, 1080x1920, < 60 s
      thumb.png       ← 1280x720
      metadata.md     ← títulos PT/EN, descrição, tags, capítulos, horário sugerido
  scripts/            ← o pipeline (Python + ffmpeg)
  marca/              ← fontes, cores, intro/outro curtos
  metricas/           ← exportações do YouTube Studio
```

**Etapas:**
1. **Ingestão:** ffprobe identifica resolução, fps e HDR; normaliza para 4K ou 1440p/60 SDR.
2. **Análise:** detecção de cenas (PySceneDetect), energia do áudio (explosões, colisões) e frames de amostra que o Claude olha para entender o conteúdo.
3. **Corte do longo:** remove menus, loading e tempo parado; monta os capítulos.
4. **Shorts:** escolhe os trechos de pico e recorta em 9:16 (fundo desfocado ou crop no centro da ação). Texto curto sobreposto quando ajudar.
5. **Thumbnail:** extrai os melhores frames e aplica texto e contraste (Pillow). O dono escolhe entre 2 ou 3 opções.
6. **Metadados:** títulos, descrições, tags e capítulos escritos pelo Claude a partir da análise e das anotações.
7. **Encode:** `hevc_nvenc` ou `h264_nvenc`, com bitrate alto para o upload.

**Publicação:** manual, pelo dono, no YouTube Studio. Motivos:
- O dono quer postar.
- Até onde sei (confirmar), projetos de API do YouTube não verificados só sobem vídeos como privados até passarem por auditoria.

**Ciclo de métricas:** uma vez por semana, o dono exporta CSVs do YouTube Studio para `metricas/` e o Claude ajusta formatos, títulos e cadência.

## 7. Expectativa honesta

- Não há garantia de dinheiro. Canal do zero, num jogo com concorrência máxima, normalmente leva meses até o YPP. O pico do lançamento ajuda, mas não substitui consistência.
- A receita de anúncios para público brasileiro tende a ser bem menor que para público dos EUA. Os títulos em EN existem para pegar esse público.
- A edição vai sair limpa e funcional, não "de editor premiado".

## 8. Decidido pelo dono vs. decidido pelo Claude

**Dono:**
- Sem comentários.
- Grava pelo PS5, 5 h por semana.
- Edição no PC.
- Ele mesmo publica.
- Windows + RTX 3060 + 16 GB.
- Design aprovado em 2026-11-14.

**Claude (pode ser contestado):**
- Edição por código em vez de clique em editor.
- Mix de formatos e prioridade (Shorts + passeios longos antes de walkthrough).
- Títulos bilíngues.
- Publicação manual.
- Repo privado separado.
- Cadência inicial.

## 9. Em aberto para o builder

- Versões exatas de ffmpeg e Python no Windows; instalação via winget.
- Parâmetros de detecção de cena e de picos (calibrar com a primeira gravação real).
- Identidade visual (fonte e cores) da thumbnail.

## 10. Pendências do dono antes do dia 19

1. Criar o canal (nome definido) e o repo privado `canal-gta6` no GitHub.
2. Instalar o Claude Code no Windows e conferir que o teleport/abertura local funciona.
3. Ter um destino com espaço (SSD/HD externo) e um pendrive ou HD para tirar os arquivos do console.
4. Fazer uma gravação de teste de 2 minutos em qualquer jogo, pelo mesmo processo, para validar o pipeline antes do lançamento.
