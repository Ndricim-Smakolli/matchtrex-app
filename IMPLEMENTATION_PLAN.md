# MatchTrex Frontend-Backend Integration - Vollständige Implementierung

## Aktueller Status-Überblick

### ❌ Gefundene Probleme
1. **Frontend-Backend Disconnect**: Frontend macht nur Supabase Insert, kein API-Call zum Backend
2. **Backend Data Layer Missing**: Backend hat keine Supabase-Integration
3. **Pipeline Implementation Missing**: Backend `run_pipeline()` ist nur Mock-Code
4. **Status Updates Missing**: Backend kann Status nicht in Supabase updaten
5. **Email Integration Incomplete**: Keine Email nach Job-Completion

### ✅ Funktioniert bereits
- ✅ Frontend: Supabase Insert für neue Searches
- ✅ Frontend: Anzeige der Suchhistorie aus Supabase
- ✅ Backend: Test-Email Endpoint
- ✅ Backend: FastAPI Grundstruktur
- ✅ Backend: MVP Pipeline-Code (mvp.py)

## Gewünschter Workflow
1. **Frontend** → Neue Suche in Supabase speichern (status="pending")
2. **Frontend** → API-Call an Backend mit Supabase-ID
3. **Backend** → Suche aus Supabase laden über ID
4. **Backend** → Status auf "processing" setzen in Supabase
5. **Backend** → MVP Pipeline ausführen (sehr lange)
6. **Backend** → Ergebnisse in Supabase speichern
7. **Backend** → Status auf "completed" setzen
8. **Backend** → Email an recipient_email senden
9. **Frontend** → Status-Updates in Echtzeit anzeigen

---

## Phase 1: Frontend-Backend Connection
**Ziel**: Frontend soll nach Supabase Insert einen API-Call an Backend machen

### 1.1 Frontend Anpassungen
**Datei**: `frontend/src/components/SearchForm.tsx`

**Änderungen**:
```typescript
// Nach dem Supabase Insert:
const { data: insertedData, error } = await supabase
  .from('searches')
  .insert([searchData])
  .select('id')
  .single();

if (error) throw error;

// NEU: API-Call an Backend
const backendUrl = import.meta.env.VITE_BACKEND_URL ||
  (window.location.hostname === 'app.72.60.131.65.sslip.io'
    ? 'http://api.72.60.131.65.sslip.io'
    : 'http://localhost:3001');

const response = await fetch(`${backendUrl}/api/jobs/start-from-supabase`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    search_id: insertedData.id
  })
});

if (!response.ok) {
  throw new Error('Failed to start backend processing');
}

const { job_id } = await response.json();
console.log('Backend job started:', job_id);
```

### 1.2 Backend Endpoint hinzufügen
**Datei**: `backend/api.py`

**Neuer Endpoint**:
```python
@app.post("/api/jobs/start-from-supabase")
async def start_job_from_supabase(request: dict, background_tasks: BackgroundTasks):
    """Start processing a search job from Supabase ID"""
    search_id = request.get('search_id')
    if not search_id:
        raise HTTPException(status_code=400, detail="search_id required")

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Start background processing
    background_tasks.add_task(process_search_from_supabase, job_id, search_id)

    return {"job_id": job_id, "status": "started"}
```

---

## Phase 2: Backend Supabase Integration
**Ziel**: Backend kann Supabase lesen und schreiben

### 2.1 Supabase Dependencies hinzufügen
**Datei**: `backend/requirements.txt`

```
# Bestehende Dependencies...
supabase==2.10.0
python-dotenv==1.0.1
```

### 2.2 Supabase Client Setup
**Datei**: `backend/supabase_client.py` (NEU)

```python
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
```

### 2.3 Environment Variables
**Datei**: `backend/.env` (NEU - nicht committen!)

