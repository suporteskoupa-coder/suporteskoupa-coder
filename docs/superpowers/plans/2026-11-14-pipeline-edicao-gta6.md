# Pipeline de Edição do Canal GTA 6 — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Um comando no Windows que pega uma gravação bruta do PS5 e entrega um pacote pronto para postar: vídeo longo, 3 a 5 Shorts, opções de thumbnail e o esqueleto dos metadados.

**Architecture:** Pacote Python `canal` com um módulo por etapa (probe → análise → corte → shorts → thumbs → metadados). Cada etapa chama o ffmpeg via `subprocess`. A CLI orquestra tudo e grava `analise.json`, que o Claude lê para escrever títulos e descrições e para ajustar os cortes. O encoder é escolhido automaticamente: `hevc_nvenc` na RTX 3060, com fallback para `libx264`, de modo que os testes rodam sem GPU.

**Tech Stack:** Python 3.12, ffmpeg/ffprobe (build gyan.dev "full", via winget), PySceneDetect 0.6+, numpy, Pillow, pytest.

**Spec:** `docs/superpowers/specs/2026-11-14-canal-gta6-design.md`

## Global Constraints

- SO alvo: Windows 11. Os testes também precisam passar em Linux (CI/nuvem). Use `pathlib` em tudo e nunca `shell=True`.
- Fonte: PS5, até 1 h por arquivo, mp4/webm, SDR esperado (HDR deve ser tratado mesmo assim).
- Vídeo longo: 2160p se a fonte for 4K, senão a altura da fonte; 60 fps CFR.
- Shorts: 1080x1920, duração ≤ 59 s, 60 fps.
- Thumbnail: 1280x720 PNG, 3 opções por vídeo.
- Encoder: `hevc_nvenc` se disponível, senão `libx264`. Nunca AV1 (a 3060 não codifica AV1).
- Nada de voz, TTS ou música adicionada. O áudio é sempre o do jogo.
- Saída em `saida/<AAAA-MM-DD>-<slug>/` com exatamente: `video.mp4`, `shorts/NN.mp4`, `thumbs/opcao-N.png`, `metadata.md`, `analise.json`.
- Textos para o usuário (mensagens da CLI, metadata.md) em PT-BR.
- O código mora no repo privado `canal-gta6`, não no repo do perfil.

## Review Focus

1. **Gravação em HDR por engano** (HDR10/PQ) → converter para SDR com tonemap; não pode sair lavado nem estourado. Teste na Task 2.
2. **Frame rate variável** (gravação de console costuma ser VFR) → a saída é sempre 60 fps CFR, sem dessincronizar o áudio. Teste na Task 2.
3. **Gravação mais curta que um Short ou com poucos picos** → gera menos Shorts (ou nenhum) sem quebrar. Teste na Task 5.
4. **Caminho com espaço e acento** (`entrada/missão da praia.mp4`) → funciona no Windows. Teste na Task 7.
5. **Disco sem espaço** → aborta antes de renderizar, com uma mensagem dizendo quanto falta (estimativa: 2× o tamanho da fonte). Teste na Task 7.

---

### Task 1: Esqueleto do repo, setup do Windows e regras para o Claude

**Files:**
- Create: `pyproject.toml`, `canal/__init__.py`, `canal/config.py`, `tests/conftest.py`, `SETUP.md`, `CLAUDE.md`, `.gitignore`

**Interfaces:**
- Produces: `Config` (dataclass frozen) em `canal/config.py`, com os campos `long_max_height: int = 2160`, `fps: int = 60`, `short_size: tuple[int,int] = (1080, 1920)`, `short_max_s: float = 59.0`, `shorts_per_video: int = 5`, `thumb_size: tuple[int,int] = (1280, 720)`, `thumb_options: int = 3`, `dead_min_s: float = 4.0`.
- Produces: fixture pytest `sample_video(tmp_path, *, seconds=20, width=1280, height=720, fps=30, freeze_at=None, hdr=False, vfr=False, audio=True) -> Path`. Ela gera um vídeo sintético com `testsrc2`, um seno no áudio e um "estrondo" (burst de ruído) a cada 5 s. `freeze_at=(s,e)` congela o frame no intervalo; `hdr=True` marca `bt2020/smpte2084`; `vfr=True` grava com timestamps variáveis.

