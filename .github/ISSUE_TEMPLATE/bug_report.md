name: "🐞 Bug Report (with Screenshots)"
description: "Report a reproducible bug with logs and screenshots for fast triage."
title: "[BUG] "
labels: ["bug", "needs-triage"]
body:
  - type: markdown
    attributes:
      value: |
        ## 🐞 Bug Report / Hata Bildirimi
        **EN:** Please fill this form carefully. Screenshots and console logs greatly speed up fixes.  
        **TR:** Lütfen formu dikkatlice doldur. Ekran görüntüsü ve konsol kayıtları çözümü hızlandırır.

  - type: input
    id: summary
    attributes:
      label: "1) Bug Summary / Hata Özeti"
      description: "EN: One sentence describing the bug. | TR: Hatanın tek cümlelik özeti."
      placeholder: "Timer freezes after long break / Uzun moladan sonra sayaç donuyor"
    validations:
      required: true

  - type: textarea
    id: impact
    attributes:
      label: "2) Impact / Etki"
      description: "EN: How does this affect the user? | TR: Kullanıcıyı nasıl etkiliyor?"
      placeholder: |
        EN: The app becomes unusable and requires refresh.
        TR: Uygulama kullanılamaz oluyor ve sayfayı yenilemek gerekiyor.
    validations:
      required: true

  - type: dropdown
    id: severity
    attributes:
      label: "3) Severity / Şiddet"
      description: "EN/TR: Select the severity level."
      options:
        - "Critical — App unusable / Uygulama kullanılamıyor"
        - "High — Major feature broken / Ana özellik bozuk"
        - "Medium — Workaround exists / Çözüm yolu var"
        - "Low — Minor issue / Küçük sorun"
    validations:
      required: true

  - type: dropdown
    id: frequency
    attributes:
      label: "4) Frequency / Sıklık"
      description: "EN/TR: How often does it happen?"
      options:
        - "Always / Her zaman"
        - "Often / Sık"
        - "Sometimes / Bazen"
        - "Rare / Nadir"
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: "5) Steps to Reproduce / Tekrarlama Adımları"
      description: "EN/TR: Clear, numbered steps to reproduce."
      placeholder: |
        1. Start a Pomodoro session (25:00)
        2. Complete 4 cycles
        3. Enter long break
        4. Click Pause then Start
        5. Observe freeze
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: "6) Expected Behavior / Beklenen Davranış"
      description: "EN/TR: What should happen?"
      placeholder: "Timer should keep counting down smoothly / Sayaç akıcı şekilde devam etmeli"
    validations:
      required: true

  - type: textarea
    id: actual
    attributes:
      label: "7) Actual Behavior / Gerçekleşen Davranış"
      description: "EN/TR: What actually happens?"
      placeholder: "Timer stops at 14:59 and UI becomes unresponsive / 14:59'da duruyor ve arayüz donuyor"
    validations:
      required: true

  - type: textarea
    id: screenshots
    attributes:
      label: "8) Screenshots / Ekran Görüntüleri (Required)"
      description: |
        EN: Attach screenshots by dragging & dropping here, or paste image links.
        TR: Buraya sürükleyip bırakıp ekran görüntüsü ekle veya görsel linki yapıştır.
        Tip: Prefer 2 screenshots: (1) UI state, (2) Console error.
      placeholder: |
        - Screenshot #1 (UI):
          [drag & drop image here]
        - Screenshot #2 (Console/Errors):
          [drag & drop image here]
    validations:
      required: true

  - type: textarea
    id: console_logs
    attributes:
      label: "9) Console Logs / Konsol Kayıtları"
      description: |
        EN: Open DevTools → Console → copy errors here.
        TR: Geliştirici araçları → Console → hataları buraya kopyala.
      render: shell
      placeholder: |
        Example:
        TypeError: ...
        at PomodoroState (...)
    validations:
      required: false

  - type: input
    id: environment
    attributes:
      label: "10) Environment / Ortam"
      description: "EN/TR: OS, Browser, Device."
      placeholder: "Windows 11 / Chrome 120 / Desktop (i5, 8GB RAM)"
    validations:
      required: true

  - type: input
    id: app_version
    attributes:
      label: "11) App Version / Uygulama Sürümü"
      description: "EN: Commit hash or release tag if known. | TR: Biliniyorsa commit veya sürüm etiketi."
      placeholder: "v1.0.0 or commit: abc1234"
    validations:
      required: false

  - type: textarea
    id: regression
    attributes:
      label: "12) Regression Check / Önce Çalışıyor muydu?"
      description: "EN/TR: Did it work before? When did it start?"
      placeholder: |
        EN: It worked yesterday. Started after adding config.json fetch.
        TR: Dün çalışıyordu. config.json fetch ekledikten sonra başladı.
    validations:
      required: false

  - type: textarea
    id: extra
    attributes:
      label: "13) Additional Context / Ek Bilgi"
      description: "EN/TR: Any extra info, links, related issues."
      placeholder: "- Related issue: #12\n- Possible cause: ..."
    validations:
      required: false

  - type: checkboxes
    id: checklist
    attributes:
      label: "14) Confirmation / Onay"
      description: "EN/TR: Please confirm the following."
      options:
        - label: "I searched existing issues and did not find a duplicate / Mevcut sorunlarda aynısını aradım, bulamadım"
          required: true
        - label: "I attached screenshots (UI + Console if possible) / Ekran görüntüsü ekledim (UI + mümkünse Console)"
          required: true
        - label: "I provided clear steps to reproduce / Tekrarlama adımlarını net verdim"
          required: true

