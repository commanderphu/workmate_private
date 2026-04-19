# Roadmap

## Vision

Workmate Private soll bis Ende 2026 ein ausgereiftes, stabiles Tool für ADHD-Betroffene sein, das sowohl als Self-Hosted Lösung als auch als optionaler Cloud-Service verfügbar ist.

---

## Phasen

### Phase 0: Foundation (Q1 2026) - **ABGESCHLOSSEN** ✅

**Ziel:** Grundlegende Architektur & MVP

**Tasks:**
- [x] Projekt-Setup & Dokumentation
- [x] Architektur-Design
- [x] Tech-Stack Entscheidungen
- [ ] Repository Setup (GitHub) ← noch ausstehend
- [ ] CI/CD Pipeline ← noch ausstehend
- [x] Basic Backend (FastAPI)
- [x] Basic Frontend (Flutter Web)
- [x] Datenbank-Setup (SQLite/PostgreSQL)

**Deliverables:**
- [x] Vollständige Dokumentation
- [x] Lauffähiger Prototyp (lokal)
- [ ] GitHub Repository public ← noch ausstehend

**Timeline:** Januar - März 2026 ✅

---

### Phase 1: MVP (Q2 2026) - **FERTIG** ✅

**Ziel:** Funktionierende Basis-Features für Beta-Tester

**Features:**
- ✅ Document Upload & Processing
  - [x] Camera/Scanner Input (File Upload Web + Mobile)
  - [x] OCR (Tesseract)
  - [x] KI-Analyse (Claude API)
- ✅ Task Management
  - [x] CRUD Operations
  - [x] Due Dates & Priorities
  - [x] Basic Status Tracking
- ✅ Reminder Engine
  - [x] Multi-Stage Reminders (info, warning, urgent) – implementiert
  - [x] Push Notifications – Firebase FCM
  - [ ] Email Notifications – **noch ausstehend**
- ✅ User Management
  - [x] Registration & Login
  - [x] JWT Authentication (Argon2)

**Tech:**
- [x] Backend: Python 3.13 + FastAPI
- [x] Frontend: Flutter (Web + Android)
- [x] Database: SQLite (dev), PostgreSQL (prod)
- [x] AI: Claude API
- [x] Deployment: Docker Compose

**Milestone:** Beta Release mit 5-10 Beta-Testern

**Timeline:** April 2026 ✅ – **Beta live, Push Notifications implementiert**

---

### Phase 2: Enhancement (Q3 2026) - **TEILWEISE VORGEZOGEN** 🔵

**Ziel:** Erweiterte Features & Integrationen

**Features:**
- 🟡 Advanced Task Management
  - [ ] Dependencies
  - [ ] Sub-Tasks
  - [ ] Recurring Tasks
- ✅ Calendar Integration ← **bereits in Phase 1 implementiert!**
  - [x] CalDAV Support (Nextcloud, Apple, Radicale, etc.)
  - [x] Google Calendar OAuth2 + API
  - [x] Two-Way Sync (bidirektionaler Sync-Service)
  - [x] Task → CalendarEvent Mapping
  - [ ] Microsoft Outlook (geplant)
- 🟡 Enhanced Reminders
  - [ ] SMS Integration
  - [ ] Telegram/WhatsApp
  - [ ] Dynamic Escalation
- [ ] Search & Filter
- [ ] Basic Analytics

**Integrations:**
- [ ] Paperless-ngx (optional)
- [ ] Home Assistant (optional)
- [ ] MQTT (optional)

**Milestone:** Public Beta (50+ Users)

**Timeline:** Juli - September 2026

---

### Phase 3: Smart Features (Q4 2026)

**Ziel:** KI-gestützte Intelligenz & Automation

**Features:**
- 🔮 Smart Home Integration
  - Home Assistant Full Support
  - MQTT Devices
  - Presence Detection
  - Room-Based Reminders
- 🔮 AI Enhancements
  - Learning from Corrections
  - Smart Suggestions
  - Pattern Recognition
  - Personalized Reminders
- 🔮 Advanced Analytics
  - Insights & Trends
  - Gamification
  - Achievement System
- 🔮 Multi-Language Support
  - English
  - French (optional)
- 🔮 iOS App
  - Native iOS Build
  - Apple Ecosystem Integration

