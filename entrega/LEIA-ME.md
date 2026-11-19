# KRYOU 3D — CIPEIRO DO MÊS — 200 mm — 4 cores — FlashForge Creator 5

## Arquivos entregues

| Arquivo | Conteúdo |
|---|---|
| `KRYOU_CIPEIRO_DO_MES_200MM_4CORES.3mf` | Arquivo principal. Um objeto de impressão (`PERSONAGEM_CIPEIRO`) com 33 volumes nomeados, 4 materiais, em mm, escala 1:1. |
| `KRYOU_CIPEIRO_DO_MES_FONTE.blend` | Fonte Blender 5.3. Uma coleção por cabeçote (T0_VERDE, T1_BRANCO, T2_PRETO, T3_PELE), 33 objetos com material real, unidades em mm. |
| `renders/render_01…10_*.png` | As 10 vistas de inspeção pedidas: frente, perfil, perspectiva, costas e closes do rosto, capacete, óculos, sinal de vitória, camisa e base. |
| `comparacao_referencia.png` | Referência anexada ao lado das vistas equivalentes do 3MF final. |
| `sobreposicao_silhuetas.png` | Contorno do modelo sobre a referência (magenta) e contorno da referência sobre o modelo (vermelho). |
| `cortes_camadas.png` | Seções horizontais nas alturas críticas: dedos, óculos, boca, CIPAA, acento do Ê, letreiro e barra da capa. |
| `validacao.json` | Todos os números da validação abaixo. |

Os renders e a comparação foram gerados a partir do 3MF exportado e relido, não da cena de modelagem.

## Medidas (lidas do 3MF exportado)
- **Altura total: 200,00 mm**, da face inferior da base ao topo do capacete.
- **Largura × profundidade: 114,6 × 68,9 mm.** A largura inclui a capa aberta e a profundidade inclui a barra da capa.
- **Base:** 106,6 × 66 mm embaixo, cerca de 86 × 42 mm no topo e cerca de 39 mm de altura (aproximadamente 20 % da altura total).
- **Apoio na mesa:** face plana em Z = 0, com 6 643 mm² de contato. Nenhuma geometria fica abaixo de Z = 0.
- **Malha:** 33 volumes e 1 607 368 triângulos.

## Filamentos (cabeçotes)

| Cabeçote | Filamento no 3MF | Material | Volumes |
|---|---|---|---|
| **T0** | 1 | PLA Verde Médio Masterprint (KRYOU ID 31) | CAMISA_VERDE, CAPA_VERDE, PROTETORES_VERDES, CAPACETE_LOGO_VERDE, CAPACETE_TEXTO_CIPAA, CAMISA_LOGO_CRUZ_VERDE, BASE_LOGO_VERDE, BASE_TEXTO_DO_MES_VERDE |
| **T1** | 2 | PLA Branco GTMax3D (KRYOU ID 02) | CAPACETE_BRANCO, CAPACETE_CRUZ_BRANCA, OLHOS_BRANCOS, OLHOS_BRILHO_BRANCO, DENTES_BRANCOS, CAMISA_LOGO_BRANCA, CAMISA_TEXTO_CIPAA_BRANCO, FAIXAS_BRANCAS, FIVELA_BRANCA, BASE_CRUZ_BRANCA, BASE_TEXTO_CIPEIRO_BRANCO |
| **T2** | 3 | PLA Preto Matte Black Soleyin (KRYOU ID 42) | BASE_PRETA, CALCA_PRETA, BOLSOS_PRETOS, CINTO_PRETO, BOTAS_PRETAS, OCULOS_PRETOS, PUPILAS_PRETAS, SOBRANCELHAS_PRETAS, BOCA_PRETA, CABELO_PRETO, PROTETORES_ESTRUTURA_PRETA, PROTETORES_HASTES_PRETAS |
| **T3** | 4 | PLA Nude GTMax3D (KRYOU ID 01) | ROSTO_PELE (rosto, nariz, pescoço), BRACOS_MAOS_PELE (dois braços, mão em V e mão na cintura) |

São exatamente 4 materiais, sem quinta cor. A fivela usa branco, o interior da boca usa preto e não há língua.