- [ ] **Step 1:** Escrever `tests/test_config.py::test_defaults_match_spec`, que verifica `Config().short_size == (1080,1920)`, `short_max_s == 59.0` e `thumb_size == (1280,720)`.
- [ ] **Step 2:** Rodar `pytest tests/test_config.py -v` → FAIL (módulo inexistente).
- [ ] **Step 3:** Implementar `Config`, a fixture `sample_video` e `pyproject.toml`, com as dependências `scenedetect[opencv-headless]>=0.6`, `numpy`, `Pillow` e o extra dev `pytest`.
- [ ] **Step 4:** Escrever `SETUP.md` com os passos para o usuário:
  - `winget install Gyan.FFmpeg Python.Python.3.12 Git.Git`
  - Clonar o repo; rodar `py -m venv .venv` e `.venv\Scripts\pip install -e .[dev]`.
  - Configurar a captura no PS5: HDR desligado, gravação manual em 4K60, áudio do jogo sem rádio.
- [ ] **Step 5:** Escrever `CLAUDE.md`, o procedimento que o Claude segue no PC a cada sessão:
  1. Rodar `python -m canal processar <arquivo> --slug <slug> --notas "<notas>"`.
  2. Ler `analise.json` e olhar os frames de amostra.
  3. Reordenar ou remover Shorts ruins com `python -m canal short <arquivo> --inicio S --fim E --texto "..."`.
  4. Preencher títulos PT/EN, descrição e tags no `metadata.md`, seguindo as regras da spec: sem spoiler, sem clickbait falso.
  5. Avisar o usuário de que está pronto.
  6. Uma vez por semana: ler os CSVs em `metricas/` e propor ajustes de formato, títulos e cadência.
- [ ] **Step 6:** Rodar `pytest -v` → PASS. Commit: `chore: esqueleto do pipeline e setup do Windows`.

### Task 2: Probe e normalização (encoder, HDR, VFR)

**Files:**
- Create: `canal/probe.py`, `canal/encode.py`
- Test: `tests/test_probe.py`, `tests/test_encode.py`

**Interfaces:**
- Consumes: `Config`, `sample_video`.
- Produces:
  - `MediaInfo` (dataclass): `width:int, height:int, fps:float, duration:float, is_hdr:bool, is_vfr:bool, has_audio:bool`
  - `probe(path: Path) -> MediaInfo`
  - `pick_encoder() -> str`, que retorna `"hevc_nvenc"` ou `"libx264"`
  - `video_args(encoder: str, height: int, fps: int) -> list[str]`
  - `normalize(src: Path, dst: Path, info: MediaInfo, cfg: Config) -> Path`

- [ ] **Step 1:** Testes:
  - `test_probe_reads_dimensions`: 1280x720, 30 fps, ~20 s.
  - `test_probe_flags_hdr`: `hdr=True` → `is_hdr`.
  - `test_probe_flags_vfr`: `vfr=True` → `is_vfr`.
  - `test_pick_encoder_falls_back`: com `ffmpeg -encoders` mockado sem nvenc → `"libx264"`.
  - `test_normalize_outputs_cfr_60`: entra VFR, sai com `fps == 60` e `is_vfr is False`, e a diferença entre as durações de áudio e vídeo é < 0,1 s.
  - `test_normalize_tonemaps_hdr`: entra HDR, sai `is_hdr is False`, e o brilho médio do frame (via Pillow) fica entre 40 e 215.
- [ ] **Step 2:** `pytest tests/test_probe.py tests/test_encode.py -v` → FAIL.
- [ ] **Step 3:** Implementar:
  - `probe` com `ffprobe -show_streams -show_format -of json`. HDR = `color_transfer` em {`smpte2084`, `arib-std-b67`}. VFR = `r_frame_rate != avg_frame_rate`.
  - `normalize` com `-vf fps=60`, mais `zscale=t=linear,tonemap=hable,zscale=p=bt709:t=bt709:m=bt709,format=yuv420p` quando HDR, e escala para `min(source, long_max_height)`.
  - Detectar NVENC tentando um encode de 1 frame. Só aparecer em `ffmpeg -encoders` não basta, porque o encoder pode estar listado sem GPU.
- [ ] **Step 4:** Rodar os testes → PASS. Commit: `feat: probe e normalização com tonemap HDR e CFR`.

### Task 3: Análise (cenas, picos de áudio, trechos mortos, frames)

**Files:**
- Create: `canal/analyze.py`
- Test: `tests/test_analyze.py`

**Interfaces:**
- Consumes: `MediaInfo`, `Config`.
- Produces:
  - `Peak` (dataclass): `t: float, rms_db: float`
  - `detect_scenes(path: Path) -> list[tuple[float, float]]`
  - `audio_peaks(path: Path, window_s: float = 1.0, top_n: int = 20) -> list[Peak]`, ordenada por `rms_db` decrescente, com picos a pelo menos 10 s um do outro
  - `dead_segments(path: Path, min_len_s: float) -> list[tuple[float, float]]` (frame congelado: loading e menus)
  - `sample_frames(path: Path, every_s: float, out_dir: Path) -> list[Path]`