```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
MISTRAL_API_KEY=83pVv0mVbOBUwSRmoPBaWg6UUkNZunTP
TWOCAPTCHA_KEY=22e969001c9ae2824614794f69230e68
EMAIL_USER=aauxilliary4@gmail.com
EMAIL_PASS=kxoc ajnf pked zhwp
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### 2.4 Backend API Anpassungen
**Datei**: `backend/api.py`

```python
from supabase_client import supabase

async def process_search_from_supabase(job_id: str, search_id: str):
    """Process search job from Supabase"""
    try:
        # 1. Load search from Supabase
        response = supabase.table('searches').select('*').eq('id', search_id).execute()
        if not response.data:
            raise Exception(f"Search {search_id} not found")

        search_data = response.data[0]

        # 2. Update status to processing
        supabase.table('searches').update({
            'status': 'processing'
        }).eq('id', search_id).execute()

        # 3. Run pipeline (implementiert in Phase 3)
        results = await run_search_pipeline(search_data)

        # 4. Update with results (implementiert in Phase 4)
        # 5. Send email (implementiert in Phase 5)

    except Exception as e:
        # Update status to failed
        supabase.table('searches').update({
            'status': 'failed',
            'error': str(e)
        }).eq('id', search_id).execute()
```

---

## Phase 3: Pipeline Integration
**Ziel**: Echte MVP Pipeline in Backend API integrieren

### 3.1 MVP Pipeline Anpassungen
**Datei**: `backend/mvp.py`

**Neue Funktion hinzufügen**:
```python
def run_search_pipeline_api(search_params: dict) -> dict:
    """
    API-Version der Pipeline - nimmt dict Parameter und gibt dict zurück
    """
    try:
        print(f"\n🎯 Starting MatchTrex Search Pipeline (API Mode)")
        print(f"   Keywords: {search_params.get('search_keywords')}")
        print(f"   Location: {search_params.get('location')}")
        print(f"   Target: {search_params.get('target_candidates', 100)} candidates")

        # Parameter extrahieren
        search_keywords = search_params.get('search_keywords', '')
        location = search_params.get('location', '')
        max_radius = int(search_params.get('max_radius', 25))
        target_candidates = int(search_params.get('target_candidates', 100))
        resume_last_updated_days = int(search_params.get('resume_last_updated_days', 30))
        system_prompt = search_params.get('system_prompt', '')
        user_prompt = search_params.get('user_prompt', '')

        # Bestehende Pipeline-Logik verwenden
        resume_filter = calculate_unix_timestamp_ms(resume_last_updated_days)
        all_candidates = []

        # Progressive radius search (wie in main())
        for radius in range(5, max_radius + 1, 5):
            print(f"   Searching radius {radius}km...")
            response = make_indeed_request(radius, search_keywords, resume_filter, location)
            if response:
                candidates = extract_candidate_data(response)
                all_candidates.extend(candidates)
                print(f"   Found {len(candidates)} candidates at {radius}km")

                if len(all_candidates) >= target_candidates:
                    break

        # Remove duplicates
        unique_candidates = list(set(all_candidates))
        print(f"   Total unique candidates found: {len(unique_candidates)}")

        # Download CV files
        print("\n3. Downloading CV HTML files...")
        downloaded_files = download_cv_html_files(unique_candidates, target_candidates)
        print(f"   Downloaded {len(downloaded_files)} CV files")

        # Process with AI
        print("\n4. Processing CV files with MistralAI...")
        filtered_candidates = process_saved_cv_files(downloaded_files, system_prompt, user_prompt)

        # Cleanup
        if os.path.exists("temp_CVs"):
            shutil.rmtree("temp_CVs")
            print("   Cleaned up temp_CVs directory")

        # Return results
        return {
            "candidates": filtered_candidates,
            "total_found": len(unique_candidates),
            "filtered_count": len(filtered_candidates),
            "search_completed": True,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        raise Exception(f"Pipeline execution failed: {str(e)}")
```

### 3.2 Backend API Integration
**Datei**: `backend/api.py`

```python
from mvp import run_search_pipeline_api

async def run_search_pipeline(search_data: dict) -> dict:
    """Run the search pipeline in executor to avoid blocking"""
    loop = asyncio.get_event_loop()

    # Pipeline Parameter vorbereiten
    pipeline_params = {
        'search_keywords': search_data['search_keywords'],
        'location': search_data.get('location', ''),
        'max_radius': search_data.get('max_radius', 25),
        'target_candidates': search_data.get('target_candidates', 100),
        'resume_last_updated_days': search_data.get('resume_last_updated_days', 30),
        'system_prompt': search_data.get('system_prompt', ''),
        'user_prompt': search_data.get('user_prompt', ''),
    }

    # Pipeline in Thread ausführen
    results = await loop.run_in_executor(None, run_search_pipeline_api, pipeline_params)
    return results
```

---

## Phase 4: Status Updates System
**Ziel**: Backend schreibt Status und Ergebnisse in Supabase zurück

### 4.1 Status Update Funktionen
**Datei**: `backend/supabase_client.py`

```python
def update_search_status(search_id: str, status: str, progress: str = None):
    """Update search status in Supabase"""
    update_data = {'status': status}
    if progress:
        update_data['progress'] = progress

    if status == 'completed':
        update_data['completed_at'] = datetime.now().isoformat()

    supabase.table('searches').update(update_data).eq('id', search_id).execute()

def update_search_results(search_id: str, results: dict):
    """Update search results in Supabase"""
    supabase.table('searches').update({
        'results': results,
        'status': 'completed',
        'completed_at': datetime.now().isoformat()
    }).eq('id', search_id).execute()
```

### 4.2 Pipeline mit Status Updates
**Datei**: `backend/api.py`

```python
async def process_search_from_supabase(job_id: str, search_id: str):
    """Process search job from Supabase with status updates"""
    try:
        # 1. Load search from Supabase
        response = supabase.table('searches').select('*').eq('id', search_id).execute()
        if not response.data:
            raise Exception(f"Search {search_id} not found")

        search_data = response.data[0]

        # 2. Update status to processing
        update_search_status(search_id, 'processing', 'Starting candidate search...')

        # 3. Run pipeline with progress updates
        update_search_status(search_id, 'processing', 'Searching Indeed for candidates...')
        results = await run_search_pipeline(search_data)

        # 4. Update with results
        update_search_results(search_id, results)

        # 5. Send email notification
        if search_data.get('recipient_email'):
            await send_completion_email(search_data, results)

        print(f"✅ Search {search_id} completed successfully")

    except Exception as e:
        print(f"❌ Search {search_id} failed: {e}")
        supabase.table('searches').update({
            'status': 'failed',
            'error': str(e)
        }).eq('id', search_id).execute()
```

---

## Phase 5: Email Integration
**Ziel**: Backend sendet Email nach Job-Completion

### 5.1 Email Template System
**Datei**: `backend/email_service.py` (NEU)

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

async def send_completion_email(search_data: dict, results: dict):
    """Send completion email with results"""
    try:
        # Email configuration
        EMAIL_USER = os.getenv("EMAIL_USER")
        EMAIL_PASS = os.getenv("EMAIL_PASS")
        SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

        recipient_email = search_data['recipient_email']

        # Create email
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = recipient_email
        msg['Subject'] = f"🎯 MatchTrex Suche abgeschlossen: {search_data['name']}"

        # Email body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
                <h2 style="color: #2563eb;">🎉 Ihre MatchTrex Suche ist abgeschlossen!</h2>

                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">📊 Suchergebnisse:</h3>
                    <ul>
                        <li><strong>Suchname:</strong> {search_data['name']}</li>
                        <li><strong>Suchbegriffe:</strong> {search_data['search_keywords']}</li>
                        <li><strong>Standort:</strong> {search_data.get('location', 'N/A')}</li>
                        <li><strong>Gefundene Kandidaten:</strong> {results.get('total_found', 0)}</li>
                        <li><strong>Nach AI-Filter:</strong> {results.get('filtered_count', 0)}</li>
                    </ul>
                </div>

                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <h4 style="margin-top: 0;">🔗 Nächste Schritte:</h4>
                    <p>Loggen Sie sich in MatchTrex ein, um die detaillierten Ergebnisse einzusehen und die Kandidatenprofile zu überprüfen.</p>
                    <p><a href="https://app.72.60.131.65.sslip.io" style="color: #2563eb;">→ Zu MatchTrex App</a></p>
                </div>

                <div style="background-color: #f0f9ff; padding: 15px; border-radius: 6px;">
                    <h4 style="margin-top: 0; color: #1976d2;">📋 Kandidatenübersicht:</h4>
        """

        # Add candidate summary
        candidates = results.get('candidates', [])
        if candidates:
            html_body += "<ul>"
            for i, candidate in enumerate(candidates[:5]):  # Max 5 in email
                html_body += f"<li><strong>{candidate.get('name', 'N/A')}</strong> - {candidate.get('email', 'N/A')}</li>"
            html_body += "</ul>"
            if len(candidates) > 5:
                html_body += f"<p><em>... und {len(candidates) - 5} weitere Kandidaten</em></p>"
        else:
            html_body += "<p>Keine passenden Kandidaten gefunden.</p>"

        html_body += f"""
                </div>

                <p style="color: #666; font-size: 14px; border-top: 1px solid #e0e0e0; padding-top: 15px; margin-top: 30px;">
                    Diese E-Mail wurde automatisch von MatchTrex generiert am {datetime.now().strftime("%d.%m.%Y um %H:%M")} Uhr.
                </p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, recipient_email, text)
        server.quit()

        print(f"📧 Email sent to {recipient_email}")

    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        # Don't fail the whole job if email fails
```

### 5.2 Email Integration in API
**Datei**: `backend/api.py`

```python
from email_service import send_completion_email

# In process_search_from_supabase():
# 5. Send email notification
if search_data.get('recipient_email'):
    await send_completion_email(search_data, results)
    print(f"📧 Email sent to {search_data['recipient_email']}")
```

---

## Phase 6: Real-time Updates (Optional)
**Ziel**: Frontend zeigt Live-Status ohne Refresh

### 6.1 Supabase Realtime
**Datei**: `frontend/src/components/SearchList.tsx`

```typescript
useEffect(() => {
  // Subscribe to search updates
  const subscription = supabase
    .channel('searches')
    .on('postgres_changes',
      { event: 'UPDATE', schema: 'public', table: 'searches' },
      (payload) => {
        console.log('Search updated:', payload);
        fetchSearches(); // Refresh list
      }
    )
    .subscribe();

  return () => {
    supabase.removeChannel(subscription);
  };
}, []);
```

---

## Deployment Überlegungen

### Environment Variables für Production
**Coolify Backend Env Vars**:
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
MISTRAL_API_KEY=83pVv0mVbOBUwSRmoPBaWg6UUkNZunTP
TWOCAPTCHA_KEY=22e969001c9ae2824614794f69230e68
EMAIL_USER=aauxilliary4@gmail.com
EMAIL_PASS=kxoc ajnf pked zhwp
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### Database Schema Anpassungen
**Supabase searches Tabelle**:
```sql
ALTER TABLE searches ADD COLUMN IF NOT EXISTS progress TEXT;
ALTER TABLE searches ADD COLUMN IF NOT EXISTS error TEXT;
```

---

## Implementierungsreihenfolge

1. **Phase 1** → Frontend-Backend Connection
2. **Phase 2** → Backend Supabase Integration
3. **Phase 3** → Pipeline Integration
4. **Phase 4** → Status Updates System
5. **Phase 5** → Email Integration
6. **Testing** → End-to-End Tests
7. **Deployment** → Production Rollout

Jede Phase wird einzeln implementiert, getestet und committed, bevor wir zur nächsten übergehen.