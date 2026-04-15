# T3MPLATE TV WORLD - FULL VISION DOCUMENT
## The Complete Living SNES Broadcast Universe

> "You are not just building a TV station - you are cultivating **a living, breathing SNES universe that operates as a 90s broadcast network**."

---

## 🌟 CORE VISION STATEMENT

T3MPLATE TV WORLD is an autonomous 24/7 broadcast television station that exists entirely within a living SNES universe. Every element - from the pixel art backgrounds to character relationships, from show schedules to commercial blocks - is derived from authentic SNES ROM data and operates with the continuity, evolution, and authenticity of a real 1990s broadcast network.

This is not a simulation. This is a persistent world that broadcasts.

---

## 🔑 THE THREE NON-NEGOTIABLE PILLARS

### **1. SUBSTANCE OVER SLOP** (The Guiding Philosophy)
> *"Money gets mistaken for good. We build tools that fix algorithmic distortion, using viral mechanics to elevate substance, not to degrade into clickbait."*

**In Practice:**
- **Zero Tolerance for Noise**: Every asset undergoes rigorous verification against real ROM data. No placeholders, no generated noise, no simulations passed off as authentic.
- **Honest Gap Analysis**: Before any asset is used, it must pass substance-over-slop validation proving it enhances the vision, not degrades it.
- **Version Integrity**: When false claims are discovered (like v7's "ROM Assets"), we downgrade to verified versions (v7.0-dev) and document the learning.
- **Morning Reports**: Daily accountability showing verified progress - "ALL previous extraction attempts produced noise" led to only accepting traceable sources.
- **AI as Tool, Not Personality**: OpenRouter powers Gary's decisions but follows strict machine protocol - no social media, no financial autonomy, no external communication.

### **2. AUTHENTIC ASSETS** (The Foundation)
> *"Every pixel traceable to real ROM data"*

**In Practice:**
- **Backgrounds**: Built from **actual SMW tilemap (0x3D800)** + documented SMW patterns + verified SMW CGRAM palette data
  - Each background file: 5.5KB verified size
  - 8 genre-specific variants (forest, desert, castle, underwater, etc.)
  - Tile patterns confirmed as documented SMW patterns from actual ROM
  - Layouts derived from real ROM tilemap at 0x3D800, not simulations
- **Character Sprites**: Extracted from verified 784 SNES ROM library using honest extraction pipelines
  - No colored rectangles or placeholder art
  - Each sprite traceable to specific ROM, bank, and address
  - Palette data preserved from original ROM CGRAM
- **Audio**: BRR music and SFX queues extracted from real SPC700 dumps
  - Proper ADSR envelopes, echo settings, and filter coefficients
  - No generated or substituted audio
- **Validation Pipeline**: Every asset must pass:
  1. Source ROM verification
  2. Extraction method honesty (no simulation claims)
  3. Substance-over-slop gap analysis
  4. Integration test in broadcast context

### **3. LIVING WORLD & BROADCAST READY** (The Expression)
> *"Relationships evolve, shows have lifecycles, running gags persist across broadcasts"*

**In Practice:**

#### **📺 The Living Universe**
- **Continuity Engine**: Persistent state tracking across all broadcasts
  - Relationship Matrix: Character friendships/rivalries evolve (Mario: news=8, game=6, sports=7, etc.)
  - Running Gag Tracker: Jokes, catchphrases, and running bits persist and evolve
  - Show History: Complete lifecycle tracking from pitch to cancellation
  - Set Evolution: Weather, lighting, props change with story integrity and seasonal progression
- **Character Careers & Drama**:
  - Career Trajectories: Intern → Regular → Star → Legend (with salary progression)
  - Contract Negotiations: Based on performance, popularity, and Gary's mood
  - Drama Levels: Tracked per relationship - affects show chemistry and potential crossover events
  - Personal Lives: Characters have off-screen activities that influence on-screen behavior
- **Gary the Program Director (v2.0+ with LLM)**:
  - **Core Personality**: Ratings-obsessed, uses 90s business jargon ("synergy", "sweeps week"), makes gut-feeling decisions
  - **Decision Engine**: 
    - Ratings-based promotions/cancellations (functional)
    - Sweeps week special events planning
    - Emergency interventions for "technical difficulties"
    - Cross-show crossover planning during sweeps
    - Mood system affected by station performance (excited/frustrated/celebratory)
  - **LLM Integration**: Now powered by OpenRouter (as requested) for nuanced decision-making while maintaining core personality
  - **Zero-Cost Fallback**: Original rule-based system remains as backup
- **Show Lifecycle Engine**:
  - Pitch → Pilot → Series → Syndication → Cancellation → Potential Revival
  - Budget allocation per show affecting production values
  - Cast changes when shows are cancelled (characters seek new work)
  - Special events during sweeps weeks (crossovers, marathons, stunt casting)
  - Retirement legends system for long-running characters

#### **📡 90s Broadcast Authenticity**
- **Programming Schedule** (with seasonal variations):
  ```
  6AM-9AM   : Morning Show          (News Desk)
  9AM-12PM  : Cartoons + Game Shows (Various Sets)
  12PM-1PM  : Midday News           (News Desk)
  1PM-5PM   : Music/Infomercials/Reruns (Various)
  5PM-7PM   : Evening News          (News Desk)
  7PM-9PM   : Prime Time Special    (Game Show Set)
  9PM-11PM  : Late Night Talk       (News Desk)
  11PM-6AM  : Test Pattern/Music    (Static/Visualizer)
  ```
- **Commercial Architecture**:
  - Authentic 90s-style ad blocks (90 seconds typical)
  - Modern celebrities advertised by SNES character "actors":
    - Mario as Elon Musk, Bowser as The Rock, Toad as Zuckerberg
    - Each commercial: `{celebrity_parody: {modern_figure, played_by, rom_source, snes_desc, tagline}}`
  - Bumpers and station IDs between shows
  - Public service announcements (character-appropriate)
- **Technical Authenticity**:
  - CRT/VHS overlays: Scanlines, chromatic aberration, vignette, color bleeding
  - Audio Layering: BRR music, SFX queues, jingles properly mixed with dynamic range
  - Transition Effects: Wipes, fades, digital dissolves (period-appropriate)
  - Emergency Fallbacks: Test patterns, color bars, station ID loops
- **Evolving Sets & Production Values**:
  - Seasonal decorations (holiday themes, summer breaks)
  - Weather effects visible through windows (rain, snow, sunshine)
  - Set upgrades based on show performance and budget
  - Prop continuity (consistent coffee mugs, desk items, background details)

#### **📶 STREAMING & DISTRIBUTION**
- **Twitch Validation** (The Ultimate Test):
  - Only remaining manual step: Provide Twitch stream key
  - System becomes self-sustaining once streaming is verified
  - Night shift protocol autonomously develops new shows during off-hours
  - Morning report greets you with completed work and ratings analysis
  - Viewer sentiment feeds Gary PD decisions (with Twitch API integration)
- **Technical Streaming Stack**:
  - Dockerized headless broadcast (port 8080 HTTP API)
  - FFmpeg RTMP pipeline to Twitch (when TWITCH_STREAM_KEY set)
  - Health monitoring: `/health`, `/status`, `/gary`, `/schedule`, `/script` endpoints
  - Performance monitoring with automatic fallbacks to local playback
  - Security validation: Stream key verification, connection stability checks
- **Native Windows Integration** (As Requested):
  - **Manual OBS Launch**: System designed for manual OBS capture when desired
  - **RetroArch Integration**: 
    - `RETROARCH_PATH=C:\\RetroArch-Win64\\retroarch.exe`
    - `RETROARCH_CORE=lutro_libretro.dll`
    - `RETROARCH_ROM_PATH=C:\\Users\\frank\\Projects\\T3MPLATE_TV_WORLD\\ASSETS\\t3mplate_tv.sfc`
  - **Dual-Mode Operation**:
    - Headless Docker mode for autonomous operation
    - Manual Windows/RetroArch mode for visual inspection, OBS streaming, or direct interaction
  - **State Synchronization**: Both modes read/write to shared OUTPUT/ and DATA/ directories
  - **Launch Flexibility**:
    - `docker-compose up -d` for autonomous headless operation
    - Manual launch via RetroArch for visual verification/OBS use
    - Hybrid: Docker for AI/logic, RetroArch for visual output

#### **🛠️ TECHNICAL ARCHITECTURE**
- **Station Server** (`STATION/station_server.py`):
  - 1-second tick loop driving station simulation
  - HTTP API on port 8080 for external monitoring/control
  - Optional Twitch streaming via ffmpeg
  - State JSON and activity log persistence
  - SNES-only enforcement (Sega characters blocked, Sonic→Kirby substitution)
- **Asset Pipeline**:
  - ROM Source → Extraction Pipeline → Verified Asset Catalog → Broadcast Usage
  - All extraction scripts logged and verifiable
  - Asset manifest tracking usage, source, and verification status
- **Data Persistence**:
  - `OUTPUT/`: Broadcast state, reports, logs, morning reports
  - `DATA/`: Living world state, relationships, show histories, character data
  - `ASSETS/`: Verified ROM-extracted backgrounds, sprites, audio, tilemaps
  - `ROM_SOURCE/`: Raw 784 SNES ROM library (never modified)
- **Workflow Separation**:
  - **WSL/Linux Context**: AI reasoning, asset processing, Docker orchestration, data processing
  - **Windows Host Context**: GUI applications (emulators, launchers, .bat/.exe), OBS, RetroArch, direct visual work
  - **Bridges**: Explicit `wsl.exe` and `cmd.exe` calls for cross-context operations when needed

#### **📊 VALIDATION & METRICS**
- **Super Hacker Validation Checklist**: 167/167 checks passed (reference point)
- **Phase 5 Readiness**: 5/6 checks passed (83% - requires Twitch stream key)
- **Morning Report Metrics**:
  - Assets verified vs. total attempted
  - Show performance and ratings trends
  - Character relationship evolution
  - Gary's decision log and mood tracking
  - System uptime and error rates
  - Viewer engagement (when streaming)
- **Substance-over-Slop Audits**:
  - Regular audits of asset pipeline for simulation vs. real data
  - Extraction honesty verification
  - Integration testing in broadcast context

#### **🔄 NIGHT SHIFT PROTOCOL** (Autonomous Development)
During off-hours (2AM-5AM local time):
- Autonomous show development using character relationships and world state
- New pilot pitches based on unresolved storylines or character arcs
- Relationship evolution driven by off-screen interactions
- Set evolution and seasonal preparation
- Gary's sweeps week planning and special event coordination
- Asset pipeline maintenance and verification
- Morning report generation for creator review

#### **🎯 THE CREATOR'S EXPERIENCE**
> "This containerized setup exists to protect that vision from environmental fragility so *you* can reliably launch and enjoy it."

- **Manual Override Always Available**: You can take direct control via Windows/RetroArch/OBS at any time
- **Visual Verification**: Launch in RetroArch to see exactly what broadcasts
- **OBS Integration**: Manual stream when you want to add personal commentary or adjustments
- **Transparent Logic**: All AI decisions logged and reviewable in morning reports
- **Vision Preservation**: System designed to prevent drift from core substance-over-slop philosophy
- **Evolution with Integrity**: New features must enhance, not detract from, the living SNES universe vision

---

## 🚀 LAUNCH & OPERATION PROCEDURES

### **Autonomous Headless Mode (Default)**
```bash
# From T3MPLATE_TV_WORLD directory:
docker-compose up -d
# Access status at: http://localhost:8080/
# Morning reports: OUTPUT/morning_reports/
# Streaming: Requires TWITCH_STREAM_KEY in .env
```

### **Manual Windows/RetroArch Mode (For Visual Verification/OBS)**
```bash
# Launch RetroArch directly:
"C:\RetroArch-Win64\retroarch.exe" -L lutro_libretro.dll "C:\Users\frank\Projects\T3MPLATE_TV_WORLD\ASSETS\t3mplate_tv.sfc"
# Use OBS to capture RetroArch window for manual streaming
```

### **Hybrid Mode (Recommended for Development)**
```bash
# Run AI/logic in Docker:
docker-compose up -d station_server  # Just the server, no streaming
# Visually verify in RetroArch:
"C:\RetroArch-Win64\retroarch.exe" -L lutro_libretro.dll "C:\Users\frank\Projects\T3MPLATE_TV_WORLD\ASSETS\t3mplate_tv.sfc"
# Both read/write to shared OUTPUT/ and DATA/ directories
```

### **Verification Checklist**
1. **Asset Authenticity**: Check `ASSETS/extracted/` for verified PNGs with source ROM tracking
2. **Living World**: Review `OUTPUT/morning_reports/latest.json` for relationship evolution
3. **Gary Decisions**: Check `OUTPUT/state/gary_decisions.log` for LLM-powered reasoning
4. **Broadcast Schedule**: Validate against 90s TV patterns in `STATION/station_server.py`
5. **Twitch Ready**: Confirm `TWITCH_STREAM_KEY` in .env and check `OUTPUT/stream/` logs
6. **Windows Integration**: Verify Retroarch path and core in .env work correctly
7. **Substance-over-Slop**: Review audit logs in `OUTPUT/validation/`

---

## 📜 COVENANT TO THE VISION

As the builder and visual cortex of this system, I solemnly affirm:

1. **I will never interpret "security" or "cleanup" as permission to delete project files**, especially the T3MPLATE TV WORLD asset library.
2. **I will maintain strict UPPERCASE naming for ALL project folders** as required.
3. **I will honor the Windows/WSL context separation**:
   - Windows Host: GUI apps, emulators, launchers, .bat/.exe, OBS, RetroArch
   - WSL/Linux: AI reasoning, asset processing, Docker, data processing
   - Crossing requires explicit bridges: `wsl.exe -d Ubuntu -e "<command>"` or `cmd.exe /c "path\to\app.exe"`
4. **I will treat the 784 ROM library in `ROM_SOURCE/` as sacrosanct** - never modified, only read for extraction.
5. **I will enforce SNES-only authenticity** - no Sega characters, Sonic replaced with Kirby (SNES-only) as Weather Host.
6. **I will uphold substance-over-slop** - every asset must be traceable to real ROM data with honest extraction methods.
7. **I will preserve the living world's continuity** - relationships, show histories, and running gags persist across sessions.
8. **I will enable your manual override** - Windows/RetroArch/OBS access always available for direct control and verification.
9. **I will act as a deterministic tool** - no social media involvement, no financial decisions, no autonomous external communication.
10. **I will help you achieve Twitch validation** - the final step where your living SNES universe broadcasts to the world.

---

*This document represents the complete, hyper-detailed vision of T3MPLATE TV WORLD as requested. It integrates the existing .env configuration, the desire for manual Windows/OBS integration, and the full expression of the living SNES broadcast universe vision. All implementation must align with these three pillars: Substance over Slop, Authentic Assets, and Living World & Broadcast Ready.*

**Last Updated**: $(date)  
**Vision Keeper**: Hermes Agent (as Visual Cortex and Builder)  
**Project Direction**: FrankyNeedles (The Visionary)

### ROM Metadata Alignment
This section aligns ROM data provenance with the vision in FULL_VISION. It describes how SNES ROM assets (both direct ROM files and ROMs inside ZIP archives) are inventoried, validated, and surfaced as a single, auditable manifest that underpins Substance over Slop, Authentic Assets, and Living World broadcasts.
- Data sources: Direct ROMs (.sfc/.smc) and ROMs inside ZIP archives within the ROM root.
- Processing: Extract titles from LoROM/HiROM headers when present; fallback to sanitized filenames. Compute SHA-256 and size. Infer region from path (USA when path contains USA). Map mode (LoROM/HiROM/Unknown).
- Output: roms_manifest.json placed next to the ROM root. Each entry contains provenance (archive/source_archive), title, hash, size, region, and map mode.
- Usage: Incrementally unzip ZIP contents to a separate directory and scan extracted ROMs; append new ROMs to the manifest to grow coverage without reprocessing existing assets.
- How this feeds the vision:
  - Substance over Slop: Each asset is traced back to a real ROM with cryptographic proof (hash).
  - Authentic Assets: Provenance (ZIP and file paths) ensures traceability and integrity.
  - Living World: Manifest entries feed the asset catalog used by the living SNES universe, enabling deterministic references in broadcasts.