**Milestone:** v1.0 Release

**Timeline:** Oktober - Dezember 2026

---

## Future (2027+)

### Potential Features

**Collaboration:**
- Shared Tasks (Households, Couples)
- Task Delegation
- Family Accounts

**Advanced Integrations:**
- Banking APIs (FinAPI)
  - Automatic Payment Matching
  - Balance Checking
- Voice Assistants
  - Alexa Skill
  - Google Assistant
- Tracking APIs
  - Automatic Shipment Tracking
  - Delivery Notifications

**AI/ML:**
- Predictive Task Scheduling
- Habit Pattern Recognition
- Personalized Optimization
- Natural Language Task Creation

**Community Features:**
- Public Task Templates
- Community Plugins
- Skill Marketplace (User-created integrations)

**Mobile Enhancements:**
- Offline Mode
- Widget Support
- Wear OS / Apple Watch

---

## Decision Points

### November 2026: Full-Time Decision

**Joshua's Entscheidungspunkt:** K.I.T. Solutions Full-Time?

**Metrics to evaluate:**
- Active Users: 200+ goal
- User Satisfaction: >80% positive feedback
- Revenue (if monetization started): €2000+/month
- Personal Wellbeing: Sustainable workload?

**Outcomes:**
- ✅ **Go Full-Time:** Focus 100% on Workmate & K.I.T.
- ❌ **Stay Part-Time:** Continue side-project, slower development

---

## Monetization Strategy (Optional)

**Open Source First:**
- Core = Free & Open Source (MIT License)
- Self-Hosting = Always Free

**Optional Paid Services:**

### Hosted Cloud Service
- **Free Tier:** 50 documents/month, 100 tasks
- **Pro Tier:** €5/month - Unlimited, priority support
- **Family Tier:** €10/month - 5 accounts

### Premium Features (Optional)
- Advanced AI (GPT-4 Turbo access)
- Extended Integrations
- Priority Email Support
- Custom Branding

### Support & Setup
- Setup Service: €50-100 one-time
- Managed Hosting: €10-20/month
- Consulting: €50/hour

**Philosophy:** Never paywall core ADHD features. Monetization only for convenience/scale.

---

## Success Metrics

### Phase 1 (MVP)
- [ ] 10 active beta users
- [ ] <5s document processing time
- [ ] >90% AI classification accuracy
- [ ] 0 critical bugs

### Phase 2 (Enhancement)
- [ ] 50 active users
- [ ] 500+ documents processed
- [ ] 1000+ tasks created
- [ ] >85% user satisfaction

### Phase 3 (Smart Features)
- [ ] 200 active users
- [ ] 10+ integrations enabled by users
- [ ] GitHub: 100+ stars
- [ ] Active community (Discord/Discussions)

### 2027+ (Growth)
- [ ] 1000+ active users
- [ ] Sustainable revenue (if monetized)
- [ ] Active contributor community
- [ ] Multi-language support

---

## Risks & Mitigation

### Technical Risks

**Risk:** Claude API Costs too high  
**Mitigation:** Ollama fallback, cost monitoring, caching

**Risk:** Flutter performance issues  
**Mitigation:** Native app option, performance testing early

**Risk:** Database scaling  
**Mitigation:** PostgreSQL from start, proper indexing

### Business Risks

**Risk:** Low user adoption  
**Mitigation:** Beta-testing, community feedback, iterate fast

**Risk:** Competition  
**Mitigation:** ADHD-specific focus, open source advantage

**Risk:** Burnout (Joshua)  
**Mitigation:** Realistic timelines, beta-testers help, no pressure

### Community Risks

**Risk:** Negative feedback  
**Mitigation:** Thick skin, focus on constructive criticism, iterate

**Risk:** Feature creep  
**Mitigation:** Strict roadmap, MVP first, say "no" to non-core features

---

## Contributing to Roadmap

**Community Input Welcome!**

If you have ideas for features or want to influence the roadmap:
- Open GitHub Discussion
- Vote on existing feature requests
- Submit detailed use cases
- Join beta testing

**Remember:** ADHD-specific features get priority. General productivity features are secondary.

---

## Updates

This roadmap is reviewed and updated:
- Monthly during active development
- Quarterly after v1.0 release

**Last Updated:** April 18, 2026  
**Next Review:** Mai 2026