# Prévision de la charge à J+1 et gestion des pointes

**Référence :** DOC-PREVISION · **Version :** 2.9 · **Date :** 2026-09-11
**Propriétaire :** Direction Prévision & Dispatching · **Catégorie :** Exploitation

Modèle de prévision, variables météo, événements, seuils d'alerte et marge de réserve.

## Article 1

La prévision J+1 est produite chaque jour à 11 h à partir des historiques de charge, de la météo (température, humidité, vent) et du calendrier (jours fériés, événements, ramadan).

## Article 2

Une température maximale supérieure à 34 °C augmente la pointe de 6 à 9 % selon la région. Une baisse de 5 °C en hiver augmente la pointe de 4 à 7 %.

## Article 3

Le seuil d'alerte est atteint lorsque la pointe prévisionnelle dépasse 92 % de la capacité disponible. Le seuil critique est de 97 %. Entre 92 % et 97 %, le dispatcher active les réserves et prépare un plan de délestage.

## Article 4

La marge de réserve minimale est de 8 % de la pointe prévisionnelle. Elle peut être abaissée à 4 % pendant une heure maximum, avec validation du directeur d'exploitation.
