# GD4H: cas d’usage qualité de l'eau du robinet

## Le Green Data for Health

Le Green Data for Health (GD4H) est un projet inscrit dans le 4ème Plan National Santé Environnement qui a pour objectif de faciliter la mobilisation et la valorisation, par les chercheurs et les experts, des données environnementales au service de la santé-environnement.

## Géo-localisation des unités de distribution

Un des cas d'usage identifiés est l'étude des impacts de la qualité de l'eau potable. Ces données sont collectées dans la base SISE-Eaux des Agences Régionales de Santé (ARS) et mises à disposition sur le site [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/resultats-du-controle-sanitaire-de-leau-distribuee-commune-par-commune/).

Les ARS produisent également des cartes des unités de distribution et le mettent à disposition sur le site [AtlaSante](https://carto.atlasante.fr/1/ars_metropole_udi_infofactures.map).

Ce module a pour objectif de permettre une jointure entre les deux lots de données.

## Installation

```
git clone https://github.com/blenzi/GD4H_eau.git
pip install numpy pandas matplotlib geopandas
```

- Télécharger les données de la base SISE-Eaux disponibles sur le site [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/resultats-du-controle-sanitaire-de-leau-distribuee-commune-par-commune/). Ouvrir le contenu des fichiers zip dans `data/DIS_2016`, etc.
- Télécharger les cartes d'[AtlaSante](https://carto.atlasante.fr/1/ars_metropole_udi_infofactures.map) en format JSON, projection WGS84 - GPS (EPSG 4326) [EPSG:4326] sur `data/AtlaSante_<region>`. La liste de fichiers utilisés se trouve sur `data/info_AtlaSante.csv`.

## Fichiers

- `data/info_AtlaSante.csv`: contient la liste des régions, fichers avec les cartes d'AtlaSante, année correspondante et les champs utilisés dans la jointure
- `checks_AtlaSante.ipynb`: vérification des cartes d'AtlaSante. Met en évidence les entrées dupliquées et/ou sans géométrie associée.
- `jointure_UDI_AtlaSante.ipynb`: réalise la jointure entre les unités de distributions (UDIs) listées dans data.gouv et AtlaSanté. Met en évidence les entrées communes et exclusives à chacune des bases.
- `adresse.ipynb`: permet d'identifier l’unité de distribution et les résultats de prélèvement pour une adresse en France (en Bretagne pour l'instant), en s'appuyant sur l'API [hub'eau](https://hubeau.eaufrance.fr/page/api-qualite-eau-potable#/).
