# Compteurs communicants et télérelève (AMI)

**Référence :** DOC-AMI · **Version :** 1.8 · **Date :** 2026-05-20
**Propriétaire :** Direction Digital & SI · **Catégorie :** Digital

Architecture AMI, collecte toutes les 15 minutes, supervision des pertes et cybersécurité des concentrateurs.

## Article 1

Le compteur communicant transmet la courbe de charge toutes les 15 minutes via un concentrateur de quartier. Les données sont agrégées au niveau du départ et du poste source.

## Article 2

La télérelève permet de détecter les pertes non techniques : branchements illicites, compteurs trafiqués, erreurs de relevé. Un écart supérieur à 3 % entre l'énergie injectée et l'énergie facturée déclenche une analyse.

## Article 3

Les concentrateurs sont segmentés sur un VLAN dédié et communiquent avec la plateforme de collecte via TLS mutuel. Les mots de passe par défaut sont interdits et les firmwares sont signés.

## Article 4

La disponibilité de la chaîne de collecte doit être supérieure à 98 %. Une panne de concentrateur est traitée comme un incident P2 si elle concerne plus de 500 compteurs.
