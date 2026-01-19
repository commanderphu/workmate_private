# Ordnerstruktur erstellen
mkdir -p docs/{concept,architecture,features/integrations,development,planning}

# Concept Docs
touch docs/concept/vision.md
touch docs/concept/why-neurodivergent.md
touch docs/concept/use-cases.md

# Architecture Docs
touch docs/architecture/system-overview.md
touch docs/architecture/components.md
touch docs/architecture/data-model.md
touch docs/architecture/tech-stack.md

# Features Docs
touch docs/features/core-features.md
touch docs/features/document-scanner.md
touch docs/features/ai-processor.md
touch docs/features/reminder-engine.md
touch docs/features/integrations/calendar.md
touch docs/features/integrations/smart-home.md
touch docs/features/integrations/paperless-ngx.md

# Development Docs
touch docs/development/setup.md
touch docs/development/api-reference.md
touch docs/development/deployment.md
touch docs/development/contributing.md

# Planning Docs
touch docs/planning/roadmap.md
touch docs/planning/milestones.md
touch docs/planning/decisions.md

# CONTRIBUTING.md im Root
touch CONTRIBUTING.md

# Git add und commit
git add .
git commit -m "docs: initialize project documentation structure"

echo "✅ Dokumentationsstruktur erstellt!"