O material de cada volume está gravado de duas formas:
- no padrão 3MF, em `basematerials`, com cor de visualização;
- em `Metadata/model_settings.config`, na chave `extruder` 1–4, formato lido por Orca, Bambu Studio e derivados.

### Trocar cor ou cabeçote sem refazer a malha
- **No fatiador:** expanda o objeto, clique na parte (por exemplo, `CAPA_VERDE`) e escolha outro filamento na coluna da parte. Só aquele volume muda.
- **Se a Creator 5 estiver com outra ordem de cabeçotes:** reatribua os 4 filamentos no fatiador. Os nomes indicam a cor de cada volume.
- **No Blender:** altere o *Base Color* do material da coleção para mudar a cor de um grupo inteiro. Para levar uma única parte para outro cabeçote, troque o material do objeto.

## Estratégia de fabricação

**Recomendação: imprimir em uma peça, de pé, com o rosto voltado para a frente.**

Motivos:
- Com 4 cabeçotes, todas as fronteiras de cor ficam fundidas na mesma impressão: rosto/óculos/olhos, logomarcas/capacete/camisa e letras/base.
- Dividir o corpo cortaria essas interfaces multicoloridas e criaria linhas de montagem visíveis.
- Os balanços da capa e da aba do capacete continuariam precisando de suporte mesmo com o corpo dividido.

O conjunto é autoportante e estável: o pedestal tem 6 643 mm² de apoio e as botas assentam por inteiro no topo da base.

Suportes em árvore, removíveis, **somente** nestes pontos:
- **Aba frontal do capacete:** balanço de cerca de 5 a 7 mm.
- **Braço levantado:** sob o cotovelo e o antebraço. Os dedos em V crescem na vertical e não precisam de suporte.
- **Barra da capa:** a partir do topo do pedestal. É o ponto mais baixo da capa, a cerca de 50 mm de altura.
- **Queixo e conchas dos abafadores:** suporte leve.

Aplique **bloqueadores de suporte** no rosto, nos óculos, nos dentes, nas logomarcas CIPAA e no letreiro da base. Coloque a costura nas costas, onde a capa a esconde.

### Perfil inicial (diretriz; calibre na sua máquina)
- **Camadas:** 0,12 mm na geral; 0,08 mm opcional entre Z ≈ 140 e 200 mm (rosto e capacete); primeira camada 0,20 mm.
- **Paredes e topos:** 3 a 4 paredes; 5 a 7 camadas de topo.
- **Preenchimento:** gyroid com 12 a 15 %.
- **Velocidades:** parede externa a 25–35 mm/s; detalhes pequenos (rosto, mãos, letras) a 15–25 mm/s.
- **Torre de purga:** obrigatória com 4 cores.

Temperatura, retração, *offsets* e troca de ferramenta devem vir do perfil calibrado da Creator 5 para estes PLA; nada disso foi assumido aqui.

## Validação executada (`validacao.json`)
1. **Releitura independente:** o 3MF foi relido com **lib3mf**, que não pertence ao gerador. Ele contém 4 materiais, 33 volumes nomeados, 1 montagem e 1 item na build.
2. **Integridade das malhas:**
   - todos os 33 volumes estão **fechados**, com **normais coerentes** e **0 arestas não-manifold**;
   - todos são válidos no manifold3d;
   - restam 7 512 triângulos-agulha com área < 1e‑10 mm² (0,47 % das faces) ao longo das linhas de corte booleano. Eles não abrem a malha, e os fatiadores os descartam.
3. **Sobreposição entre cores:** a interseção booleana exata entre todos os pares de volumes soma **0,048 mm³** em 370 800 mm³. Isso é ruído numérico; as interfaces são coincidentes.
4. **Continuidade física:** são 65 componentes e **todos se ligam à base**. A menor área de contato é a de uma letra do "CIPAA" pequeno, com 10,9 mm².
5. **Espessura local** (raio para dentro a partir de 4 000 pontos da superfície; valores em mm):

   | Parte | Medida | Resultado | Leitura |
   |---|---|---|---|
   | Braços e mãos (inclui os dedos em V) | espessura | 1º percentil 5,5 | dedos robustos |
   | Capa | espessura | 1º percentil 1,2; mediana 2,1 | dentro da faixa de 1,6–2,4 mm |
   | Armação dos óculos | espessura | mediana 2,0; 5º percentil 1,0 | |
   | Faixas brancas | espessura | mediana 1,6 | |
   | Hastes dos abafadores | espessura | 5º percentil 1,8 | |
   | Letreiro "DO MÊS" | relevo | 1,4 | |
   | "CIPAA" pequeno e sobrancelhas | relevo | ~1,0 / ~0,9 | camadas finas sobre a superfície |

   Nos relevos, os valores baixos de percentil vêm das bordas, onde o relevo encontra a superfície; medem altura de relevo, não largura de traço.
