# Especificação de peças — @ninguem_nasce_ensinado

Cada peça é UM ficheiro JSON em `content/<AAAA-MM>/<ID>.json`. Todo o texto é escrito em PORTUGUÊS EUROPEU (PT-PT) e usa aspas «».

```json
{
  "id": "P16",
  "tipo": "CARROSSEL",
  "quando": "2026-11-02 20:00",
  "kicker": "A forma como falamos",
  "titulo": "Título interno curto",
  "ideias": ["LNG-I010"],
  "fontes": ["LNG-S02"],
  "slides": [ { "T": "L", "blocks": [ ... ] } ],
  "legenda": "Texto da legenda…\n\nFonte: Bishop et al. (2017), J Child Psychol Psychiatry.\n\n#ninguemnasceensinado #…",
  "notas": "opcional"
}
```

## Campos

- **id:** P = post de feed (carrossel ou imagem), R = reel, S = story «dica do dia» / «sabias que…?».
- **tipo:** `CARROSSEL` | `IMAGEM` | `REEL` | `STORY`.
- **kicker:** rótulo pequeno no topo de cada slide (2–4 palavras).
- **ideias e fontes:** IDs da biblioteca científica que sustentam a peça.
- **slides — quantos por tipo:**
  - `CARROSSEL`: 5–8 slides (1080×1350).
  - `IMAGEM`: 1 slide (1080×1350).
  - `REEL`: exatamente 4 cenas (1080×1920, cerca de 3 s cada, sem som).
  - `STORY`: 1 slide (1080×1920).
- **T — tema visual do slide:**
  - `L`: fundo papel claro, texto escuro, acento vermelho.
  - `K`: fundo preto, texto branco e vermelho.
  - `R`: fundo vermelho, texto branco e preto.
  - Usa o mesmo T em todos os slides de uma peça.
- **legenda:**
  - Gancho e 2–4 frases.
  - Linha `Fonte:` com autor(es), ano e revista, tirada da ficha da fonte.
  - 5–8 hashtags, a primeira `#ninguemnasceensinado`.
  - Máximo de 2000 caracteres.

## Blocos (dentro de `blocks`, pela ordem em que aparecem)

| bloco | campos | uso |
|---|---|---|
| `{"t":"label","text":…}` | — | rótulo em maiúsculas, cor de acento |
| `{"t":"h","text":…,"size":96,"italic":false}` | size 60–160 | título forte (Fraunces) |
| `{"t":"q","text":…,"size":100}` | size 60–160 | frase em itálico, citação ou exemplo |
| `{"t":"p","text":…,"size":34,"muted":false}` | size 28–46 | texto corrido |
| `{"t":"hand","text":…,"size":54}` | — | nota manuscrita (Caveat), vermelha |
| `{"t":"big","text":…,"size":230}` | — | número ou palavra gigante |
| `{"t":"pairs","rows":[["errado","certo"],…]}` | máx. 5 linhas | pares ✗ / ✓ |
| `{"t":"items","rows":[["1","título","texto"],…]}` | máx. 4 itens | lista numerada |
| `{"t":"card","label":…,"text":…,"size":44}` | — | cartão branco com destaque |
| `{"t":"bubble","text":…,"align":"left"}` | align `left` ou `right` | balão de fala |
| `{"t":"tenframe","ink":8,"red":2}` | — | moldura de 10 |
| `{"t":"sabias"}` | — | cabeçalho «Sabias que…?» com acento circunflexo |
| `{"t":"swipe"}` | — | «Desliza →» (só no 1.º slide de um carrossel) |
| `{"t":"cta"}` | — | botões «Guarda / Partilha» (último slide de carrossel ou imagem) |
| `{"t":"cta_reel","text":…}` | — | fecho de reel: «Guarda e envia a quem precisa.» + frase |
| `{"t":"ref","text":…}` | — | linha pequena de fonte, ex.: «Fonte: Gathercole et al., 2016» |

- **Destaque de cor:** dentro de qualquer `text`, envolve as palavras em `[[` e `]]` para as pintar na cor de acento. Exemplo: `"A gente [[vai]]."`.
- **Riscado:** usa `~~palavra~~`.

## Limites de texto (cabem no slide)

- **Carrossel e imagem:** no máximo cerca de 45 palavras por slide; título com 2 a 8 palavras.
- **Reel:** no máximo cerca de 18 palavras por cena; frases muito curtas e grandes, para ler em 3 s.
- **Story:** no máximo cerca de 40 palavras.

O motor reduz o tamanho da letra quando o texto não cabe, mas é preferível escrever pouco.

## Regras editoriais

1. **Fonte obrigatória.** Cada peça assenta em ideias e fontes da biblioteca. Não acrescentes factos que não estejam nas fichas.
2. **Certeza graduada.** A formulação segue a certeza da ficha: «A investigação mostra consistentemente…» / «Vários estudos sugerem…» / «Ainda não sabemos…».
3. **Tom.** Sem alarmismo, sem culpar pais nem crianças, sem autodiagnóstico. Distingue variação normal, sinal de alerta e diagnóstico.
4. **Língua.** PT-PT estrito: ecrã, telemóvel, equipa, «a fazer» (não «fazendo»), «tu» ou «os pais». Siglas: PHDA, PDL, PEA.
5. **Carrosséis:**
   - O 1.º slide é um gancho (pergunta, situação do dia a dia ou mito) e leva `swipe`.
   - O penúltimo slide inclui `ref`.
   - O último leva `cta`.
6. **Imagens únicas:** uma ideia forte, com `ref` e `cta`.
7. **Reels:**
   - Cena 1: gancho que prenda a atenção nos primeiros 3 segundos.
   - Cenas 2–3: explicação e exemplo.
   - Cena 4: `cta_reel`.
   - A fonte fica na legenda.
