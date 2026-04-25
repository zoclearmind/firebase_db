# functions-ticket

Cloud Function Firebase (Pub/Sub) — génération badge ZPL, upload GCS et envoi email de billet.

> Le badge est généré au format **ZPL** pour l'imprimante **Zebra iT4S**.  
> Le QR code est rendu nativement par l'imprimante via la commande `^BQ` — aucune librairie image n'est nécessaire.

## Structure

```
functions-ticket/
├── main.py              # Point d'entrée Firebase + dispatch Pub/Sub
├── config.py            # Constantes SMTP et visuelles (logo, hero)
├── storage.py           # Config émulateur GCS + storage_client
├── pdf_generator.py     # Génération badge PDF 10×5cm + upload GCS
├── email_sender.py      # Contenu et envoi de l'email de billet
└── templates/
    ├── base.py          # Styles CSS + enveloppe HTML
    └── components.py    # Composants visuels réutilisables
```

---

## Où modifier quoi

### Changer le logo ou l'image hero
→ `config.py` — variables `LOGO_URL` et `HERO_IMAGE_URL`

### Changer les couleurs / polices / espacements
→ `templates/base.py` — fonction `_base_styles()`

### Modifier le texte ou les blocs de l'email de billet
→ `email_sender.py` — fonction `send_ticket_email_with_qr()`  
→ Chercher les sections `rows = (...)` et `security_items = [...]`

### Modifier la mise en page du badge ZPL (nom, prénom, entreprise, poste)
→ `pdf_generator.py` — fonction `_build_zpl()`  
→ Les positions sont définies via `^FO x,y` (en dots, 300 DPI = 11.81 dots/mm)  
→ Les polices via `^A0N,hauteur,largeur` (ex: `94,94` ≈ 8mm à 300 DPI)  
→ Les dimensions du badge : `LABEL_WIDTH = 1181` (10cm), `LABEL_HEIGHT = 590` (5cm)  
→ La taille du QR code : `^BQN,2,12` → module 12 dots (~1mm par module à 300 DPI)

**Disposition actuelle de la colonne gauche :**

| Ligne | Champ       | Position `^FO` | Police `^A0N` | Max chars |
|-------|-------------|----------------|---------------|-----------|
| 1     | Prénom      | `44, 100`      | `88,82`       | 12        |
| 2     | Nom         | `44, 220`      | `80,72`       | 13        |
| 3     | Entreprise  | `44, 338`      | `52,52`       | 21        |
| 4     | Poste       | `44, 400`      | `52,52`       | 21        |

> Prénom en haut — Nom en dessous.  
> Entreprise et Poste masqués si vides ou égaux à `"N/A"`.  
> Entreprise toujours affichée en MAJUSCULES.

**Colonne droite (QR code) :**

| Élément     | Valeur                  | Détail                              |
|-------------|-------------------------|-------------------------------------|
| Position QR | `^FO700,60`             | x=700, y=60                         |
| Module QR   | `^BQN,2,20`             | module 20 dots ≈ 1.7mm (~4.1cm QR) |
| Token texte | `^FO700,560^FB437,1,0,C`| centré sous le QR sur 437 dots      |

> Pour inverser Prénom/Nom : échanger les lignes `^FO44,100` et `^FO44,220` dans `_build_zpl()`.

### Changer le bucket GCS cible
→ `main.py` — variable `bucket_name` dans `send_event_ticket()`

### Changer la config émulateur GCS
→ `storage.py` — variable d'env `STORAGE_EMULATOR_HOST`

### Modifier la config SMTP
→ `config.py` — variables `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`

---

## Types acceptés (topic : `prod-email-notifications`)

| Type Pub/Sub                      | Comportement                              |
|-----------------------------------|-------------------------------------------|
| `EVENT_REGISTRATION_CONFIRMED`    | Génère PDF + uploade GCS + envoie email   |
| `RESEND_REGISTRATION_CONFIRMED`   | Skip génération PDF + envoie email seul   |

---

## Champs requis dans le message Pub/Sub

```json
{
  "type": "EVENT_REGISTRATION_CONFIRMED",
  "registrationId": "...",
  "userId": "...",
  "eventId": "...",
  "userEmail": "...",
  "userFirstName": "...",
  "userLastName": "...",
  "eventTitle": "...",
  "eventStartDate": "...",
  "eventLocation": "...",
  "qrCodeToken": "...",
  "companyName": "...",
  "userRole": "..."
}
```
> `companyName` et `userRole` sont optionnels (défauts : `"N/A"` et `"Participant"`).

---

## Ajouter un nouveau type d'email

**1.** Ajouter la fonction dans `email_sender.py`

**2.** Ajouter la validation dans `main.py` :
```python
elif email_type == "MON_TYPE":
    required_fields = ["champ1", "champ2"]
    email_field = data.get("userEmail", "")
```

**3.** Ajouter le dispatch dans `main.py` :
```python
elif email_type == "MON_TYPE":
    send_mon_email(email_field, ...)
```

---

## Composants disponibles

| Composant           | Description                               |
|---------------------|-------------------------------------------|
| `_hero()`           | Bandeau image de fond + logo + badge      |
| `_body_open()`      | Salutation + paragraphe d'intro           |
| `_body_close()`     | Séparateur doré + signature               |
| `_info_card()`      | Encadré jaune avec lignes d'info          |
| `_info_row()`       | Ligne icône + label + valeur              |
| `_qr_block()`       | Bloc sombre avec QR code inline (CID)     |
| `_security_card()`  | Card rouge avec consignes de sécurité     |
| `_footer()`         | Pied de page contacts + copyright         |
| `_build_html()`     | Assemble l'email complet                  |
