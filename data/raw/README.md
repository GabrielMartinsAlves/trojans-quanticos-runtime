# Dados brutos (não versionados)

Os circuitos golden vêm do dataset de Souza Filho, Hayashi e Ferreira (SBSeg 2026):
<https://github.com/apenas-will/IC-QT-2026>

O repositório original não declara licença, então os arquivos não são copiados para cá.
Para usar localmente:

```powershell
cd data\raw
git clone https://github.com/apenas-will/IC-QT-2026.git
```

Os circuitos golden ficam em `IC-QT-2026/results/datasets/dataset_trojan_final/full/`
(pasta `golden/` e arquivo `metadata.csv`). A seleção usada no artigo vai em
`data/selecao.csv`, que é versionado.
