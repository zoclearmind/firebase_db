# Installer dependecie python

```bash
cd ~/firebase_db

for dir in functions-email-firebase functions-ticket-firebase functions-brochure-firebase; do
    echo "Setting up venv in $dir..."
    cd $dir
    python3.12 -m venv venv
    source venv/bin/activate
    python3.12 -m pip install -r requirements.txt  
    deactivate
    cd ..
done
```

# et lancer sur commande

```bash
npm install
```

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
export FIRESTORE_EMULATOR_HOST=localhost:8082                   
export SPRING_PROFILES_ACTIVE=dev
```

```bash
export $(grep -v '^#' .env.local | xargs)
```

```bash
echo $GOOGLE_CLIENT_ID
```

```bash
./mvnw spring-boot:run
```


