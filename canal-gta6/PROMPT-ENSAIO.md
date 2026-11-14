Cole o texto abaixo num chat novo do Claude Code aberto NO SEU PC, dentro da pasta canal-gta6:

---

Leia CLAUDE.md, docs\superpowers\specs\2026-11-14-canal-gta6-design.md e docs\superpowers\plans\2026-11-14-pipeline-edicao-gta6.md (na pasta acima).
Estou no Windows (RTX 3060, 16 GB). Faça:
1. git checkout claude/session-teleport-pc-349wdk e git pull. Se .venv não existir, rode: powershell -ExecutionPolicy Bypass -File .\instalar.ps1 — confira testes passando e encoder hevc_nvenc. Se falhar, conserte com TDD.
2. Tenho 2 vídeos de Battlefield 6. Pergunte onde estão e se foram gravados pelo PS5 ou pelo PC; copie para entrada\.
3. Faça a Tarefa 8 (ensaio): processe cada vídeo, meça o tempo de cada etapa, revise frames/Shorts/thumbs, calibre e registre na seção Calibração do CLAUDE.md.
4. Verifique as pendências do CLAUDE.md (detect_scenes lento, limite de linha de comando, vídeo 100% parado).
5. Mostre o resultado e faça commit + push no mesmo branch.
Seja direto e crítico. Não poste nada nem invente resultados.
