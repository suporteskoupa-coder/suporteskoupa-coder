# Canal GTA 6 sem comentários — instruções para o Claude

Spec: veja `docs/superpowers/specs/2026-11-14-canal-gta6-design.md` no repo original (copiar para cá ao migrar).

## Regras inegociáveis
- Nada de voz, TTS, música adicionada ou conteúdo gerado por IA no vídeo. Só a gameplay do dono.
- Sem spoiler da história em título, thumbnail ou nos primeiros segundos.
- Sem clickbait falso. Sem violência explícita nos primeiros ~7 s de um vídeo.
- Textos em PT-BR; título também em EN (recurso de idiomas do YouTube).

## Procedimento a cada sessão
1. Para cada arquivo novo em `entrada/`:
   `.venv\Scripts\python -m canal processar "entrada\<arquivo>" --slug <slug-curto> --notas "<anotações do dono>"`
2. Leia `saida/<pasta>/analise.json` e olhe os JPGs de `saida/<pasta>/frames/` para entender o conteúdo.
3. Revise os Shorts em `shorts/` e as thumbs. Olhe os **primeiros 7 s** de cada Short e do longo:
   os picos de áudio caem em tiro/batida/morte e o `freezedetect` não pega tela de morte animada.
   Para trocar ou adicionar um trecho:
   `.venv\Scripts\python -m canal short "entrada\<arquivo>" --inicio S --fim E --texto "..." --saida saida\<pasta>\shorts\NN.mp4`
4. Preencha em `metadata.md` todos os `<!-- CLAUDE: preencher -->`: títulos PT/EN, descrição, tags, nomes dos capítulos.
   Escolha a melhor das 3 thumbs (ou peça ao dono para escolher).
5. Diga ao dono o que está pronto e a ordem/horário de publicação sugeridos.
6. Uma vez por semana: ler os CSVs em `metricas/` e propor ajustes de formato, títulos e cadência.

## Opções
- `--cinematic`: cor mais rica + barras 2.39:1 + fades de 1 s. Use em passeios/ambientes, não em missões.
- `--duracao-short N`: duração dos Shorts (padrão 30 s, máx. 59).
- Áudio é sempre normalizado para -14 LUFS (padrão do YouTube).

## Status
- Tarefas 1–7 prontas. Tarefa 8 (ensaio) feita em 2026-11-14 com 3 gravações de **Battlefield 6 do PC**, não do PS5 (veja Calibração).
- **Ainda falta antes do dia 19:** uma gravação de teste de ~2 min no PS5. Os caminhos de normalização (HDR, VFR, fps ≠ 60, 4K real) não foram exercitados por gravação real.
- Falta o passo 4 da Tarefa 8 (é do dono): subir 1 Short como **não listado** para conferir a qualidade final, e depois apagar.

## Calibração
Ensaio de 2026-11-14 · PC: i5-12400F, RTX 3060, ffmpeg 9.0.2 (gyan full), Python 3.12.

**Fonte do ensaio:** NVIDIA ShadowPlay (PC), 1080p60 h264 ~16 Mb/s, SDR bt709, aac 48 kHz.
O avg_frame_rate é 59,9997, abaixo do limiar de VFR, então **não houve normalização**.
O PS5 pode gravar diferente (4K, VFR, HDR): conferir no teste do console.

