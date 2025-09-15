# MatchTrex Async Architecture Implementation Plan

## 🎯 Ziel
Umbau von synchroner zu asynchroner Architektur für lange Pipeline-Prozesse mit Real-time Status Updates.

## 📋 Übersicht
- **Aktuell**: Frontend → Supabase Insert → Backend manuell getriggert
- **Neu**: Frontend → Backend API → Job Queue → WebSocket Updates → Database Update

---

## Phase 1: Backend Foundation (Parallelimplementierung)
> **Ziel**: Neue Async-Endpunkte hinzufügen, ohne bestehende Funktionalität zu brechen

### ✅ Step 1.1: Dependencies erweitern
- [x] `requirements.txt` mit Async-Libraries erweitern (python-socketio, websockets, aiofiles)
- [x] Virtual Environment aktualisieren
- [x] Kompatibilität testen
- **Test**: ✅ Backend startet weiterhin normal
- **Rollback**: `git checkout requirements.txt`

### ✅ Step 1.2: Job Queue Models hinzufügen
- [x] Pydantic Models für Jobs erstellen (`JobCreateRequest`, `JobStatusResponse`, `JobProgress`, etc.)
- [x] In-Memory Job Storage (Dict) als MVP
- [x] Job ID Generation System
- **Test**: Models importieren ohne Fehler
- **Rollback**: Neue Files löschen

### ✅ Step 1.3: Neue API Endpunkte (parallel zu bestehenden)
- [x] `POST /api/jobs` → Job erstellen (sofortige Antwort) ✅
- [x] `GET /api/jobs/{job_id}` → Job Status abfragen ✅
- [x] `GET /api/jobs` → Alle Jobs auflisten (Debug/Admin) ✅
- [x] Bestehende `/search` Endpunkte bleiben unverändert ✅
- **Test**: ✅ Alle neuen Endpunkte funktionieren, alte API weiterhin verfügbar
- **Rollback**: Neue Routes auskommentieren

---

## Phase 2: Background Job System
> **Ziel**: Async Job Processing implementieren

### ✅ Step 2.1: Simple Background Task System
- [x] ThreadPoolExecutor für Background Jobs (JobWorkerManager mit max 2 workers) ✅
- [x] Job Status Management (pending → running → completed/failed) ✅
- [x] Background Pipeline mit Progress Updates (5 Steps: init → scraping → download → AI → email) ✅
- [x] WebSocket Broadcasting Framework (placeholder) ✅
- [x] Graceful Shutdown Support ✅
- **Test**: ✅ Job wird sofort async gestartet, Live Status Updates alle 2s, Complete Results nach 10s
- **Rollback**: Threading Code entfernen

### ✅ Step 2.2: Pipeline Integration
- [x] Pipeline Wrapper erstellt (`pipeline_wrapper.py`) ✅
- [x] Job Worker mit Pipeline Progress Callbacks integriert ✅
- [x] Realistische Pipeline Steps (init → scraping → download → AI → email) ✅
- [x] Live Progress Updates alle 3 Sekunden ✅
- [x] Complete Job Results mit Candidate URLs ✅
- [x] Error Handling für Background Jobs ✅
- **Test**: ✅ Vollständige Pipeline läuft async in 10s mit Live Updates
- **Rollback**: Alte Pipeline-Calls wiederherstellen

### ✅ Step 2.3: Job Persistence
- [x] Supabase Client Integration mit graceful degradation ✅
- [x] Job Creation Persistence (create_job_entry) ✅
- [x] Job Status Updates Persistence (update_job_status) ✅
- [x] Supabase Service Module (`supabase_service.py`) ✅
- [x] Database Connection Testing (`/api/supabase/test`) ✅
- [x] Job History Endpunkt (mit Route-Fix) ✅
- **Test**: ✅ Jobs persistieren korrekt, System läuft mit/ohne DB
- **Rollback**: Database writes optional machen

---

## Phase 3: Real-time Updates
> **Ziel**: WebSocket Integration für Live Status Updates

### ✅ Step 3.1: WebSocket Server Setup
- [ ] FastAPI WebSocket Endpunkt `/ws/{job_id}`
- [ ] Connection Management
- [ ] Basic Message Broadcasting
- **Test**: WebSocket Verbindung von Frontend möglich
- **Rollback**: WebSocket Endpunkte entfernen

