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
3. Revise os Shorts em `shorts/`. Para trocar ou adicionar um trecho:
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
- Tarefas 1–7 do plano prontas. Falta a Tarefa 8: ensaio com gravação real (o dono tem 2 vídeos de Battlefield 6 — servem de ensaio).
- Pendências a medir no ensaio: tempo do detect_scenes em 1 h de 4K; limite de linha de comando com muitos cortes; vídeo 100% parado quebra render_long.

## Calibração
(valores ajustados após o ensaio com gravação real do PS5 entram aqui)
