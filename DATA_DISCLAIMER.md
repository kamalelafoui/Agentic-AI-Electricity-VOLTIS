# ⚠️ Provenance des données — VOLTIS

## Réponse courte

**Toutes les données de VOLTIS sont simulées.**

Aucune API réelle n'est appelée. Aucune donnée ONEE, ANRE, MASEN, SCADA, AMI,
MongoDB Atlas ou autre source opérateur n'est utilisée. Aucun scraping n'a été
réalisé. Aucun client réel n'est présent dans le projet.

---

## 1. Origine exacte

Toutes les données sont générées par le script :

```text
scripts/build_data.py
```

avec une graine aléatoire fixe :

```python
random.seed(20261112)
```

Cette graine garantit que les mêmes fichiers sont régénérés à l'identique.

### Fichiers générés

| Fichier | Contenu | Mode |
|---|---|---|
| `data/regions.json` | 8 régions, clients, consommation, pointe, pertes, SAIDI/SAIFI | Simulé |
| `data/load_curve.csv` | 5 760 lignes horaires sur 30 jours | Simulé |
| `data/monthly_consumption.csv` | 96 lignes mensuelles | Simulé |
| `data/outages.csv` | 72 incidents sur 90 jours | Simulé |
| `data/customers.json` | 24 clients suivis | Simulé |
| `data/tariffs.json` | 5 grilles tarifaires | Simulé |
| `data/corpus.json` | 12 documents / 49 chunks | Rédigé pour la démo |
| `data/benchmarks.json` | 5 tâches, scores Reflexion | Calculé sur le workflow |

### Ce qui est simulé

- Les consommations, pointes, pertes et indicateurs de continuité.
- Les incidents, départs, causes, durées et clients affectés.
- Les clients, segments, factures et niveaux de satisfaction.
- Les courbes de charge et les températures.
- Les documents du corpus (procédures internes fictives).
- Les résultats du benchmark Reflexion.

### Ce qui n'est pas simulé

- Le code Python, les protocoles MCP/A2A, le workflow LangGraph et les calculs.
- Les scores du Critic sont calculés réellement sur les réponses produites.
- Les appels HTTP entre le dashboard, MCP et A2A sont réels (en local).

---

## 2. Pourquoi des données simulées ?

1. **Confidentialité** : les données de réseau, de clients et d'incidents sont sensibles.
2. **Reproductibilité** : un jury ou un correcteur peut relancer le projet sans accès externe.
3. **Démonstration** : les volumes et scénarios sont contrôlés pour illustrer les agents.
4. **Absence d'API publique** : il n'existe pas d'API publique ouverte donnant accès
   aux incidents, aux courbes de charge et aux factures d'un opérateur réel.

Les valeurs sont **calibrées sur des ordres de grandeur publics** (TWh, MW, millions
de clients, SAIDI, pertes) mais ne représentent **aucune situation réelle**.

---

## 3. Où brancher des données réelles ?

Le projet est conçu pour que le remplacement soit localisé.

### 3.1 Point unique d'accès

Toutes les fonctions métier sont dans :

```text
shared/electricity_core.py
```

Les outils MCP, les agents A2A et LangGraph passent par ces fonctions.
Il suffit de remplacer leur implémentation par des appels API.

### 3.2 Correspondance API réelle

| Fonction actuelle | Source réelle possible |
|---|---|
| `national_kpis()` | API datahub ONEE / ANRE / tableau de bord régulateur |
| `regions()` | Référentiel régional officiel |
| `load_curve()` | API SCADA / dispatching / compteurs AMI |
| `outages()` | GMAO / ticketing incidents / SCADA |
| `customers()` | CRM / système de facturation |
| `tariffs()` | Grille tarifaire officielle |
| `search_documents()` | Base documentaire interne (GED) |
| `forecast_load()` | Modèle de prévision interne ou API météo + historique |

### 3.3 Ce qu'il faut ajouter

- Un connecteur HTTP par source (`requests`, `httpx`).
- Une authentification (Bearer, mTLS, OAuth2).
- Un mapping des schémas réels vers les schémas MCP actuels.
- Une gestion des erreurs et un cache.
- Des tests de non-régression sur les données.
- Une journalisation des appels et des latences.

### 3.4 Ce qu'il ne faut pas changer

- Les noms et schémas des outils MCP.
- Les contrats des agents A2A.
- Le format des réponses du dashboard.

Ainsi, le remplacement des données ne casse ni les agents ni l'interface.

---

## 4. Mention à afficher

Le dashboard, la documentation et la présentation doivent indiquer :

> **Données 100 % synthétiques — aucune API réelle, aucun client réel, aucun accès
> ONEE/ANRE/SCADA. Les valeurs sont calibrées sur des ordres de grandeur publics
> uniquement.**

Cette mention est présente dans :
- le pied de page du dashboard ;
- la page « Vue d'ensemble » ;
- la documentation finale (section 4.4) ;
- la présentation finale (slide Données et slide Limites) ;
- le fichier `Agentic_AI_Electricity_VOLTIS.json` (bloc `volt_is.data`).

---

## 5. Conclusion

Le projet ne prétend pas utiliser des données réelles. Il démontre une
**architecture agentique fonctionnelle** sur un jeu de données synthétique
réaliste. Le passage à la production nécessite des conventions d'accès, une
validation métier et une phase de tests avec l'opérateur.
