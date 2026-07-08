# functions-email

Cloud Function Firebase (Pub/Sub) — envoi d'emails transactionnels Athena Event.

## Structure

```
functions-email/
├── main.py                  # Point d'entrée Firebase + dispatch Pub/Sub
├── config.py                # Constantes SMTP et visuelles (logo, hero)
├── sender.py                # Envoi SMTP centralisé
├── email_senders.py         # Contenu de chaque email (send_xxx)
└── templates/
    ├── base.py              # Styles CSS + enveloppe HTML
    └── components.py        # Composants visuels réutilisables
```

---

## Où modifier quoi

### Changer le logo ou l'image hero
→ `config.py` — variables `LOGO_URL` et `HERO_IMAGE_URL`

### Changer les couleurs / polices / espacements
→ `templates/base.py` — fonction `_base_styles()`

### Modifier le texte ou les blocs d'un email existant
→ `email_senders.py` — fonction `send_xxx()` correspondante

| Type Pub/Sub                    | Fonction                          |
|---------------------------------|-----------------------------------|
| `ACTIVATION_CODE`               | `send_activation_code()`          |
| `ACTIVATION_LINK`               | `send_hostess_activation_link()`  |
| `RESET_PASSWORD`                | `send_reset_password_email()`     |
| `EVENT_AWAITING_APPROVAL`       | `send_event_awaiting_approval()`  |
| `EVENT_APPROVED`                | `send_event_approved()`           |
| `PARTICIPANT_INVITATION_KNOWN`  | `send_participant_invitation_known()` |
| `PARTICIPANT_INVITATION_UNKNOWN`| `send_participant_invitation_unknown()` |

### Modifier la structure hero / footer / cards
→ `templates/components.py` — fonctions `_hero()`, `_footer()`, `_info_card()`, etc.

### Modifier la config SMTP
→ `config.py` — variables `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`  
→ Ces valeurs sont lues depuis les variables d'environnement au démarrage.

---

## Ajouter un nouveau type d'email

**1. Ajouter la fonction d'envoi** dans `email_senders.py` :
```python
def send_mon_email(email: str, ...) -> None:
    rows = (
        _hero(title="...", subtitle="...", email_type_label="...")
        + _body_open(greeting="...", intro="...")
        + _info_card(_info_row("🔔", "Champ", valeur), label="DÉTAILS")
        + _body_close()
    )
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "..."
    msg['From']    = f"Athena Event <{SMTP_USER}>"
    msg['To']      = email
    msg.attach(MIMEText("...", 'plain', 'utf-8'))
    msg.attach(MIMEText(_build_html(rows, preheader="..."), 'html', 'utf-8'))
    _send_email(msg)
```

**2. Importer la fonction** en tête de `main.py` :
```python
from email_senders import send_mon_email
```

**3. Ajouter la validation** dans `process_email()` dans `main.py` :
```python
elif email_type == "MON_TYPE":
    required_fields = ["champ1", "champ2"]
    email_field = data.get("email", "")
```

**4. Ajouter le dispatch** dans `process_email()` dans `main.py` :
```python
elif email_type == "MON_TYPE":
    send_mon_email(email_field, data["champ1"], data["champ2"])
```

---

## Composants disponibles

| Composant          | Description                              |
|--------------------|------------------------------------------|
| `_hero()`          | Bandeau image de fond + logo + badge     |
| `_body_open()`     | Salutation + paragraphe d'intro          |
| `_body_close()`    | Séparateur doré + signature              |
| `_info_card()`     | Encadré jaune avec lignes d'info         |
| `_info_row()`      | Ligne icône + label + valeur             |
| `_cta_button()`    | Bouton call-to-action centré             |
| `_cta_secondary()` | Lien secondaire (ex: Décliner)           |
| `_alert()`         | Encadré warning (jaune) ou danger (rouge)|
| `_code_block()`    | Bloc sombre avec code en grand           |
| `_steps_card()`    | Card avec étapes numérotées              |
| `_footer()`        | Pied de page contacts + copyright        |
| `_build_html()`    | Assemble l'email complet                 |
