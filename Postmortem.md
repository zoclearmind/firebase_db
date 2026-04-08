# Postmortem — [Date] [Description courte]

## Résumé
- Durée : 19h30 → 23h00 (3h30)
- Impact : App inaccessible en prod
- Cause racine : RateLimitFilter bloquait health check Cloud Run

## Timeline
19h30 — Déploiement lancé
19h35 — Première alerte 5xx
20h00 — Identification du problème (logs Cloud Run)
23h00 — Fix déployé, app stable

## Cause racine
RateLimitFilter rejetait les probes Cloud Run (pas de User-Agent)
→ Health check retournait 403
→ Cloud Run ne démarrait pas

## Actions correctives
✅ Fix RateLimitFilter — exclure /actuator/health
✅ Réduire startup_probe initial_delay 60s → 30s
⬜ Ajouter alerte sur health check failures
⬜ Tester localement avant push sur main

## Ce qu'on a appris
- Toujours tester le health check localement
- Vérifier tous les filtres avant déploiement
```

---

## 6. Spring suffit pour ton backend ?

**Oui, ton architecture est solide.** Voici pourquoi :
```
Spring Boot ✅
  → Métier, Auth JWT, OAuth2, API REST
  → SSE Notifications (léger car Pub/Sub fait le lourd)
  → Upload images → GCS direct

Cloud Functions ✅
  → Email (tâche lourde, lente, isolée)
  → PDF génération (CPU intensive)
  → Ne perturbe pas Spring car découplé via Pub/Sub

Pub/Sub ✅
  → Buffer entre Spring et Cloud Functions
  → Si Cloud Function tombe → messages restent dans queue
  → Spring n'attend pas → pas de timeout

Firestore ✅
  → Scalable automatiquement
  → Pas de gestion de pool connexions
  → Parfait pour Cloud Run scale to 0
```

## 7. Roadmap SRE pour toi
```
Niveau 1 (maintenant) ✅
  → App qui tourne en prod
  → Scale to 0
  → Filtres sécurité basiques

Niveau 2 (prochain mois)
  → Alertes Cloud Monitoring
  → Dashboard 4 Golden Signals
  → Postmortem template
  → Tests locaux avant push

Niveau 3 (dans 3 mois)
  → SLO définis (ex: 99.5% uptime, p95 < 500ms)
  → Load testing jour d'event (k6 ou Artillery)
  → Runbooks (procédures écrites pour chaque incident)

Niveau 4 (dans 6 mois)
  → Chaos engineering (tuer une instance volontairement)
  → Capacity planning (combien d'instances pour 10k users)
  → Tracing distribué (Cloud Trace)