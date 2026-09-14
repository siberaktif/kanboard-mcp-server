# Değişim Günlüğü (Changelog)

## [1.1.0] - 2026-09-14

### Eklenenler (Added)
- **Yeni MCP Araçları (`kanboard_mcp_server.py`):**
  - `create_external_task_link`: Görevlere harici web bağlantıları (Forgejo / GitHub commit linkleri) ekleme desteği.
  - `create_task_link`: Görevler arasında yönlü ilişkiler ve blokaj (`blocks` / link_id: 2) zinciri kurma desteği.
  - `close_task`: Görevleri geçmiş zamanlı veya tamamlandı statüsünde arşivleme (`is_active = 0`) desteği.
- **Kalıcı SDLC Senkronizasyon Betiği (`scripts/setup_project_tasks.py`):**
  - **Upsert Mimarisi:** Görev silme (`remove_task`) kaldırıldı. `reference` (örn. `commit:<hash>`) üzerinden çalışan, varsa güncelleyen (`update_task`), yoksa oluşturan güvenli veri yapısı.
  - **Git Epoch Desteği:** Sentetik gün artırımı yerine Git logundan doğrudan Unix epoch zaman damgaları (`%at`) ile saniyesi saniyesine tarih senkronizasyonu.
  - **Phase 0 Bellek Entegrasyonu:** Kodlama öncesi mimari ve fizibilite kararlarını (`docs/ai_chats/`) Kanboard ek dosyası olarak ilişkilendirme parametresi.
