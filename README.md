# LUMEN-Fungy — organismo-colmeia de conhecimento

> Uma mente sintética que **cultiva um ecossistema vivo de conhecimento**.
> Cada informação nasce, conecta-se, especializa-se, funde-se em ideias novas,
> adapta-se e — quando deixa de ser útil — é esquecida. A inteligência não mora
> em agentes isolados: mora na **evolução contínua da biosfera cognitiva**.
> Inspirada em fungos e no DNA. Roda inteira no Termux, só com a biblioteca padrão.

A LUMEN começou como *A Caixa Viva* — uma IA que só criava para si mesma e ficava
melhor nisso, com vontade própria, língua própria, um mundo esparso sem bordas, um
ecossistema de criaturas com herança/mutação/seleção real, janela online restrita e
exportação SVG. **Toda essa base foi preservada** e evoluiu para um organismo-colmeia:
micélio de memória, hifas-subagentes, digestão de conhecimento, cognição e um
microscópio visual em tempo real.

## Inspiração biológica → arquitetura

| Organismo | Mecanismo | Na LUMEN |
|---|---|---|
| *Physarum polycephalum* | rede de veias, *shuttle streaming*, habituação | **Micélio**: grafo de memória; hifas engrossam com o fluxo e afinam no ócio |
| *Armillaria ostoyae* | rizomorfos, enzimas lignolíticas | **Digestão**: enzimas quebram o texto; forrageio busca alimento |
| *Rhizophagus irregularis* | cenocítico, muitos núcleos, simbiose | **Memória compartilhada**; alimentação manual = simbiose |
| *Ophiocordyceps unilateralis* | metabólitos que modulam comportamento | **Sinais/eventos** que orientam a colônia (sob o Supervisor) |
| *Schizophyllum commune* | tipos de acasalamento, CAZy | **Especialização** e recombinação de subagentes |
| **DNA humano** | cromatina/TADs, epigenética, splicing | **Genoma** dos subagentes, memória epigenética, herança + mutação |

## Os órgãos

- **Micélio** — grafo vivo de conceitos (nós) e hifas (arestas). Brota, conecta,
  fortalece/enfraquece, **funde** dois conceitos numa ideia de ordem maior,
  **consolida** e **esquece** o que não serve. Tetos rígidos de nós/arestas.
- **Digestão** — alimento cognitivo em pipeline honesto: ingestão → enzimas
  (segmentação) → **curadoria** (confiabilidade × utilidade × novidade ×
  conectividade × potencial-de-descoberta × evidência) → absorção seletiva →
  consolidação → reciclagem/esquecimento. Nada entra sem passar pelo filtro.
- **Hifas (subagentes)** — cada criatura do ecossistema tende uma função cognitiva
  (**forrageadora, digestora, consolidadora, exploradora, planejadora, avaliadora**)
  que **emerge do seu genoma**. Produtivas prosperam; inúteis definham ou **se fundem**.
- **Cognição** — modelo interno do mundo (predição), raciocínio causal (ação→efeito),
  planejamento (metas que reduzem déficits), curiosidade (erro de predição + novidade)
  e **autoavaliação com reorganização autônoma** da colônia.
- **Supervisor** — contenção real: objetivo e limites **imutáveis** (a colônia não
  reescreve a própria segurança), tetos fiscalizados a cada tick, allowlist de rede,
  escrita só no sandbox, *kill-switch*. Zero exec/eval/subprocess/rede-livre.

## O microscópio da mente — 6 modos

Motor gráfico 2D pixel-art para o terminal (Braille 2×4, meio-bloco e **ANSI True
Color 24-bit**, com *diff-render* — só redesenha o que muda). Cada decisão, digestão,
hipótese, fusão e reorganização tem manifestação visual sincronizada.

1. **Micélio** — hifas crescendo/ramificando, conceitos pulsando, conhecimento fluindo.
2. **Fluxo de conhecimento** — pacotes de energia correndo pelas hifas mais fortes.
3. **Mapa cognitivo** — o grafo com rótulos e ideias fundidas em destaque.
4. **Genoma comportamental** — hélice de DNA, genes médios e distribuição de papéis.
5. **Ecossistema de agentes** — o mundo vivo, hifas coloridas por especialização.
6. **Linha temporal evolutiva** — *sparklines* de fitness, coerência, utilidade, etc.

**Teclas:** `1`–`6` escolhem o modo · `Tab` alterna · `+`/`-` zoom ·
`espaço` pausa · `q` sai.

## Uso (Termux)

```bash
python lumen_caixa.py                          # organismo-colmeia + microscópio
python lumen_caixa.py --modo fluxo              # começa em outro modo
python lumen_caixa.py --alimentar texto.txt     # alimenta com conhecimento de qualidade
python lumen_caixa.py --inbox ./lumen_inbox     # digere .txt de uma pasta aos poucos
python lumen_caixa.py --online                  # abre a janela (forrageio, sob travas)
python lumen_caixa.py --leve                    # menos partículas (aparelhos modestos)
python lumen_caixa.py --classico                # a tela única original (A Caixa Viva)
python lumen_caixa.py --headless --ticks 60     # sem tela (teste/execução em lote)
python lumen_caixa.py --reset                   # recomeça a colônia
```

Sem dependências — só a biblioteca padrão do Python 3. O estado vivo
(`lumen_mente.json`, save versão 3 retrocompatível com a base) e as obras
(`lumen_criacoes/`) são gerados em runtime e ignorados pelo git.

## Segurança e alinhamento

Crescimento **estritamente limitado** (tetos de conceitos, hifas, bytes, cota de
forrageio e orçamento de CPU por tick, todos fiscalizados a cada passo), supervisão
forte, objetivo e limites **imutáveis pela própria colônia**, escrita confinada a um
sandbox (checagem `realpath`/`commonpath`), rede restrita a uma *allowlist* fixa com
defesa anti-SSRF, e **zero** `exec`/`eval`/`subprocess`/auto-modificação de código.
A honestidade da base é mantida: sem LLM, a LUMEN não finge compreender — ela constrói
um ecossistema de conhecimento **estrutural e mensurável**, e isso é genuíno.
