(function () {
  window.App = window.App || {};
  App.Pages = App.Pages || {};

  function recommendationBanner(recommendation) {
    return "";
    return [
      '<section class="rounded-[32px] border ' + (recommendation.tone === "success" ? "border-success/20 bg-emerald-50" : "border-warning/20 bg-amber-50") + ' p-6 shadow-soft">',
      '  <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">',
      "    <div>",
      '      <div class="flex flex-wrap items-center gap-3">' + App.UI.badge(recommendation.tone, "המלצת מערכת") + '<span class="text-xs font-bold uppercase tracking-[0.22em] text-slateText">decision signal</span></div>',
      '      <h2 class="mt-4 text-3xl font-extrabold text-ink">' + recommendation.headline + "</h2>",
      '      <p class="mt-3 max-w-3xl text-sm leading-7 text-slateText">' + recommendation.reason + "</p>",
      "    </div>",
      '    <div class="rounded-[24px] border border-white/50 bg-white/80 px-5 py-4 text-sm text-slateText">המערכת היא כלי המלצה בלבד. יש לאמת נתונים ועלויות מול הבנק והגורמים המקצועיים.</div>',
      "  </div>",
      "</section>"
    ].join("");
  }

  function trackCard(track) {
    return [
      '<article class="rounded-[28px] border border-line bg-white p-6 shadow-soft">',
      '  <div class="flex items-start justify-between gap-4">',
      '    <div><p class="text-sm font-bold text-slateText">' + App.Helpers.escapeHtml(track.label) + '</p><h3 class="mt-1 text-2xl font-bold text-ink">' + App.Format.currency(track.outstandingBalance) + "</h3></div>",
      '    <button type="button" class="rounded-full border border-line px-4 py-2 text-xs font-semibold text-ink hover:border-brand-600 hover:text-brand-600" data-track-detail="' + track.id + '">פירוט מלא</button>',
      "  </div>",
      '  <div class="mt-5 grid gap-4 sm:grid-cols-2">',
      '    <div class="rounded-2xl bg-surface px-4 py-3 text-sm text-slateText"><span class="block font-semibold text-ink">סוג</span>' + App.Helpers.escapeHtml(track.label) + "</div>",
      '    <div class="rounded-2xl bg-surface px-4 py-3 text-sm text-slateText"><span class="block font-semibold text-ink">ריבית נוכחית</span>' + App.Format.percent(track.currentRate) + "</div>",
      '    <div class="rounded-2xl bg-surface px-4 py-3 text-sm text-slateText"><span class="block font-semibold text-ink">יתרת חודשים</span>' + App.Format.number(track.remainingTermMonths) + "</div>",
      '    <div class="rounded-2xl bg-surface px-4 py-3 text-sm text-slateText"><span class="block font-semibold text-ink">סיכון</span>' + App.Helpers.escapeHtml(track.riskTag || track.prepaymentPenaltyRule) + "</div>",
      "  </div>",
      "</article>"
    ].join("");
  }

  function workspaceIcon(name) {
    var icons = {
      reset: '<svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 4v6h6" stroke-linecap="round" stroke-linejoin="round"/><path d="M20 20v-6h-6" stroke-linecap="round" stroke-linejoin="round"/><path d="M20 9a7 7 0 0 0-12-3L4 10M4 15a7 7 0 0 0 12 3l4-4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
      risk: '<svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3l9 16H3L12 3z" stroke-linejoin="round"/><path d="M12 9v4" stroke-linecap="round"/><circle cx="12" cy="16.5" r="0.8" fill="currentColor" stroke="none"/></svg>',
      shield: '<svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3l7 3v5c0 4.7-2.8 7.8-7 10-4.2-2.2-7-5.3-7-10V6l7-3z" stroke-linejoin="round"/><path d="M9.5 12.2l1.7 1.8 3.3-3.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    };

    return icons[name] || icons.shield;
  }

  function workspaceSignal(title, body, tone, iconName) {
    var toneClasses = tone === "warning"
      ? "border-warning/20 bg-amber-50 text-warning"
      : tone === "success"
        ? "border-success/20 bg-emerald-50 text-success"
        : "border-accent/20 bg-sky-50 text-accent";

    return [
      '<article class="rounded-[24px] border p-5 shadow-soft ' + toneClasses + '">',
      '  <div class="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-white/80">' + workspaceIcon(iconName) + "</div>",
      '  <h3 class="mt-4 text-lg font-bold text-ink">' + title + "</h3>",
      '  <p class="mt-2 text-sm leading-7">' + body + "</p>",
      "</article>"
    ].join("");
  }

  function alertCard(item, options) {
    var config = options || {};
    return [
      '<article class="rounded-[24px] border border-line bg-white p-5 shadow-soft">',
      '  <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">',
      "    <div>",
      '      <div class="flex flex-wrap items-center gap-3">' + App.UI.badge(item.severity, App.Helpers.severityLabel(item.severity)) + '<span class="text-xs font-bold uppercase tracking-[0.18em] text-slateText">' + App.Helpers.escapeHtml(item.category || "alert") + "</span></div>",
      '      <h3 class="mt-3 text-xl font-bold text-ink">' + App.Helpers.escapeHtml(item.title) + "</h3>",
      '      <p class="mt-2 text-sm leading-7 text-slateText">' + App.Helpers.escapeHtml(item.description || item.message) + "</p>",
      '      <p class="mt-3 text-xs font-semibold text-slateText">' + App.Format.shortDateTime(item.timestamp) + "</p>",
      "    </div>",
      config.actions ? '<div class="flex flex-wrap gap-3">' + config.actions + "</div>" : "",
      "  </div>",
      "</article>"
    ].join("");
  }

  function comparisonMetric(label, currentValue, proposedValue) {
    return [
      '<article class="rounded-[24px] border border-line bg-white p-5 shadow-soft">',
      '  <p class="text-sm font-semibold text-slateText">' + label + "</p>",
      '  <div class="mt-4 grid gap-3 sm:grid-cols-2">',
      '    <div class="rounded-2xl bg-surface px-4 py-3"><span class="block text-xs font-bold uppercase tracking-[0.18em] text-slateText">נוכחי</span><span class="mt-2 block text-2xl font-bold text-ink">' + currentValue + "</span></div>",
      '    <div class="rounded-2xl bg-brand-50 px-4 py-3"><span class="block text-xs font-bold uppercase tracking-[0.18em] text-slateText">מוצע</span><span class="mt-2 block text-2xl font-bold text-brand-600">' + proposedValue + "</span></div>",
      "  </div>",
      "</article>"
    ].join("");
  }

  function buildTrackModal(track) {
    return [
      '<div class="grid gap-4 sm:grid-cols-2">',
      '  <div class="rounded-2xl bg-surface p-4 text-sm text-slateText"><span class="block font-semibold text-ink">יתרה</span>' + App.Format.currency(track.outstandingBalance) + "</div>",
      '  <div class="rounded-2xl bg-surface p-4 text-sm text-slateText"><span class="block font-semibold text-ink">ריבית נוכחית</span>' + App.Format.percent(track.currentRate) + "</div>",
      '  <div class="rounded-2xl bg-surface p-4 text-sm text-slateText"><span class="block font-semibold text-ink">ריבית מקורית</span>' + App.Format.percent(track.originalRate) + "</div>",
      '  <div class="rounded-2xl bg-surface p-4 text-sm text-slateText"><span class="block font-semibold text-ink">שיטת סילוקין</span>' + App.Helpers.escapeHtml(track.amortizationMethod) + "</div>",
      '  <div class="rounded-2xl bg-surface p-4 text-sm text-slateText"><span class="block font-semibold text-ink">תחנת איפוס</span>' + App.Helpers.escapeHtml(track.nextResetDate || "לא רלוונטי") + "</div>",
      '  <div class="rounded-2xl bg-surface p-4 text-sm text-slateText"><span class="block font-semibold text-ink">קנס פירעון</span>' + App.Helpers.escapeHtml(track.prepaymentPenaltyRule) + "</div>",
      "</div>"
    ].join("");
  }

  function inputField(label, name, value, attrs) {
    return '<label class="block"><span class="mb-2 block text-sm font-semibold text-ink">' + label + '</span><input name="' + name + '" value="' + App.Helpers.escapeHtml(value) + '" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm" ' + (attrs || "") + " /></label>";
  }

  function selectField(label, name, value, options) {
    return '<label class="block"><span class="mb-2 block text-sm font-semibold text-ink">' + label + '</span><select name="' + name + '" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm">' + options.map(function (option) {
      return '<option value="' + option.value + '"' + (option.value === value ? " selected" : "") + ">" + option.label + "</option>";
    }).join("") + "</select></label>";
  }

  function checkboxField(name, checked, label) {
    return '<label class="flex items-center gap-3 rounded-2xl border border-line bg-white p-4 text-sm text-slateText"><input type="checkbox" name="' + name + '" class="h-4 w-4 rounded border-line text-brand-600 focus:ring-brand-600" ' + (checked ? "checked" : "") + " />" + label + "</label>";
  }

  function preferenceCards(profile) {
    return [
      '<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">',
      App.UI.metricCard({ label: "סבילות סיכון", value: profile.riskTolerance || "balanced", note: "הגדרת משתמש" }),
      App.UI.metricCard({ label: "רגישות לתשלום", value: profile.paymentSensitivity || "medium", note: "הגדרת משתמש" }),
      App.UI.metricCard({ label: "מטרה מרכזית", value: profile.goal || "monthly_payment", note: "חיסכון / יציבות" }),
      App.UI.metricCard({ label: "רתיעה מהצמדה", value: profile.inflationAversion || "high", note: "אינפלציה" }),
      "</div>"
    ].join("");
  }

  var pendingInterestRequest = null;

  function interestButton(label, context, recommendation) {
    return '<button type="button" class="rounded-full bg-brand-600 px-5 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700" data-interest-request="' + context + '" data-interest-recommendation="' + App.Helpers.escapeHtml(recommendation || "") + '">' + label + "</button>";
  }

  function bindInterestFlow(root) {
    if ($(root).data("interest-flow-bound")) {
      return;
    }

    $(root).data("interest-flow-bound", true);

    $(root).on("click", "[data-interest-request]", function () {
      pendingInterestRequest = {
        context: $(this).data("interest-request"),
        recommendation: $(this).data("interest-recommendation")
      };

      App.UI.showModal(
        "אישור עניין בהמלצה",
        '<div class="space-y-4"><p class="text-sm leading-7 text-slateText">המערכת אינה מפעילה את החלופה שנמצאה. אם ברצונך שנמשיך, נא לאשר עניין ונעביר את הבקשה לצוות שלנו.</p><div class="rounded-2xl border border-line bg-surface px-4 py-4 text-sm text-slateText"><span class="block font-semibold text-ink">המלצה</span>' + App.Helpers.escapeHtml(pendingInterestRequest.recommendation || "המלצת מחזור") + '</div><div class="flex flex-wrap gap-3"><button type="button" class="rounded-full bg-brand-600 px-5 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700" data-confirm-interest>אני מעוניין/ת</button><button type="button" class="rounded-full border border-line px-5 py-3 text-sm font-bold text-ink hover:border-brand-600 hover:text-brand-600" data-modal-close>לא עכשיו</button></div></div>',
        "המשך הטיפול יתבצע רק לאחר אישורך"
      );
    });
  }

  $(document).on("click", "[data-confirm-interest]", function () {
    if (!pendingInterestRequest) {
      return;
    }

    App.MockApi.submitInterestRequest(pendingInterestRequest).then(function (response) {
      App.UI.showModal(
        "הבקשה הועברה",
        '<div class="space-y-4"><p class="text-sm leading-7 text-slateText">' + App.Helpers.escapeHtml(response.message) + '</p><div class="rounded-2xl border border-success/20 bg-emerald-50 px-4 py-4 text-sm text-success">ניצור קשר עם הלקוח/ה בקרוב לאחר בדיקה אנושית.</div></div>',
        "אין ביצוע אוטומטי של מחזור דרך הממשק"
      );
      pendingInterestRequest = null;
    });
  });

  App.Pages.dashboard = function (root) {
    Promise.all([App.MockApi.getDashboard(), App.MockApi.getMortgage(), App.MockApi.getAlerts()]).then(function (results) {
      var dashboard = results[0];
      var mortgage = results[1];
      var alerts = results[2];

      root.innerHTML = [
        App.UI.renderPageHeader({
          eyebrow: "decision dashboard",
          title: "לוח מחוונים: האם צריך לפעול עכשיו?",
          description: "המסך הראשי מרכז את ההמלצה הנוכחית, רמת הדחיפות, החיסכון האפשרי וההתראות האחרונות כדי לענות מהר על שאלת הפעולה.",
          actions: [
            '<a href="' + App.Helpers.link("pages/analysis-center.html") + '" class="rounded-full bg-brand-600 px-5 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">למרכז הניתוח</a>',
            interestButton("אני מעוניין/ת בהמלצה", "dashboard", dashboard.recommendation.headline),
            '<a href="' + App.Helpers.link("pages/onboarding.html") + '" class="rounded-full border border-line px-5 py-3 text-sm font-bold text-ink hover:border-brand-600 hover:text-brand-600">עדכון נתונים</a>'
          ].join("")
        }),
        recommendationBanner(dashboard.recommendation),
        '<section class="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">',
        App.UI.metricCard({ label: "תשלום חודשי כיום", value: App.Format.currency(mortgage.currentMonthlyPayment), note: "על בסיס נתוני התיק העדכניים" }),
        App.UI.metricCard({ label: "תשלום משוער לאחר מחזור", value: App.Format.currency(dashboard.estimatedRefinancePayment), note: "תרחיש מרכזי", badge: { tone: "success", label: "פחות לחץ תזרימי" } }),
        App.UI.metricCard({ label: "חיסכון נטו חזוי", value: App.Format.currency(dashboard.projectedNetSavings), note: "כולל עלויות מעבר" }),
        App.UI.metricCard({ label: "נקודת איזון", value: dashboard.breakEvenMonths + " חודשים", note: App.Format.shortDateTime(dashboard.lastAnalysisTime) }),
        "</section>",
        '<section class="mt-6 grid gap-6 xl:grid-cols-[1fr,0.95fr]">',
        '  <div class="space-y-6">',
        '    <article class="rounded-[28px] border border-line bg-white p-6 shadow-soft"><div class="flex items-start justify-between gap-4"><div><p class="text-sm font-bold uppercase tracking-[0.18em] text-slateText">urgency</p><h2 class="mt-2 text-2xl font-bold text-ink">' + dashboard.urgency.label + '</h2><p class="mt-3 text-sm leading-7 text-slateText">' + dashboard.urgency.description + '</p></div>' + App.UI.badge("warning", "נדרש מעקב") + '</div><div class="mt-6 flex flex-wrap gap-3">' + interestButton("אשר/י עניין להמשך טיפול", "dashboard-urgency", dashboard.recommendation.headline) + '<a href="' + App.Helpers.link("pages/partial-refinance.html") + '" class="rounded-full border border-line px-5 py-3 text-sm font-bold text-ink hover:border-brand-600 hover:text-brand-600">בדיקת מחזור חלקי</a></div><p class="mt-4 text-sm leading-7 text-slateText">המערכת אינה מממשת את המחזור שנמצא. לאחר אישור עניין, הבקשה נשלחת לצוות וניצור קשר עם הלקוח/ה בהקדם.</p></article>',
        App.UI.chartPlaceholder("חלוקת יתרה בין מסלולים", mortgage.tracks.map(function (track) {
          return {
            label: track.label,
            value: App.Format.currency(track.outstandingBalance),
            width: Math.max(20, Math.round((track.outstandingBalance / mortgage.outstandingBalance) * 100)),
            className: track.type === "prime_floating" ? "bg-accent" : track.type.indexOf("fixed") === 0 ? "bg-brand-600" : "bg-slate-300"
          };
        })),
        "  </div>",
        '  <div class="space-y-6">',
        '    <article class="rounded-[28px] border border-line bg-white p-6 shadow-soft"><h2 class="text-2xl font-bold text-ink">התראות אחרונות</h2><div class="mt-5 space-y-4">' + alerts.active.slice(0, 3).map(function (item) {
          return alertCard(item, {
            actions: '<button type="button" class="rounded-full border border-line px-4 py-2 text-xs font-semibold text-ink hover:border-brand-600 hover:text-brand-600" data-alert-details="' + item.id + '">פרטים</button>'
          });
        }).join("") + '</div><div class="mt-4"><a href="' + App.Helpers.link("pages/alerts.html") + '" class="text-sm font-bold text-brand-600">למרכז ההתראות</a></div></article>',
        '    <article class="rounded-[28px] border border-line bg-white p-6 shadow-soft"><h2 class="text-2xl font-bold text-ink">צילום מצב משכנתא</h2><div class="mt-5 grid gap-4 sm:grid-cols-2">' +
          App.UI.metricCard({ label: "בנק נוכחי", value: App.Helpers.escapeHtml(mortgage.lender), note: "מקור המשכנתא" }) +
          App.UI.metricCard({ label: "יתרה לסילוק", value: App.Format.currency(mortgage.outstandingBalance), note: "סך כל המסלולים" }) +
          App.UI.metricCard({ label: "מסלולים פעילים", value: String(mortgage.tracks.length), note: "חלקם משתנים" }) +
          App.UI.metricCard({ label: "יתרת תקופה", value: App.Format.relativeMonths(mortgage.remainingTermMonths), note: "כולל מסלולים משתנים" }) +
        "</div></article>",
        "  </div>",
        "</section>"
      ].join("");

      bindInterestFlow(root);

      $(root).on("click", "[data-alert-details]", function () {
        var id = $(this).data("alert-details");
        var item = alerts.active.filter(function (alert) { return alert.id === id; })[0];
        if (item) {
          App.UI.showModal(item.title, '<p class="text-sm leading-7 text-slateText">' + App.Helpers.escapeHtml(item.description || item.message) + "</p>", App.Format.shortDateTime(item.timestamp));
        }
      });
    });
  };

  App.Pages["mortgage-workspace"] = function (root) {
    Promise.all([App.MockApi.getMortgage(), App.MockApi.getDashboard()]).then(function (results) {
      var mortgage = results[0];
      var dashboard = results[1];

      root.innerHTML = [
        App.UI.renderPageHeader({
          eyebrow: "mortgage workspace",
          title: "מרחב המשכנתא",
          description: "המסך המרכזי לניהול נתוני המשכנתא הקיימת: סקירה, מסלולים, עלויות יציאה ועריכת נתונים.",
          actions: '<a href="' + App.Helpers.link("pages/onboarding.html") + '" class="rounded-full bg-brand-600 px-5 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">עריכת תיק</a>'
        }),
        App.UI.tabs({
          tabs: [
            {
              key: "overview",
              label: "Overview",
              content: [
                '<div class="grid gap-4 lg:grid-cols-3">',
                workspaceSignal("תחנת איפוס קרובה", "למסלול המשתנה יש תחנת איפוס קרובה יחסית ולכן כדאי לעקוב מקרוב אחר תנאי השוק.", "warning", "reset"),
                workspaceSignal("חשיפת מדד פעילה", "המסלול הצמוד ממשיך לייצר חשיפה לאינפלציה ולכן הוא נבחן היטב בתוך ההמלצה.", "info", "risk"),
                workspaceSignal("עוגן הגנה בתיק", "החלק הקבוע הלא צמוד עדיין מספק שכבת יציבות חשובה גם תחת תרחישי לחץ.", "success", "shield"),
                "</div>",
                '<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">',
                App.UI.metricCard({ label: "יתרה כוללת", value: App.Format.currency(mortgage.outstandingBalance), note: mortgage.lender }),
                App.UI.metricCard({ label: "תשלום חודשי", value: App.Format.currency(mortgage.currentMonthlyPayment), note: "חיוב חודשי נוכחי" }),
                App.UI.metricCard({ label: "רמת דחיפות", value: dashboard.urgency.label, note: dashboard.urgency.description }),
                App.UI.metricCard({ label: "סך מסלולים", value: String(mortgage.tracks.length), note: "חלקם משתנים" }),
                "</div>",
                '<div class="mt-6 grid gap-6 lg:grid-cols-[1fr,0.9fr]">',
                App.UI.table({
                  columns: [
                    { label: "מסלול", key: "label" },
                    { label: "איפוס הבא", key: "nextResetDate" },
                    { label: "הצמדה", key: "linkageType" },
                    { label: "קנס / כלל", key: "prepaymentPenaltyRule" }
                  ],
                  rows: mortgage.tracks
                }),
                '<article class="rounded-[28px] border border-line bg-white p-6 shadow-soft"><h3 class="text-2xl font-bold text-ink">סיכום חשיפה לסיכון</h3><div class="mt-5 space-y-4 text-sm text-slateText"><div class="rounded-2xl bg-surface px-4 py-3">חשיפת מדד משמעותית במסלול הקבוע הצמוד.</div><div class="rounded-2xl bg-surface px-4 py-3">סיכון ריבית במסלול הפריים פעיל ומצדיק ניטור שוטף.</div><div class="rounded-2xl bg-surface px-4 py-3">תחנת האיפוס הבאה הופכת את מסלול המשתנה לכלי מרכזי בהחלטת המחזור.</div></div></article>',
                "</div>"
              ].join("")
            },
            {
              key: "tracks",
              label: "Tracks",
              content: '<div class="grid gap-6 xl:grid-cols-2">' + mortgage.tracks.map(trackCard).join("") + "</div>"
            },
            {
              key: "costs",
              label: "Costs & penalties",
              content: '<div class="space-y-6">' + App.UI.table({
                columns: [
                  { label: "רכיב", key: "label" },
                  { label: "סכום", render: function (row) { return App.Format.currency(row.value); } }
                ],
                rows: [
                  { label: "עמלת פירעון", value: mortgage.refinanceCosts.prepaymentFee },
                  { label: "שכר טרחה משפטי", value: mortgage.refinanceCosts.legalFee },
                  { label: "שמאות", value: mortgage.refinanceCosts.appraisal },
                  { label: "רישום", value: mortgage.refinanceCosts.registration },
                  { label: "יועץ / תפעול", value: mortgage.refinanceCosts.advisor }
                ]
              }) + '<article class="rounded-[28px] border border-warning/20 bg-amber-50 p-6"><h3 class="text-xl font-bold text-warning">הערת סיכון</h3><p class="mt-3 text-sm leading-7 text-warning">עמלת הפירעון במסלול הקבוע עשויה להשתנות עד ביצוע בפועל. כדאי להוציא דוח עדכני מהבנק לפני החלטה.</p></article></div>'
            },
            {
              key: "edit",
              label: "Edit data",
              content: '<div class="rounded-[28px] border border-line bg-white p-6 shadow-soft"><h3 class="text-2xl font-bold text-ink">עדכון הנתונים שמזינים את ההמלצה</h3><p class="mt-3 text-sm leading-7 text-slateText">לצורך שמירה על המלצה אמינה, יש לעדכן יתרות, מסלולים ועלויות בכל שינוי מהותי.</p><div class="mt-6 grid gap-4 sm:grid-cols-2"><div class="rounded-2xl bg-surface px-4 py-3 text-sm text-slateText">עודכן לאחרונה: ' + App.Format.shortDateTime(dashboard.lastAnalysisTime) + '</div><div class="rounded-2xl bg-surface px-4 py-3 text-sm text-slateText">בנק נוכחי: ' + App.Helpers.escapeHtml(mortgage.lender) + '</div></div><div class="mt-6"><a href="' + App.Helpers.link("pages/onboarding.html") + '" class="rounded-full bg-brand-600 px-5 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">פתיחת אשף העריכה</a></div></div>'
            }
          ]
        })
      ].join("");

      $(root).on("click", "[data-track-detail]", function () {
        var id = $(this).data("track-detail");
        var track = mortgage.tracks.filter(function (item) { return item.id === id; })[0];
        if (track) {
          App.UI.showModal(track.label, buildTrackModal(track), "פרטי מסלול מלאים");
        }
      });
    });
  };

  App.Pages["analysis-center"] = function (root) {
    Promise.all([App.MockApi.getAnalysis(), App.MockApi.getDashboard()]).then(function (results) {
      var analysis = results[0];
      var dashboard = results[1];

      root.innerHTML = [
        App.UI.renderPageHeader({
          eyebrow: "analysis center",
          title: "מרכז ניתוח",
          description: "השוואה מלאה בין השארת המשכנתא הקיימת לבין מחזור עכשיו, כולל עלות כוללת, תשלום חודשי, NPV, סיכון והסבר להמלצה.",
          actions: interestButton("אשר/י עניין בהמלצה", "analysis-center", dashboard.recommendation.headline) + '<a href="' + App.Helpers.link("pages/partial-refinance.html") + '" class="rounded-full border border-line px-5 py-3 text-sm font-bold text-ink hover:border-brand-600 hover:text-brand-600">השוואת מחזור חלקי</a>'
        }),
        recommendationBanner(dashboard.recommendation),
        '<div class="mt-6">' + App.UI.tabs({
          tabs: [
            {
              key: "summary",
              label: "Summary",
              content: '<div class="grid gap-4 lg:grid-cols-2">' + [
                comparisonMetric("תשלום חודשי", App.Format.currency(analysis.keepCurrent.monthlyPayment), App.Format.currency(analysis.refinanceNow.monthlyPayment)),
                comparisonMetric("עלות כוללת עתידית", App.Format.currency(analysis.keepCurrent.totalRemainingCost), App.Format.currency(analysis.refinanceNow.totalRemainingCost)),
                comparisonMetric("רמת סיכון", String(analysis.keepCurrent.riskScore), String(analysis.refinanceNow.riskScore)),
                comparisonMetric("חשיפת מדד", analysis.keepCurrent.inflationExposure, analysis.refinanceNow.inflationExposure)
              ].join("") + "</div>"
            },
            {
              key: "cost",
              label: "Cost comparison",
              content: '<div class="grid gap-6 lg:grid-cols-[1fr,0.9fr]">' + App.UI.table({
                columns: [
                  { label: "מדד", key: "label" },
                  { label: "השארה", key: "current" },
                  { label: "מחזור", key: "proposed" }
                ],
                rows: [
                  { label: "תשלום חודשי", current: App.Format.currency(analysis.keepCurrent.monthlyPayment), proposed: App.Format.currency(analysis.refinanceNow.monthlyPayment) },
                  { label: "עלות כוללת עתידית", current: App.Format.currency(analysis.keepCurrent.totalRemainingCost), proposed: App.Format.currency(analysis.refinanceNow.totalRemainingCost) },
                  { label: "עלויות כניסה", current: "₪0", proposed: App.Format.currency(analysis.refinanceNow.upfrontCost) },
                  { label: "חיסכון צפוי", current: "—", proposed: App.Format.currency(analysis.refinanceNow.projectedSavings) }
                ]
              }) + '<article class="rounded-[28px] border border-line bg-white p-6 shadow-soft"><h3 class="text-2xl font-bold text-ink">מדדים פיננסיים עיקריים</h3><div class="mt-5 grid gap-4 sm:grid-cols-2">' + App.UI.metricCard({ label: "Break-even", value: analysis.refinanceNow.breakEvenMonths + " חודשים", note: "אחרי קיזוז עלויות כניסה" }) + App.UI.metricCard({ label: "NPV", value: App.Format.currency(analysis.refinanceNow.npv), note: "תרחיש בסיס" }) + "</div></article></div>"
            },
            {
              key: "payment",
              label: "Payment path",
              content: App.UI.chartPlaceholder("מסלול תזרים מצטבר", analysis.paymentPath.map(function (item, index) {
                return {
                  label: "חודש " + item.month + " | נוכחי " + App.Format.currency(Math.abs(item.current)) + " | מחזור " + App.Format.currency(Math.abs(item.proposed)),
                  value: App.Format.currency(Math.abs(item.proposed)),
                  width: Math.max(18, 100 - index * 12),
                  className: index % 2 === 0 ? "bg-brand-600" : "bg-accent"
                };
              }))
            },
            {
              key: "risk",
              label: "Risk comparison",
              content: '<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">' + [
                App.UI.metricCard({ label: "סיכון נוכחי", value: String(analysis.keepCurrent.riskScore), badge: { tone: App.Helpers.riskTone(analysis.keepCurrent.riskScore), label: "risk score" } }),
                App.UI.metricCard({ label: "סיכון לאחר מחזור", value: String(analysis.refinanceNow.riskScore), badge: { tone: App.Helpers.riskTone(analysis.refinanceNow.riskScore), label: "risk score" } }),
                App.UI.metricCard({ label: "חשיפת מדד", value: analysis.keepCurrent.inflationExposure, note: "נוכחי" }),
                App.UI.metricCard({ label: "חשיפת מדד לאחר מחזור", value: analysis.refinanceNow.inflationExposure, note: "מוצע" })
              ].join("") + '</div><article class="mt-6 rounded-[28px] border border-line bg-white p-6 shadow-soft"><p class="text-sm leading-7 text-slateText">הירידה בסיכון מגיעה בעיקר מצמצום מסלולים משתנים וצמודי מדד. המשמעות היא תזרים צפוי יותר ופחות רגישות לשינויי ריבית ואינפלציה.</p></article>'
            },
            {
              key: "explanation",
              label: "Explanation",
              content: '<div class="space-y-4">' + analysis.explanation.map(function (item, index) {
                return '<article class="rounded-[24px] border border-line bg-white p-5 shadow-soft"><p class="text-sm font-bold text-slateText">סיבה ' + (index + 1) + '</p><p class="mt-2 text-sm leading-7 text-ink">' + item + "</p></article>";
              }).join("") + "</div>"
            },
            {
              key: "assumptions",
              label: "Assumptions",
              content: App.UI.accordion(analysis.assumptions.map(function (item, index) {
                return { question: "הנחה " + (index + 1), answer: item };
              }))
            }
          ]
        }) + "</div>"
      ].join("");

      bindInterestFlow(root);
    });
  };

  App.Pages["partial-refinance"] = function (root) {
    Promise.all([App.MockApi.getPartialRefinance(), App.MockApi.getDashboard()]).then(function (results) {
      var partial = results[0];
      var dashboard = results[1];

      root.innerHTML = [
        App.UI.renderPageHeader({
          eyebrow: "partial refinance",
          title: "מחזור חלקי לעומת מחזור מלא",
          description: "המסך הזה נועד להראות מתי כדאי למחזר רק חלק מהמסלולים ולהשאיר מסלולים אחרים כפי שהם.",
          actions: interestButton("אני מעוניין/ת במחזור החלקי", "partial-refinance", dashboard.recommendation.headline) + '<a href="' + App.Helpers.link("pages/analysis-center.html") + '" class="rounded-full border border-line px-5 py-3 text-sm font-bold text-ink hover:border-brand-600 hover:text-brand-600">חזרה לניתוח המלא</a>'
        }),
        recommendationBanner(dashboard.recommendation),
        '<section class="mt-6 grid gap-6 lg:grid-cols-2">',
        '  <article class="rounded-[28px] border border-success/20 bg-emerald-50 p-6 shadow-soft"><h2 class="text-2xl font-bold text-success">מסלולים מומלצים למחזור</h2><div class="mt-5 space-y-4">' + partial.refinance.map(function (item) {
          return '<div class="rounded-2xl border border-success/20 bg-white px-4 py-4"><div class="flex items-center justify-between"><span class="font-bold text-ink">' + item.label + '</span><span class="text-sm font-semibold text-success">' + App.Format.currency(item.savingsContribution) + '</span></div><p class="mt-2 text-sm text-slateText">' + item.reason + "</p></div>";
        }).join("") + "</div></article>",
        '  <article class="rounded-[28px] border border-line bg-white p-6 shadow-soft"><h2 class="text-2xl font-bold text-ink">מסלולים שכדאי לשמור</h2><div class="mt-5 space-y-4">' + partial.keep.map(function (item) {
          return '<div class="rounded-2xl border border-line bg-surface px-4 py-4"><div class="flex items-center justify-between"><span class="font-bold text-ink">' + item.label + '</span><span class="text-sm font-semibold text-slateText">' + item.riskReduction + '</span></div><p class="mt-2 text-sm text-slateText">' + item.reason + "</p></div>";
        }).join("") + "</div></article>",
        "</section>",
        '<section class="mt-6 grid gap-6 lg:grid-cols-[1fr,0.95fr]">',
        App.UI.table({
          columns: [
            { label: "חלופה", key: "option" },
            { label: "תשלום חודשי", key: "payment" },
            { label: "חיסכון נטו", key: "savings" },
            { label: "סיכון", key: "risk" }
          ],
          rows: [
            { option: "השארה", payment: App.Format.currency(7640), savings: "₪0", risk: "גבוה יחסית" },
            { option: "מחזור מלא", payment: App.Format.currency(6840), savings: App.Format.currency(196200), risk: "נמוך" },
            { option: "מחזור חלקי", payment: App.Format.currency(6980), savings: App.Format.currency(184300), risk: "נמוך-בינוני" }
          ]
        }),
        '<article class="rounded-[28px] border border-line bg-white p-6 shadow-soft"><h3 class="text-2xl font-bold text-ink">מגבלות מדיניות / חוקיות</h3><div class="mt-5 space-y-3">' + partial.constraints.map(function (item) {
          return '<div class="rounded-2xl bg-surface px-4 py-3 text-sm leading-7 text-slateText">' + item + "</div>";
        }).join("") + "</div></article>",
        "</section>"
      ].join("");

      bindInterestFlow(root);
    });
  };

  App.Pages.scenarios = function (root) {
    App.MockApi.getScenarios().then(function (scenarioData) {
      var selected = "בסיס";

      function renderScenarioPage() {
        var row = scenarioData.rows.filter(function (item) { return item.name === selected; })[0] || scenarioData.rows[0];
        root.innerHTML = [
          App.UI.renderPageHeader({
            eyebrow: "scenario testing",
            title: "תרחישים, רגישות ועמידות",
            description: "בדיקה אם ההמלצה נשארת יציבה גם כאשר האינפלציה, הריבית או אופק ההחזקה משתנים.",
            actions: '<a href="' + App.Helpers.link("pages/analysis-center.html") + '" class="rounded-full border border-line px-5 py-3 text-sm font-bold text-ink hover:border-brand-600 hover:text-brand-600">חזרה למרכז הניתוח</a>'
          }),
          '<section class="rounded-[32px] border border-line bg-white p-6 shadow-soft"><div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between"><div><h2 class="text-2xl font-bold text-ink">בחירת תרחיש</h2><p class="mt-2 text-sm text-slateText">התרחיש המסומן משפיע על כרטיס הסיכום העליון.</p></div><div class="flex flex-wrap gap-3">' + scenarioData.rows.map(function (item) {
            return '<button type="button" class="rounded-full px-4 py-2 text-sm font-semibold ' + (item.name === selected ? "bg-brand-600 text-white" : "bg-surface text-slateText") + '" data-scenario="' + item.name + '">' + item.name + "</button>";
          }).join("") + "</div></div></section>",
          '<section class="mt-6 grid gap-6 lg:grid-cols-[1fr,0.9fr]">',
          '  <div class="space-y-6">',
          '    <article class="rounded-[28px] border border-line bg-white p-6 shadow-soft"><div class="flex items-center justify-between">' + App.UI.badge(row.verdict === "גבולי" ? "warning" : "success", row.verdict) + '<span class="text-sm text-slateText">' + selected + '</span></div><h2 class="mt-4 text-3xl font-extrabold text-ink">' + App.Format.currency(row.savings) + '</h2><p class="mt-2 text-sm leading-7 text-slateText">חיסכון צפוי בתרחיש הנבחר. נקודת איזון: ' + row.breakEven + ' חודשים.</p></article>',
          App.UI.table({
            columns: [
              { label: "תרחיש", key: "name" },
              { label: "תשלום", render: function (item) { return App.Format.currency(item.payment); } },
              { label: "חיסכון", render: function (item) { return App.Format.currency(item.savings); } },
              { label: "Break-even", render: function (item) { return item.breakEven + " חודשים"; } },
              { label: "פסק דין", key: "verdict" }
            ],
            rows: scenarioData.rows
          }),
          "  </div>",
          '  <div class="space-y-6">',
          '    <article class="rounded-[28px] border border-line bg-white p-6 shadow-soft"><h3 class="text-2xl font-bold text-ink">Robustness verdict</h3><p class="mt-3 text-sm leading-7 text-slateText">' + scenarioData.verdict + "</p></article>",
          '    <article class="rounded-[28px] border border-line bg-white p-6 shadow-soft"><h3 class="text-2xl font-bold text-ink">Sensitivity view</h3><div class="mt-5 space-y-4">' + scenarioData.sensitivity.map(function (item) {
            return '<div class="rounded-2xl bg-surface px-4 py-4"><div class="flex items-center justify-between"><span class="font-bold text-ink">' + item.label + '</span><span class="text-xs font-bold uppercase tracking-[0.16em] text-slateText">' + item.impact + '</span></div><p class="mt-2 text-sm text-slateText">' + item.note + "</p></div>";
          }).join("") + "</div></article>",
          "  </div>",
          "</section>"
        ].join("");
      }

      renderScenarioPage();

      $(root).on("click", "[data-scenario]", function () {
        selected = $(this).data("scenario");
        renderScenarioPage();
      });
    });
  };

  App.Pages.alerts = function (root) {
    function renderAlerts(alertData, filter) {
      var filteredActive = alertData.active.filter(function (item) {
        return filter === "all" ? true : item.severity === filter;
      });

      root.innerHTML = [
        App.UI.renderPageHeader({
          eyebrow: "alerts center",
          title: "מרכז התראות",
          description: "מעקב אחר התראות פעילות, היסטוריה, פריטים שסומנו כטופלו והעדפות ההתראה האישיות.",
          actions: '<a href="' + App.Helpers.link("pages/settings.html") + '" class="rounded-full border border-line px-5 py-3 text-sm font-bold text-ink hover:border-brand-600 hover:text-brand-600">להעדפות כלליות</a>'
        }),
        App.UI.tabs({
          tabs: [
            {
              key: "active",
              label: "Active alerts",
              content: [
                '<div class="mb-5 flex flex-wrap items-center gap-3">',
                '<span class="text-sm font-semibold text-slateText">סינון לפי חומרה:</span>',
                '<button type="button" class="rounded-full px-4 py-2 text-sm font-semibold ' + (filter === "all" ? "bg-brand-600 text-white" : "bg-surface text-slateText") + '" data-alert-filter="all">הכל</button>',
                '<button type="button" class="rounded-full px-4 py-2 text-sm font-semibold ' + (filter === "high" ? "bg-brand-600 text-white" : "bg-surface text-slateText") + '" data-alert-filter="high">גבוהה</button>',
                '<button type="button" class="rounded-full px-4 py-2 text-sm font-semibold ' + (filter === "medium" ? "bg-brand-600 text-white" : "bg-surface text-slateText") + '" data-alert-filter="medium">בינונית</button>',
                '<button type="button" class="rounded-full px-4 py-2 text-sm font-semibold ' + (filter === "low" ? "bg-brand-600 text-white" : "bg-surface text-slateText") + '" data-alert-filter="low">נמוכה</button>',
                "</div>",
                '<div class="space-y-4">' + (filteredActive.length ? filteredActive.map(function (item) {
                  return alertCard(item, {
                    actions: '<button type="button" class="rounded-full border border-line px-4 py-2 text-xs font-semibold text-ink hover:border-brand-600 hover:text-brand-600" data-view-alert="' + item.id + '">פרטים</button><button type="button" class="rounded-full border border-line px-4 py-2 text-xs font-semibold text-slateText hover:border-danger hover:text-danger" data-dismiss-alert="' + item.id + '">סמן כטופל</button>'
                  });
                }).join("") : '<div class="rounded-[24px] border border-line bg-white px-5 py-10 text-center text-sm text-slateText">אין כרגע התראות פעילות בפילטר שנבחר.</div>') + "</div>"
              ].join("")
            },
            {
              key: "history",
              label: "History",
              content: '<div class="space-y-4">' + alertData.history.map(function (item) { return alertCard(item); }).join("") + "</div>"
            },
            {
              key: "dismissed",
              label: "Dismissed",
              content: '<div class="space-y-4">' + alertData.dismissed.map(function (item) { return alertCard(item); }).join("") + "</div>"
            }
          ]
        })
      ].join("");

      $(root).off("click.alerts").on("click.alerts", "[data-alert-filter]", function () {
        renderAlerts(alertData, $(this).data("alert-filter"));
      });

      $(root).off("click.alert-details").on("click.alert-details", "[data-view-alert]", function () {
        var id = $(this).data("view-alert");
        var item = alertData.active.concat(alertData.history, alertData.dismissed).filter(function (alert) { return alert.id === id; })[0];
        if (item) {
          App.UI.showModal(item.title, '<p class="text-sm leading-7 text-slateText">' + App.Helpers.escapeHtml(item.description) + "</p>", App.Format.shortDateTime(item.timestamp));
        }
      });

      $(root).off("click.dismiss").on("click.dismiss", "[data-dismiss-alert]", function () {
        App.MockApi.dismissAlert($(this).data("dismiss-alert")).then(function (nextData) {
          renderAlerts(nextData, filter);
        });
      });
    }

    App.MockApi.getAlerts().then(function (data) {
      renderAlerts(data, "all");
    });
  };

  App.Pages.settings = function (root) {
    App.MockApi.getProfile().then(function (profile) {
      var notifications = App.State.load().notifications;
      var profileState = $.extend({}, profile);

      root.innerHTML = [
        App.UI.renderPageHeader({
          eyebrow: "settings & profile",
          title: "הגדרות ופרופיל",
          description: "ניהול פרופיל אישי, העדפות פיננסיות, הנחות משק בית, התראות ואבטחת חשבון.",
          actions: '<a href="' + App.Helpers.link("pages/dashboard.html") + '" class="rounded-full border border-line px-5 py-3 text-sm font-bold text-ink hover:border-brand-600 hover:text-brand-600">חזרה לדשבורד</a>'
        }),
        App.UI.tabs({
          tabs: [
            {
              key: "personal",
              label: "Personal profile",
              content: '<form id="profile-form" class="wizard-track-grid">' +
                inputField("שם משתמש", "username", profile.username || profile.fullName) +
                inputField("שם מלא", "fullName", profile.fullName) +
                inputField("עיר", "city", profile.city) +
                inputField("טלפון", "phone", profile.phone) +
                inputField("גיל", "age", profile.age || "", 'type="number" min="18" max="120"') +
                selectField("מגדר", "gender", profile.gender || "", [
                  { value: "", label: "לא נבחר" },
                  { value: "female", label: "אישה" },
                  { value: "male", label: "גבר" },
                  { value: "other", label: "אחר / מעדיף לא לציין" }
                ]) +
                selectField("מצב משפחתי", "maritalStatus", profile.maritalStatus || "", [
                  { value: "", label: "לא נבחר" },
                  { value: "single", label: "רווק/ה" },
                  { value: "married", label: "נשוי/אה" },
                  { value: "divorced", label: "גרוש/ה" },
                  { value: "widowed", label: "אלמן/ה" }
                ]) +
                inputField("עיסוק", "occupation", profile.occupation || "") +
                inputField("אופק החזקה", "holdingPeriodYears", profile.holdingPeriodYears, 'type="number" min="1" max="30"') +
                '<div class="col-span-full"><div id="profile-state" class="text-sm"></div><button type="submit" class="mt-4 rounded-full bg-brand-600 px-5 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">שמירת פרופיל</button></div>' +
              "</form>"
            },
            {
              key: "financial",
              label: "Financial preferences",
              content: '<form id="preferences-form" class="space-y-5">' +
                '<div class="grid gap-4 md:grid-cols-2">' +
                  selectField("סבילות סיכון", "riskTolerance", profile.riskTolerance, [
                    { value: "low", label: "נמוכה" },
                    { value: "balanced", label: "מאוזנת" },
                    { value: "high", label: "גבוהה" }
                  ]) +
                  selectField("רגישות לתשלום חודשי", "paymentSensitivity", profile.paymentSensitivity, [
                    { value: "low", label: "נמוכה" },
                    { value: "medium", label: "בינונית" },
                    { value: "high", label: "גבוהה" }
                  ]) +
                  selectField("העדפה עיקרית", "goal", profile.goal, [
                    { value: "monthly_payment", label: "תשלום חודשי נמוך יותר" },
                    { value: "total_cost", label: "עלות כוללת נמוכה יותר" },
                    { value: "risk_reduction", label: "צמצום סיכון" }
                  ]) +
                "</div>" +
                '<div class="mt-2">' + preferenceCards(profile) + '</div>' +
                '<div id="preferences-state" class="text-sm"></div>' +
                '<button type="submit" class="rounded-full bg-brand-600 px-5 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">שמירת העדפות פיננסיות</button>' +
              "</form>"
            },
            {
              key: "household",
              label: "Household assumptions",
              content: '<form id="household-form" class="space-y-5">' +
                '<div class="grid gap-4 md:grid-cols-2">' +
                  inputField("אופק החזקה (שנים)", "holdingPeriodYears", profile.holdingPeriodYears, 'type="number" min="1" max="30"') +
                  selectField("רתיעה מהצמדה", "inflationAversion", profile.inflationAversion, [
                    { value: "low", label: "נמוכה" },
                    { value: "medium", label: "בינונית" },
                    { value: "high", label: "גבוהה" }
                  ]) +
                  selectField("רתיעה מסיכון איפוס", "resetRiskAversion", profile.resetRiskAversion, [
                    { value: "low", label: "נמוכה" },
                    { value: "medium", label: "בינונית" },
                    { value: "high", label: "גבוהה" }
                  ]) +
                "</div>" +
                '<div class="rounded-[24px] border border-line bg-white p-5 shadow-soft text-sm leading-7 text-slateText">לצורך עדכון עמוק יותר של מבנה המשכנתא והנחות החישוב, אפשר לחזור לאשף ההקמה.</div>' +
                '<div id="household-state" class="text-sm"></div>' +
                '<div class="flex flex-wrap gap-3"><button type="submit" class="rounded-full bg-brand-600 px-5 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">שמירת הנחות משק בית</button><a href="' + App.Helpers.link("pages/onboarding.html") + '" class="rounded-full border border-line px-5 py-3 text-sm font-bold text-ink hover:border-brand-600 hover:text-brand-600">פתיחת אשף ההקמה</a></div>' +
              "</form>"
            },
            {
              key: "notifications",
              label: "__removed",
              content: '<form id="settings-notifications" class="space-y-4">' +
                checkboxField("email", notifications.email, "עדכוני אימייל") +
                checkboxField("sms", notifications.sms, "עדכוני SMS") +
                checkboxField("weeklyDigest", notifications.weeklyDigest, "סיכום שבועי") +
                checkboxField("severeOnly", notifications.severeOnly, "חומרה גבוהה בלבד") +
                '<div id="settings-notifications-state" class="text-sm"></div><button type="submit" class="rounded-full bg-brand-600 px-5 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">שמירת התראות</button>' +
              "</form>"
            },
            {
              key: "security",
              label: "__removed",
              content: '<div class="space-y-4"><article class="rounded-[24px] border border-line bg-white p-5 shadow-soft"><h3 class="text-xl font-bold text-ink">אבטחת חשבון</h3><p class="mt-3 text-sm leading-7 text-slateText">לצורך הדגמה, איפוס סיסמה מנוהל דרך מסכי האימות. אפשר לבדוק גם מצב token expired.</p><div class="mt-4 flex flex-wrap gap-3"><a href="' + App.Helpers.link("pages/reset-password.html") + '" class="rounded-full bg-brand-600 px-5 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">איפוס סיסמה</a><a href="' + App.Helpers.link("pages/reset-password.html?token=expired") + '" class="rounded-full border border-line px-5 py-3 text-sm font-bold text-ink hover:border-brand-600 hover:text-brand-600">הדגמת token expired</a></div></article></div>'
            }
          ]
        })
      ].join("");

      $(root).find('[data-tab-button="notifications"], [data-tab-panel="notifications"], [data-tab-button="security"], [data-tab-panel="security"]').remove();

      $(root).on("submit", "#profile-form", function (event) {
        event.preventDefault();
        profileState = $.extend({}, profileState, {
          username: $(this).find('[name="username"]').val(),
          fullName: $(this).find('[name="fullName"]').val(),
          city: $(this).find('[name="city"]').val(),
          phone: $(this).find('[name="phone"]').val(),
          age: $(this).find('[name="age"]').val(),
          gender: $(this).find('[name="gender"]').val(),
          maritalStatus: $(this).find('[name="maritalStatus"]').val(),
          occupation: $(this).find('[name="occupation"]').val(),
          holdingPeriodYears: Number($(this).find('[name="holdingPeriodYears"]').val() || 0),
          riskTolerance: profileState.riskTolerance,
          paymentSensitivity: profileState.paymentSensitivity,
          goal: profileState.goal,
          inflationAversion: profileState.inflationAversion,
          resetRiskAversion: profileState.resetRiskAversion
        });
        App.MockApi.updateProfile(profileState).then(function () {
          profile = profileState;
          $("#profile-state").html('<div class="rounded-2xl border border-success/20 bg-emerald-50 px-4 py-3 text-success">הפרופיל נשמר.</div>');
        });
      });

      $(root).on("submit", "#preferences-form", function (event) {
        event.preventDefault();
        profileState = $.extend({}, profileState, {
          riskTolerance: $(this).find('[name="riskTolerance"]').val(),
          paymentSensitivity: $(this).find('[name="paymentSensitivity"]').val(),
          goal: $(this).find('[name="goal"]').val()
        });
        App.MockApi.updateProfile(profileState).then(function () {
          $("#preferences-state").html('<div class="rounded-2xl border border-success/20 bg-emerald-50 px-4 py-3 text-success">העדפות פיננסיות נשמרו.</div>');
        });
      });

      $(root).on("submit", "#household-form", function (event) {
        event.preventDefault();
        profileState = $.extend({}, profileState, {
          holdingPeriodYears: Number($(this).find('[name="holdingPeriodYears"]').val() || 0),
          inflationAversion: $(this).find('[name="inflationAversion"]').val(),
          resetRiskAversion: $(this).find('[name="resetRiskAversion"]').val()
        });
        App.MockApi.updateProfile(profileState).then(function () {
          $("#household-state").html('<div class="rounded-2xl border border-success/20 bg-emerald-50 px-4 py-3 text-success">הנחות משק הבית נשמרו.</div>');
        });
      });

      $(root).on("submit", "#settings-notifications", function (event) {
        event.preventDefault();
        App.MockApi.updateNotifications({
          email: $(this).find('[name="email"]').is(":checked"),
          sms: $(this).find('[name="sms"]').is(":checked"),
          weeklyDigest: $(this).find('[name="weeklyDigest"]').is(":checked"),
          severeOnly: $(this).find('[name="severeOnly"]').is(":checked")
        }).then(function () {
          $("#settings-notifications-state").html('<div class="rounded-2xl border border-success/20 bg-emerald-50 px-4 py-3 text-success">הגדרות ההתראה נשמרו.</div>');
        });
      });
    });
  };

  App.Pages.__removedExpertPage = function (root) {
    App.MockApi.getExpertData().then(function (expert) {
      root.innerHTML = [
        App.UI.renderPageHeader({
          eyebrow: "expert next steps",
          title: "השלבים הבאים",
          description: "אחרי שההמלצה ברורה, זה המסך שמרכז בקשת חזרה, הסכמה לשיתוף הניתוח וצ'קליסט פעולה.",
          actions: '<a href="' + App.Helpers.link("pages/analysis-center.html") + '" class="rounded-full border border-line px-5 py-3 text-sm font-bold text-ink hover:border-brand-600 hover:text-brand-600">חזרה לניתוח</a>'
        }),
        '<section class="grid gap-6 lg:grid-cols-[1fr,0.95fr]">',
        '  <div class="space-y-6">',
        '    <form id="advisor-form" class="rounded-[28px] border border-line bg-white p-6 shadow-soft">',
        '      <h2 class="text-2xl font-bold text-ink">בקשת שיחה עם מומחה</h2>',
        '      <div class="mt-6 grid gap-4 sm:grid-cols-2">',
               inputField("שם מלא", "name", App.State.load().profile.fullName),
               inputField("טלפון", "phone", App.State.load().profile.phone),
               inputField("חלון זמן מועדף", "availability", "מחר 10:00-13:00"),
               inputField("הערות", "notes", "מעוניינ/ת להבין אם מחזור חלקי עדיף על מלא"),
        "      </div>",
        '      <label class="mt-4 flex items-start gap-3 rounded-2xl border border-line p-4 text-sm text-slateText"><input type="checkbox" name="shareConsent" class="mt-1 h-4 w-4 rounded border-line text-brand-600 focus:ring-brand-600" checked />אני מסכים/ה לשתף את סיכום הניתוח עם המומחה לצורך שיחה ממוקדת.</label>',
        '      <div id="advisor-state" class="mt-4 text-sm"></div>',
        '      <button type="submit" class="mt-5 rounded-full bg-brand-600 px-5 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">שליחת בקשה</button>',
        "    </form>",
        '    <article class="rounded-[28px] border border-line bg-white p-6 shadow-soft"><h2 class="text-2xl font-bold text-ink">שיתוף הניתוח</h2><p class="mt-3 text-sm leading-7 text-slateText">בממשק האמיתי אפשר יהיה לשתף PDF, סיכום JSON או קישור מאובטח. כרגע נשמרת רק הסכמה לשיתוף ומסך עבודה ברור.</p><div class="mt-5 rounded-2xl bg-surface px-4 py-3 text-sm text-slateText">שיתוף מותר רק לאחר הסכמה מפורשת של המשתמש.</div></article>',
        "  </div>",
        '  <div class="space-y-6">',
        '    <article class="rounded-[28px] border border-line bg-white p-6 shadow-soft"><h2 class="text-2xl font-bold text-ink">צ\'קליסט פעולה</h2><div class="mt-5 space-y-3">' + expert.actions.map(function (item) {
          return '<label class="flex items-start gap-3 rounded-2xl bg-surface px-4 py-3 text-sm text-slateText"><input type="checkbox" class="mt-1 h-4 w-4 rounded border-line text-brand-600 focus:ring-brand-600" /><span>' + item + "</span></label>";
        }).join("") + "</div></article>",
        '    <article class="rounded-[28px] border border-line bg-white p-6 shadow-soft"><h2 class="text-2xl font-bold text-ink">מסמכים להכנה</h2><div class="mt-5 space-y-3">' + expert.documents.map(function (item) {
          return '<div class="rounded-2xl bg-surface px-4 py-3 text-sm text-slateText">' + item + "</div>";
        }).join("") + "</div></article>",
        "  </div>",
        "</section>"
      ].join("");

      $(root).on("submit", "#advisor-form", function (event) {
        event.preventDefault();
        App.MockApi.requestAdvisor().then(function () {
          $("#advisor-state").html('<div class="rounded-2xl border border-success/20 bg-emerald-50 px-4 py-3 text-success">הבקשה נקלטה. מומחה יחזור אליך בהתאם לחלון הזמן שסומן.</div>');
        });
      });
    });
  };
})();
