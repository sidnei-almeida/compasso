# Trilha de fundo dos episódios de Alien: Isolation

Pack gerado localmente (Stable Audio 3, `scripts/music-pack.sh`), tudo em Lá menor e na mesma
família de som da intro, para soar como uma trilha só. Nada aqui tem direitos de terceiros.

## O que tem em cada pasta

| Pasta | Clima | Quando usar |
|---|---|---|
| `01-exploracao` | calma, pad e piano | andar, ler terminais, comentar com calma |
| `02-inquieto` | drone baixo, piano raro, sem pulso | "tem algo errado", corredores vazios |
| `03-stealth` | batimento, drone, tiques | esconder, rastreador na mão, esperar o alien passar |
| `04-terror` | swells dissonantes, chocalhos | o alien está perto, sem pulso |
| `05-perseguicao-alien` | ostinato de cordas, taiko, 120 bpm | caçada |
| `06-perseguicao-androide` | pulso mecânico frio, metal | Working Joes |
| `07-ninho` | texturas orgânicas, drone grave | reator e ninho (M14) |
| `08-lv426` | vasto, alienígena | flashback do Marlow (M9) |
| `09-morte` | impacto, queda, silêncio (12 s) | a morte |
| `10-alivio` | piano resolvendo (30 s) | depois da fuga, save point |
| `11-stingers` | golpes secos (3 a 6 s) | sustos, exatamente no corte |
| `12-risers` | subidas (6 a 8 s) | antes do susto; o pico cai no corte |
| `13-transicoes` | whoosh e impacto (2 a 4 s) | cortes entre cenas |
| `14-reator-descida` | pulso mecânico dos androides, taiko, alarmes, tensão sem resolver | a descida ao reator com os Working Joes atrás, armando a purga (M14). Plano do dono: `parte1` na chegada; `parte2-1` em loop enquanto os androides vão aparecendo, com um `stinger-metal` em cada novo; `parte2-2` quando ela aperta o botão da purga; o som do botão é o do próprio jogo, a música só para no corte |
| `15-ninho` | peça de 4 min: orgânico, batimento que acelera, stabs | dentro do ninho (M14) |
| `18-fuga-final` | peça de 4 min: orquestra desesperada, sirenes, e o piano da intro voltando no fim | os dois aliens e o traje no terminal de voo (M18) |

As peças especiais (14, 15, 18) vêm em `parte1`, `parte2` (continuação composta pelo modelo),
`completa` (4 min) e loops de cada parte, mais stingers próprios. As camas (pastas 01 a 08) têm 2 minutos; a versão `-loop` tem emenda invisível (os últimos 4 s
cruzados com os primeiros), para repetir quanto precisar.

## Como usar na edição (como num filme)

1. **Uma cama por cena, não por minuto.** Troque a cama quando o clima muda, não no relógio.
2. **Ducking**: a cama fica 10 a 14 dB abaixo da voz enquanto você fala, e volta nos silêncios.
3. **Silêncio é instrumento.** Antes de um susto grande, corte a música de vez por alguns segundos.
   O stinger sozinho, no silêncio, assusta mais do que em cima de uma cama.
4. **Stinger no corte**: o pico do stinger cai no mesmo quadro do susto (o alien aparecendo, a
   morte, a porta abrindo).
5. **Riser antes, stinger no, alívio depois**: riser de 6 s subindo até o corte, stinger no corte,
   dois segundos de nada, e a cama de alívio ou de stealth entra baixinho.
6. **Perseguição**: entra no primeiro passo de corrida e corta seco quando você se esconde; na
   escuta, volta para `03-stealth`.
7. **Morte**: `09-morte` sozinha, com a imagem; nada por cima.
8. **Transições de cena** (pular para outra missão, cortar tempo morto): um `13-transicoes` no corte.
9. Volte à `01-exploracao` sempre que der para respirar; é a identidade do canal.

Para gerar mais variações de uma pasta: `scripts/music-pack.sh 03-stealth`.