- [ ] **Step 1:** Testes:
  - `test_audio_peaks_finds_bursts`: o vídeo de 20 s tem bursts em 5, 10 e 15 s; os 3 primeiros picos ficam a ±1 s desses tempos.
  - `test_dead_segments_finds_freeze`: `freeze_at=(6,12)` → um segmento com início em [5,5; 6,5] e fim em [11,5; 12,5].
  - `test_no_audio_returns_no_peaks`: `audio=False` → `[]`, sem exceção.
  - `test_sample_frames_count`: 20 s com `every_s=5` → 4 arquivos JPG.
- [ ] **Step 2:** `pytest tests/test_analyze.py -v` → FAIL.
- [ ] **Step 3:** Implementar:
  - Picos: decodificar o áudio para PCM mono 8 kHz via ffmpeg (stdout) e calcular o RMS por janela com numpy.
  - Trechos mortos: filtro `freezedetect=n=-60dB:d=<min_len_s>` lido do stderr.
  - Cenas: `scenedetect.detect` com `ContentDetector`.
- [ ] **Step 4:** Rodar os testes → PASS. Commit: `feat: análise de cenas, picos e trechos mortos`.

### Task 4: Vídeo longo (corte e capítulos)

**Files:**
- Create: `canal/cut.py`
- Test: `tests/test_cut.py`

**Interfaces:**
- Consumes: `dead_segments`, `video_args`, `pick_encoder`.
- Produces:
  - `keep_segments(duration: float, dead: list[tuple[float,float]]) -> list[tuple[float,float]]`
  - `render_long(src: Path, segments: list[tuple[float,float]], dst: Path, cfg: Config) -> Path`
  - `chapters(segments: list[tuple[float,float]], scenes: list[tuple[float,float]], min_gap_s: float = 60.0) -> list[tuple[float, str]]`: tempos já no vídeo cortado, o primeiro sempre `(0.0, "Início")`, os demais `"Parte N"` (o Claude renomeia depois)

- [ ] **Step 1:** Testes:
  - `test_keep_segments_inverts_dead`: `(20, [(6,12)])` → `[(0,6),(12,20)]`.
  - `test_keep_segments_no_dead`: → `[(0,20)]`.
  - `test_render_long_duration`: `freeze_at=(6,12)` → duração de saída 14 s ± 0,5 s.
  - `test_chapters_start_at_zero`: primeiro item `(0.0, "Início")`; nenhum par de capítulos a menos de 60 s.
- [ ] **Step 2:** → FAIL.
- [ ] **Step 3:** Implementar `render_long` com `trim`/`atrim` + `concat` num único `filter_complex`, sem arquivos intermediários.
- [ ] **Step 4:** → PASS. Commit: `feat: corte do vídeo longo e capítulos`.

### Task 5: Shorts

**Files:**
- Create: `canal/shorts.py`
- Test: `tests/test_shorts.py`

**Interfaces:**
- Consumes: `Peak`, `video_args`, `pick_encoder`, `Config`.
- Produces:
  - `pick_short_windows(peaks: list[Peak], duration: float, n: int, length_s: float, lead_s: float = 3.0) -> list[tuple[float,float]]`: cada janela começa `lead_s` antes do pico, cabe em `[0, duration]`, as janelas não se sobrepõem, e o resultado vem ordenado por força do pico
  - `render_short(src: Path, window: tuple[float,float], dst: Path, cfg: Config, text: str | None = None) -> Path`

- [ ] **Step 1:** Testes:
  - `test_windows_do_not_overlap`.
  - `test_windows_clamped_to_duration`: pico em 1 s com `lead_s=3` → início 0.
  - `test_short_video_yields_fewer_windows`: vídeo de 8 s com `length_s=30` → `[]`.
  - `test_render_short_is_vertical`: probe da saída → 1080x1920 e duração ≤ 59.
  - `test_render_short_with_accented_text`: `text="Ação na praia!"` renderiza sem erro.
- [ ] **Step 2:** → FAIL.
- [ ] **Step 3:** Implementar `render_short` em layout 9:16:
  - Fundo: a fonte escalada para cobrir 1080x1920 e desfocada (`boxblur=20`).
  - Frente: a fonte escalada para largura 1080, centralizada.
  - Texto opcional com `drawtext`, usando um arquivo de fonte em `marca/fonte.ttf`. O texto vai por `textfile=` (arquivo temporário UTF-8) para evitar problemas de escape no Windows.
- [ ] **Step 4:** → PASS. Commit: `feat: geração de Shorts 9:16`.

### Task 6: Thumbnails e metadados

**Files:**
- Create: `canal/thumbs.py`, `canal/metadata.py`
- Test: `tests/test_thumbs.py`, `tests/test_metadata.py`

