## Installation varible python et lance projet cloud fuction
```bash
python -m venv venv
```

## l’activer :
```bash
venv\Scripts\activate
```

## Installer toutes les dépendances listées dans le fichier requirements.txt
```bash
pip install -r requirements.txt
```

## Login pour emulator firebase local

```bash
npx firebase init
```

# Installer dependecie python

```bash
pip install -r requirements.txt
```

# et lancer sur commande
```bash

 npx firebase emulators:start --project demo-event-app --import=./emulator-data --export-on-exit=./emulator-data
```

# Créer les topics
```bash
curl -X PUT "http://localhost:8085/v1/projects/demo-event-app/topics/notifications-inbound"
curl -X PUT "http://localhost:8085/v1/projects/demo-event-app/topics/sse-delivery-topic"
```

# Créer les subscriptions
```bash
curl -X PUT "http://localhost:8085/v1/projects/demo-event-app/subscriptions/notifications-inbound-sub" \
  -H "Content-Type: application/json" \
  -d '{"topic": "projects/demo-event-app/topics/notifications-inbound", "ackDeadlineSeconds": 10}'

curl -X PUT "http://localhost:8085/v1/projects/demo-event-app/subscriptions/sse-delivery-sub" \
  -H "Content-Type: application/json" \
  -d '{"topic": "projects/demo-event-app/topics/sse-delivery-topic", "ackDeadlineSeconds": 10}'
```

# Creation variabale local en spring pas ici

```bash
$env:FIRESTORE_EMULATOR_HOST="localhost:8082"                        
$env:SPRING_PROFILES_ACTIVE="dev"
```

```bash
Get-Content .env.local | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
}
```

```bash
echo $env:GOOGLE_CLIENT_ID

mvn spring-boot:run


 ./mvnw spring-boot:run

ngrok http --domain=overexert-gloomily-exchange.ngrok-free.dev 8080

curl -X POST https://overexert-gloomily-exchange.ngrok-free.dev/webhook/messenger \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "messaging": [{
        "sender": { "id": "27135442052716717" },
        "referral": { "ref": "1484107550130618" },
        "message": { "text": "Bonjour" }
      }]
    }]
  }'



curl "https://graph.facebook.com/v21.0/me/conversations?fields=participants&access_token=EAAVt8svNVyIBRtcaJHWGlBssKnRLuFL9c8U8I8ZCCVvZA51L4IWDhs0WNwwzVhK6u8FgEB5IvRZC7X18LEVYgTjIIge9c012rDckxODLV9woUltPuXi7kKLv3CCzYVRDhTUdg1gghvGH2IXAoGKyPu8L4sppfHZBia1RvsXKGh37GZBQew5pSc8zseVtFWFdf9ZAdKVgZDZD"
```