**Tempo medido (processar completo, já com as correções abaixo):**
| Arquivo | Duração | Analisar | Longo | Shorts | Total |
|---|---|---|---|---|---|
| BF6 #1 1080p | 3:48 | 26 s | 37 s | 22 s (4) | 89 s |
| BF6 #2 1080p | 1:20 | 17 s | 13 s | 11 s (2) | 44 s |
| BF6 #3 1080p | 0:08 | 2 s | 2 s | 0 (curto demais, ok) | 6 s |
| clipe 4K60 (upscale do #1) | 1:00 | 60 s* | 37 s | 24 s (2) | 128 s |

\* Inclui sample_frames de 1 em 1 s. Num arquivo de 1 h é 1 frame por minuto (~45 s no total).

**1 h de 4K60, extrapolado do clipe de 60 s (não medido):**
- scan ≈ 15 min, vídeo longo ≈ 36 min, frames + Shorts + thumbs ≈ 2 min. **Total ≈ 53 min por arquivo.**
- Antes das correções, ≈ 2 h.
- 5 arquivos por semana ≈ 4,5 h de máquina: deixe rodando enquanto faz outra coisa.
- O teto agora é o NVENC: a 3060 faz ~100 fps de HEVC 4K60 no p4.

**Correções feitas no ensaio:**
- Cenas: PySceneDetect → `scdet` do ffmpeg, na mesma passada do `freezedetect`, em 480 px de largura (`analyze.scan`).
  - Em 4K, o PySceneDetect levava 0,87× a duração (~52 min por 1 h). A passada única leva 0,25×.
  - O CUDA decode não ajuda: medido mais lento que a CPU.
- NVENC `-preset p5` → `p4`: SSIM 0,99063 contra 0,99064 (igual) e 1,55× mais rápido. O p1 é 3× mais rápido, com SSIM 0,9887.
- Fundo dos Shorts: desfoque em 1/4 da resolução e depois ampliado. Mesmo visual, de 19,5 s para 5,2 s por Short de 30 s.
- Texto do Short: tamanho fixo 72 vazava do quadro com ~40 caracteres. Agora reduz a fonte ou quebra em 2 linhas (`shorts.fit_text`).
- Fixture HDR dos testes: o ffmpeg 9 ignora `-color_trc` de saída, então o teste de tonemap passava sem testar nada.

**Pendências do plano, verificadas:**
- detect_scenes lento em 4K: **confirmado e corrigido** (acima).
- Limite de linha de comando:
  - **Confirmado:** o Windows corta em 32.767 caracteres, ~230 cortes no `render_long`.
  - **Corrigido:** acima de 8.000 caracteres o grafo vai para um arquivo via `-/filter_complex`.
  - O ffmpeg 9 **removeu** `-filter_complex_script`, e `-/` exige ffmpeg ≥ 7.1.
- Vídeo 100% parado:
  - **Confirmado:** quebrava com `concat=n=0`.
  - **Corrigido:** mantém o vídeo inteiro e avisa.
  - Também passaram a ser descartados os pedaços de menos de 1 s entre trechos parados.

**Revisão de conteúdo (o que o código NÃO resolve: checar à mão a cada vídeo):**
- Picos de áudio caem em tiro, explosão e morte. Com `lead_s=3` o Short começa 3 s antes da violência.
  - No ensaio, o Short que começava em 0 s do BF6 #2 abria com corpo e sangue, e o vídeo longo também. Troquei esse Short com `canal short`.
  - **Regra:** olhar os primeiros 7 s de todo Short e do longo. Se tiver violência, trocar o trecho.
  - Para o vídeo longo **não existe opção de cortar o início**: fazer à mão ou adicionar um `--inicio` ao `processar`.
- Tela de morte e killcam animadas (cinza, com texto) **não são pegas pelo `freezedetect`**: o `dead` saiu vazio nos 3 arquivos.
  - Em GTA 6, "Wasted", loading com animação e menus devem ter o mesmo problema. Calibrar quando houver gravação real.
- Thumbs: a nitidez (Laplaciano) favorece frames com HUD e texto.
  - No ensaio, uma das opções era a tela de morte, com o nick de outro jogador. **Sempre olhar as 3 antes de oferecer ao dono.**
- Layout 9:16: a gameplay ocupa só a faixa central de 1080×608 (31% da altura) e o HUD fica ilegível no celular.
  - Avaliar crop/zoom (ex.: altura ~1100 px cortando as laterais) quando houver métricas de retenção.
- Loudness medida: longo de -14,5 a -14,9 LUFS, Shorts -14,4 a -14,5 (alvo -14, loudnorm de 1 passada). OK.
- Saída: hevc/hvc1, 60 fps CFR, 1920x1080 / 1080x1920. Conferido com ffprobe.
- Capítulos: com `min_gap_s=60`, um vídeo de 1:20 sai com 2 capítulos. O YouTube exige 3+, então em vídeo curto apague a seção.

**Ambiente Windows:**
- O winget instala o ffmpeg sem atalho no PATH da sessão já aberta.
  - Em shell novo funciona.
  - Em sessão antiga, recarregar com `$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")`.
- O `instalar.ps1` reinstala o Git mesmo já instalado e pede UAC: pode aceitar.
