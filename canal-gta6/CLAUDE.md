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

## Calibração
(valores ajustados após o ensaio com gravação real do PS5 entram aqui)