**Interfaces:**
- Consumes: `sample_frames`, `chapters`, `Config`.
- Produces:
  - `sharpness(img: Path) -> float` (variância do Laplaciano em tons de cinza)
  - `best_frames(frames: list[Path], k: int, min_gap: int = 3) -> list[Path]`: os k mais nítidos, com pelo menos `min_gap` posições de distância na lista original
  - `make_thumb(frame: Path, dst: Path, cfg: Config, text: str | None = None) -> Path`: 1280x720 com contraste +15% e texto opcional com contorno
  - `write_metadata(dst: Path, *, slug: str, notas: str, chapters: list[tuple[float,str]], shorts: list[Path], thumbs: list[Path]) -> Path`

- [ ] **Step 1:** Testes:
  - `test_best_frames_prefers_sharp`: entre um frame nítido e um desfocado, o nítido vem primeiro.
  - `test_make_thumb_size`: 1280x720.
  - `test_metadata_has_sections`: o arquivo contém os cabeçalhos `## Título (PT)`, `## Title (EN)`, `## Descrição`, `## Tags`, `## Capítulos`, `## Horário sugerido`; os capítulos aparecem no formato `0:00 Início`; as notas aparecem literalmente.
- [ ] **Step 2:** → FAIL.
- [ ] **Step 3:** Implementar com Pillow + numpy.
  - `write_metadata` deixa `<!-- CLAUDE: preencher -->` nos campos de título, descrição e tags.
  - O horário sugerido é fixo por enquanto, até haver métricas: Shorts 12h e 19h, longos 18h, horário de Brasília.
- [ ] **Step 4:** → PASS. Commit: `feat: thumbnails e esqueleto de metadados`.

### Task 7: CLI `processar` e `short`, com checagens

**Files:**
- Create: `canal/cli.py`, `canal/__main__.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: tudo acima.
- Produces:
  - `processar(src: Path, slug: str, notas: str = "", out_root: Path = Path("saida"), cfg: Config = Config()) -> Path`, que devolve a pasta de saída e grava `analise.json` com as chaves `info`, `scenes`, `peaks`, `dead`, `segments`, `chapters`, `shorts`, `frames`
  - `check_free_space(src: Path, out_root: Path) -> None`, que levanta `EspacoInsuficiente` com a mensagem `"Espaço insuficiente: precisa de ~X GB, tem Y GB"` quando livre < 2× o tamanho da fonte
  - Subcomandos: `python -m canal processar <arquivo> --slug S [--notas N]` e `python -m canal short <arquivo> --inicio S --fim E [--texto T] --saida <pasta>`

- [ ] **Step 1:** Testes:
  - `test_processar_creates_package`: vídeo sintético de 40 s → existem `video.mp4`, ≥ 1 arquivo em `shorts/`, 3 em `thumbs/`, `metadata.md` e um `analise.json` válido. O nome da pasta casa com `\d{4}-\d{2}-\d{2}-teste`.
  - `test_processar_path_with_accents`: fonte em `tmp/missão da praia.mp4` → sucesso.
  - `test_free_space_check`: com `shutil.disk_usage` mockado retornando 1 GB livre e uma fonte de 1 GB → `EspacoInsuficiente`, e nenhum arquivo criado em `saida/`.
- [ ] **Step 2:** → FAIL.
- [ ] **Step 3:** Implementar com `argparse`. A ordem é: checar espaço → probe → normalizar (só se HDR, VFR ou fps ≠ 60; senão usar a fonte direto) → análise → longo → shorts → thumbs → metadados → JSON. Um print em PT-BR por etapa, com o tempo gasto.
- [ ] **Step 4:** `pytest -v` (suíte inteira) → PASS. Commit: `feat: CLI processar e short`.

### Task 8: Ensaio geral com gravação real do PS5

**Files:**
- Modify: `canal/config.py` (só se a calibração pedir), `CLAUDE.md` (lições do ensaio)

- [ ] **Step 1:** O usuário grava 2 minutos de qualquer jogo no PS5, com as configurações do `SETUP.md`, e copia o arquivo para `entrada/`.
- [ ] **Step 2:** Rodar `python -m canal processar entrada/<arquivo> --slug ensaio`. Esperado: o pacote completo em menos de ~5 min, usando `hevc_nvenc` (aparece no log).
- [ ] **Step 3:** O Claude revisa os Shorts e as thumbs gerados. Se os picos escolhidos forem ruins, ajustar `window_s`/`top_n` e o limiar do `freezedetect`, e registrar os valores no `CLAUDE.md`.
- [ ] **Step 4:** O usuário sobe um Short como **não listado** no YouTube para conferir a qualidade final, e depois apaga.
- [ ] **Step 5:** Commit: `chore: calibração com gravação real do PS5`.