### ✅ Step 3.2: Job Status Broadcasting
- [ ] Job Status Updates via WebSocket senden
- [ ] Progress Updates (% completed, candidates found, etc.)
- [ ] Error/Completion Notifications
- **Test**: Status Updates kommen im Frontend an
- **Rollback**: WebSocket calls auskommentieren

---

## Phase 4: Frontend Integration
> **Ziel**: Frontend für Async Jobs umbauen

### ✅ Step 4.1: Async Job Creation UI
- [ ] SearchForm um API-Call erweitern (parallel zu Supabase)
- [ ] Job ID handling im Frontend
- [ ] Loading States für Job Creation
- **Test**: Job wird erstellt, Job ID wird erhalten
- **Rollback**: Alte Supabase-only Version wiederherstellen

### ✅ Step 4.2: Real-time Status Display
- [ ] WebSocket Client im Frontend
- [ ] Progress Bar/Status Updates in UI
- [ ] Live Candidate Counter
- **Test**: Status Updates werden in UI angezeigt
- **Rollback**: WebSocket Code auskommentieren

### ✅ Step 4.3: Job Results Integration
- [ ] Job Results von API statt nur Supabase laden
- [ ] Error Handling für failed Jobs
- [ ] Job History/Retry Funktionalität
- **Test**: Complete Flow funktioniert end-to-end
- **Rollback**: Alte Supabase-Queries wiederherstellen

---

## Phase 5: Production Readiness
> **Ziel**: System für Production optimieren

### ✅ Step 5.1: Error Handling & Resilience
- [ ] Job Retry Mechanismus
- [ ] WebSocket Reconnection Logic
- [ ] Graceful Degradation (fallback zu Polling)
- **Test**: System funktioniert bei Fehlern robust
- **Rollback**: Retry Logic deaktivieren

### ✅ Step 5.2: Performance & Scaling
- [ ] Job Queue Limits (max concurrent jobs)
- [ ] WebSocket Connection Limits
- [ ] Memory Management für long-running Jobs
- **Test**: System performant bei mehreren Jobs
- **Rollback**: Limits erhöhen/entfernen

### ✅ Step 5.3: Monitoring & Logging
- [ ] Job Metrics und Logging
- [ ] Health Check für Job System
- [ ] Admin Interface für Job Management
- **Test**: Monitoring funktioniert korrekt
- **Rollback**: Logging optional machen

---

## Phase 6: Cleanup & Migration
> **Ziel**: Alte synchrone Implementierung entfernen

### ✅ Step 6.1: Dual System Testing
- [ ] A/B Testing zwischen alter und neuer Implementierung
- [ ] Performance Vergleich
- [ ] Feature Parity Check
- **Test**: Neue Implementierung ist vollständig äquivalent
- **Rollback**: Bei altem System bleiben

### ✅ Step 6.2: Migration & Cleanup
- [ ] Frontend komplett auf neue API umstellen
- [ ] Alte `/search` Endpunkte deprecaten
- [ ] Code Cleanup und Dokumentation
- **Test**: Nur neue API wird verwendet
- **Rollback**: Alte Endpunkte wieder aktivieren

---

## 🛡️ Robustheit-Strategien

### Nach jedem Step:
1. **Funktionstest**: Alte Features funktionieren weiter
2. **Integration Test**: Neue Features funktionieren
3. **Commit**: Änderungen committen für Rollback-Möglichkeit

### Kritische Rollback-Punkte:
- Nach Phase 1: Alles läuft wie vorher
- Nach Phase 2: Jobs funktionieren, aber ohne UI
- Nach Phase 4: Complete neue Pipeline funktioniert
- Nach Phase 6: Migration abgeschlossen

### Risk Mitigation:
- **Feature Flags**: Neue Features togglebar machen
- **Database Migrations**: Reversible Schema Changes
- **API Versioning**: `/api/v1/` vs `/api/v2/`

---

## 📊 Success Metrics

- [ ] Job Creation: < 200ms Response Time
- [ ] WebSocket Updates: < 1s Latency
- [ ] Pipeline Reliability: > 95% Success Rate
- [ ] User Experience: Real-time Status Updates
- [ ] System Stability: 0% Downtime während Migration

---

## 🚀 Getting Started

**Next Step**: Phase 1.1 - Dependencies erweitern
```bash
cd backend
# Backup current state
git add -A && git commit -m "Backup before async implementation"

# Start with Phase 1.1
# Update requirements.txt...
```

---
*Erstellt: 2025-09-15 | Status: Ready for Implementation*