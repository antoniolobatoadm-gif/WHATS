# KRYOU – Troféu "CIPEIRO DO MÊS" – 200 mm – 4 cores – Creator 5

Arquivo principal: `KRYOU_Cipeiro_do_Mes_200mm_4C_Creator5.3mf`

## Medidas (medidas no arquivo exportado, relido com lib3mf)
- X × Y × Z = **116,52 × 70,57 × 200,00 mm**. O X inclui a capa aberta; o pedestal sozinho mede cerca de 107 × 71 mm.
- Face de apoio plana em Z = 0, com 7 322 mm² de contato com a mesa. Nenhuma geometria fica abaixo de Z = 0.
- Um único item na mesa: o objeto `KRYOU_Cipeiro_do_Mes`, com 32 volumes nomeados.
- A escala foi uniforme nos três eixos (fator 0,9945 sobre o modelo esculpido).

## Filamentos
| Filamento no projeto | Material | Volumes |
|---|---|---|
| 1 | Verde Médio Masterprint (KRYOU ID 31) | Camisa, Capa, Conchas_Abafadores, Emblema_Capacete_Circulo, Texto_CIPAA_Capacete, Emblema_Peito_Cruz, Emblema_Base_Circulo, Letreiro_DO_MES (inclui Ê e traços) |
| 2 | Preto Matte Black Soleyin (KRYOU ID 42) | Base, Calca, Botas, Cinto, Armacao_Oculos, Almofadas_Abafadores, Suportes_Abafadores, Cabelo, Sobrancelhas, Pupilas, Boca_Interior |
| 3 | Branco GTMax3D (KRYOU ID 02) | Capacete, Emblema_Capacete_Cruz, Olhos_Brancos, Brilho_Olhos, Dentes, Faixas_Calca, Fivela, Letreiro_CIPEIRO, Emblema_Peito_Circulo, Texto_CIPAA_Peito, Emblema_Base_Cruz |
| 4 | Nude GTMax3D (KRYOU ID 01) | Pele_Rosto (rosto, nariz, pescoço), Pele_Bracos_Maos |

O arquivo registra o material de cada volume de duas formas:
- No padrão 3MF: `basematerials`, índices 1 a 4, com cor de visualização.
- Em `Metadata/model_settings.config`: chave `extruder` = 1 a 4, formato lido por OrcaSlicer, Bambu Studio e derivados, como o Orca-FlashForge.

A numeração do fatiador corresponde 1:1 à tabela acima.

## Trocar a cor de uma parte (fluxo do Orca, base do fatiador FlashForge)
1. Abra o .3mf. O troféu aparece como um objeto. Expanda-o na lista de objetos para ver as 32 partes.
2. Clique na parte, por exemplo `Capa`. Na coluna de filamento dela, escolha outro slot. Só aquele volume muda; a `Camisa` continua no slot 1.
3. Se o fatiador abrir com menos de 4 filamentos ou ignorar a coluna `extruder`, adicione os 4 slots na ordem da tabela e reatribua por parte. Os nomes dos volumes indicam a cor.

## Suportes recomendados (removíveis, em árvore, só onde houver contato)
- Sob a aba frontal do capacete, que tem cerca de 5 mm de balanço.
- Sob o cotovelo e o antebraço do braço levantado. Os dedos em V crescem na vertical e não precisam de suporte.
- Sob a barra da capa, a partir do topo do pedestal. É o ponto mais baixo da capa, a cerca de 61 mm de altura.
- Sob o queixo, em menor quantidade. O pescoço tem um filete de transição.
- Use bloqueadores de suporte no rosto, nos óculos, nas letras e no peito.

Base, botas, pernas, tronco, cabeça e mão no quadril são autoportantes.

## Validação executada (`validacao.json`, `cortes_camadas.png`)
- O 3MF foi relido com lib3mf, que é independente do gerador. Ele contém 4 materiais, 32 volumes com nome, 1 montagem e 1 item na build.
- Todos os volumes estão fechados, com normais coerentes, 0 arestas não-manifold e 0 faces degeneradas. Todos são válidos no manifold3d.
- A sobreposição entre volumes, medida por interseção booleana exata entre todos os pares, soma 0,029 mm³ em 375 977 mm³. Isso é ruído numérico; as interfaces são coincidentes.
- Continuidade física: 65 componentes, todos ligados à base por contatos de pelo menos 1 mm². A menor área de contato é a de uma letra do "CIPAA", com 11 mm².
- Textos:
  - "CIPEIRO": traço mediano de 2,55 mm.
  - "DO MÊS": traço mediano de 2,11 mm, com relevo de 0,8 mm sobre a face inclinada.
  - "CIPAA" pequenos: traço mediano de 0,76 a 0,87 mm, com contraformas abertas de no mínimo 0,43 mm.
- A simplificação das malhas tem tolerância de 0,01 mm (desvio máximo medido abaixo de 0,02 mm).

**Não executado:** nenhum fatiador. Flash Studio e o perfil oficial da Creator 5 não estão disponíveis neste ambiente, e a execução do OrcaSlicer baixado foi bloqueada. Confira a prévia por camada no seu fatiador antes de imprimir.

## Limitações
- As regiões ocultas da referência foram reconstruídas: costas, nuca e parte de trás da capa e das botas. As orelhas ficam cobertas pelos abafadores e não foram modeladas.
- No "CIPAA" pequeno, as pontas do A ficam com cerca de 0,55 mm (5º percentil). Com bico de 0,4 mm, as pontas podem arredondar, mas a grafia completa é preservada.
- O interior da boca é preto, porque não há vermelho entre os quatro filamentos.

## Regenerar
`trofeu_cipeiro/`: `mesher.py`, `export_3mf.py`, `validate.py` (Python com numpy, scipy, scikit-image, trimesh, manifold3d, lib3mf).
