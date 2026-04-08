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
 npx firebase emulators:start --project demo-event-app
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
```