6. **Textos** (largura de traço medida no esqueleto das letras; valores em mm):

   | Texto | Traço (mediana) | Traço (5º percentil) | Vão interno mínimo |
   |---|---|---|---|
   | CIPEIRO | 2,54 | 2,27 | — |
   | DO MÊS | 2,11 | 1,25 | — |
   | CIPAA do capacete | 0,80 | 0,50 | 0,41 |
   | CIPAA da camisa | 0,76 | 0,56 | 0,43 |

   O acento do Ê está presente; confira em `cortes_camadas.png`.
7. **Fidelidade:** a sobreposição de silhuetas com a referência (IoU, *intersection over union*, na mesma escala) é **0,86 na frente** e **0,83 no perfil**. A versão anterior tinha 0,85 e 0,66. Veja `sobreposicao_silhuetas.png` e `comparacao_referencia.png`.

**Não executado:** nenhum fatiador. O Flash Studio e o perfil oficial da Creator 5 não estão disponíveis neste ambiente. Por isso **não informo consumo de filamento nem tempo de impressão**.

O volume geométrico sólido por cor é T0 55,7, T1 25,1, T2 267,6 e T3 22,3 cm³. Ele não equivale ao consumo real, porque o fatiador aplica preenchimento parcial. Confira a prévia por camada no fatiador antes de imprimir.

## Limitações conhecidas
- **Regiões ocultas da referência:** foram reconstruídas apenas para dar continuidade. São elas: costas sob a capa, nuca, verso das botas e interior da capa. As orelhas ficam sob os abafadores e não foram modeladas.
- **Diferenças entre as vistas da referência:** as três vistas são imagens independentes e não são perfeitamente coerentes entre si; por exemplo, a altura da aba do capacete muda entre a frente e o perfil. Nesses casos foi adotado um compromisso entre as vistas.
- **Diferenças visíveis que restam:**
  - os dedos em V são um pouco mais finos que na imagem;
  - a capa, na referência, sobe mais por cima dos ombros;
  - as dobras de tecido da calça e da camisa são mais discretas que na ilustração.
- **"CIPAA" pequeno:** as pontas do A ficam com cerca de 0,5 mm. Com bico de 0,4 mm, essas pontas podem arredondar, mas a grafia completa é preservada.
- **Malha facetada:** o modelo é gerado por campos de distância e *marching cubes* com passo de 0,07 a 0,3 mm. A faceta é menor que a largura de linha do bico, mas não é uma malha de subdivisão editável à mão como a de uma escultura manual. Para mudanças de forma, edite os parâmetros em `trofeu_cipeiro/model.py` e regenere.

## Regenerar (pasta `trofeu_cipeiro/`)

Dependências: Python 3 com numpy, scipy, scikit-image, trimesh, manifold3d, lib3mf, rtree e matplotlib; `bpy` 5.x para o .blend; Node com three e Playwright para os renders.

```bash
python3 mesher.py 1.0 malhas.npz
```
```bash
python3 export_3mf.py malhas.npz ../entrega/KRYOU_CIPEIRO_DO_MES_200MM_4CORES.3mf
```
```bash
python3 validate.py ../entrega/KRYOU_CIPEIRO_DO_MES_200MM_4CORES.3mf malhas.npz ../entrega
```
```bash
python make_blend.py ../entrega/KRYOU_CIPEIRO_DO_MES_200MM_4CORES.3mf ../entrega/KRYOU_CIPEIRO_DO_MES_FONTE.blend
```
```bash
NODE_PATH=$(npm root -g) python3 render_views.py ../entrega/KRYOU_CIPEIRO_DO_MES_200MM_4CORES.3mf ../entrega/renders
```

O último comando requer `npm install three` dentro de `trofeu_cipeiro/`.
