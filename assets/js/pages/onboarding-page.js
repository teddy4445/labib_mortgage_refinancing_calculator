(function () {
  window.App = window.App || {};
  App.Pages = App.Pages || {};

  var trackTypeLabels = {
    fixed_non_linked: "קבועה לא צמודה",
    fixed_linked: "קבועה צמודה",
    prime_floating: "פריים / משתנה",
    adjustable_non_linked: "משתנה לא צמודה",
    adjustable_linked: "משתנה צמודה"
  };

  var trackTypeMeta = {
    fixed_non_linked: {
      linkageType: "לא צמוד",
      rateType: "קבועה",
      rateLabel: "ריבית במסלול",
      hasRateUpdateStation: false,
      note: "במסלול קבוע לא צמוד שומרים על ריבית אחת קבועה ללא תחנת עדכון ריבית."
    },
    fixed_linked: {
      linkageType: "צמוד מדד",
      rateType: "קבועה",
      rateLabel: "ריבית במסלול",
      hasRateUpdateStation: false,
      note: "במסלול קבוע צמוד הריבית קבועה, והחשיפה היא בעיקר למדד."
    },
    prime_floating: {
      linkageType: "לא צמוד",
      rateType: "משתנה",
      rateLabel: "ריבית נוכחית",
      hasRateUpdateStation: false,
      note: "מסלול פריים מתעדכן באופן שוטף לפי ריבית הפריים, ולכן אין צורך להזין תחנת עדכון ידנית."
    },
    adjustable_non_linked: {
      linkageType: "לא צמוד",
      rateType: "משתנה",
      rateLabel: "ריבית נוכחית",
      hasRateUpdateStation: true,
      note: "במסלול משתנה לא צמוד יש להזין את תחנת עדכון הריבית הבאה."
    },
    adjustable_linked: {
      linkageType: "צמוד מדד",
      rateType: "משתנה",
      rateLabel: "ריבית נוכחית",
      hasRateUpdateStation: true,
      note: "במסלול משתנה צמוד יש להזין תחנת עדכון ריבית לצד החשיפה למדד."
    }
  };

  var lenderOptions = [
    "בנק לאומי",
    "בנק הפועלים",
    "בנק דיסקונט",
    "בנק מזרחי טפחות",
    "בנק הבינלאומי",
    "בנק אגוד",
    "בנק אחר"
  ];

  function trackTypeOptions(selected) {
    return Object.keys(trackTypeLabels).map(function (key) {
      return '<option value="' + key + '"' + (key === selected ? " selected" : "") + ">" + trackTypeLabels[key] + "</option>";
    }).join("");
  }

  function normalizeTrack(track) {
    var meta = trackTypeMeta[track.type] || trackTypeMeta.fixed_non_linked;
    track.linkageType = meta.linkageType;
    track.rateType = meta.rateType;

    if (!meta.hasRateUpdateStation) {
      track.resetInterval = track.type === "prime_floating" ? "עדכון שוטף לפי פריים" : "ללא";
      track.nextResetDate = "";
    }

    return track;
  }

  function createTrack(index, seed) {
    return normalizeTrack($.extend(true, {
      id: App.Helpers.uid("track"),
      label: "מסלול " + (index + 1),
      type: "fixed_non_linked",
      outstandingBalance: 0,
      currentRate: 0,
      originalRate: 0,
      remainingTermMonths: 0,
      linkageType: "לא צמוד",
      rateType: "קבועה",
      resetInterval: "ללא",
      nextResetDate: "",
      amortizationMethod: "שפיצר",
      prepaymentPenaltyRule: "לפי תנאי הבנק"
    }, seed || {}));
  }

  function normalizeTracksCollection(state) {
    state.tracks = (state.tracks || []).slice(0, 6).map(function (track, index) {
      return createTrack(index, track);
    });

    if (!state.tracks.length) {
      state.tracks = [createTrack(0)];
    }

    state.tracksMeta = state.tracksMeta || {};
    state.tracksMeta.trackCount = state.tracks.length;
  }

  function defaultWizardState() {
    var mortgage = window.MockData.mortgage;
    var stored = App.State.load();
    var existing = stored.onboarding;
    var profile = stored.profile || {};
    var session = stored.session || {};
    var baseState = {
      basic: {
        propertySettlement: "תל אביב",
        propertyValue: mortgage.propertyValue,
        currentMonthlyPayment: mortgage.currentMonthlyPayment,
        propertyType: "מגורים_עצמיים",
        propertySubtype: "דירת_מגורים",
        yearsSinceOrigin: 0,
        remainingTermYears: 25
      },
      lender: {
        lenderName: mortgage.lender,
        originationDate: mortgage.originationDate,
        originalAmount: mortgage.originalAmount,
        originalTermMonths: 300,
        branch: "סניף מרכז",
        accountManager: "צוות משכנתאות"
      },
      tracksMeta: { trackCount: mortgage.tracks.length },
      tracks: mortgage.tracks.map(function (track, index) {
        return createTrack(index, track);
      }),
      costs: {
        prepaymentFee: mortgage.refinanceCosts.prepaymentFee,
        legalFee: mortgage.refinanceCosts.legalFee,
        appraisal: mortgage.refinanceCosts.appraisal,
        registration: mortgage.refinanceCosts.registration,
        advisor: mortgage.refinanceCosts.advisor
      },
      preferences: {
        holdingPeriodYears: 8,
        riskTolerance: "balanced",
        paymentSensitivity: "medium",
        goal: "monthly_payment",
        inflationAversion: "high",
        resetRiskAversion: "medium"
      },
      account: {
        username: profile.username || "",
        email: session.email || "",
        phone: profile.phone || "",
        password: "",
        confirmPassword: "",
        terms: false,
        privacy: false,
        emailAvailable: null,
        emailCheckStatus: ""
      },
      demographics: {
        age: "",
        gender: "",
        maritalStatus: "",
        occupation: ""
      },
      review: { confirm: false }
    };
    var state = existing ? $.extend(true, {}, baseState, App.Helpers.deepClone(existing)) : baseState;

    normalizeTracksCollection(state);
    return state;
  }

  function stepDefinitions() {
    return [
      "מידע בסיסי ובנק",
      "פרטי מסלולים",
      "עלויות מחזור",
      "העדפות",
      "פרטי חשבון",
      "סקירה ושליחה"
    ];
  }

  function setByPath(target, path, value) {
    var segments = path.split(".");
    var cursor = target;

    for (var i = 0; i < segments.length - 1; i += 1) {
      cursor[segments[i]] = cursor[segments[i]] || {};
      cursor = cursor[segments[i]];
    }

    cursor[segments[segments.length - 1]] = value;
  }

  function emailValid(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || ""));
  }

  function passwordStrong(value) {
    return String(value || "").length >= 8;
  }

  function phoneValid(value) {
    return /^[0-9+\-\s()]{9,}$/.test(String(value || ""));
  }

  function helpBubble(tooltipText) {
    return '<button type="button" class="ml-2 inline-flex h-5 w-5 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-700 hover:bg-brand-200" data-help-bubble="' + App.Helpers.escapeHtml(tooltipText) + '" title="עזרה">?</button>';
  }

  function input(label, bind, value, type, options) {
    var config = options || {};
    var fieldType = type || "text";
    var attrs = config.attrs || "";
    var hint = config.hint ? '<p class="mt-2 text-xs text-slateText">' + config.hint + "</p>" : "";
    var help = config.help ? helpBubble(config.help) : "";
    var element = "";

    if (fieldType === "select") {
      element = '<select data-bind="' + bind + '" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm">' + config.options + "</select>";
    } else if (fieldType === "checkbox") {
      return '<div class="col-span-full"><label class="flex items-start gap-3 rounded-2xl border border-line p-4 text-sm text-slateText"><input type="checkbox" data-bind="' + bind + '" class="mt-1 h-4 w-4 rounded border-line text-brand-600 focus:ring-brand-600" ' + (value ? "checked" : "") + ' /><span>' + label + "</span></label></div>";
    } else {
      element = '<input data-bind="' + bind + '" type="' + fieldType + '" value="' + App.Helpers.escapeHtml(value) + '" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm" ' + attrs + " />";
    }

    return '<label class="block"><span class="mb-2 flex items-center text-sm font-semibold text-ink">' + label + help + "</span>" + element + hint + "</label>";
  }

  function factCard(label, value) {
    return '<div class="rounded-[22px] border border-brand-100 bg-brand-50 px-4 py-4"><span class="block text-xs font-bold uppercase tracking-[0.16em] text-slateText">' + label + '</span><span class="mt-2 block text-base font-bold text-ink">' + App.Helpers.escapeHtml(value) + "</span></div>";
  }

  function infoNote(text, tone) {
    var noteTone = tone === "warning"
      ? "border border-orange-200 bg-orange-50 text-ink"
      : "border border-line bg-surface text-slateText";
    return '<div class="rounded-[24px] px-5 py-4 text-sm leading-7 ' + noteTone + '">' + text + "</div>";
  }

  function formSection(title, desc, body) {
    return '<section class="rounded-[32px] border border-line bg-white p-8 shadow-soft"><h2 class="text-3xl font-bold text-ink">' + title + '</h2><p class="mt-3 text-sm leading-7 text-slateText">' + desc + "</p>" + body + "</section>";
  }

  function moneySummary(state) {
    return {
      totalBalance: state.tracks.reduce(function (sum, track) {
        return sum + Number(track.outstandingBalance || 0);
      }, 0),
      totalFees: [
        state.costs.prepaymentFee,
        state.costs.legalFee,
        state.costs.appraisal,
        state.costs.registration,
        state.costs.advisor
      ].reduce(function (sum, value) {
        return sum + Number(value || 0);
      }, 0)
    };
  }

  function progressBar(currentStep) {
    var steps = stepDefinitions();
    var progress = ((currentStep - 1) / (steps.length - 1)) * 100;

    return [
      '<section class="wizard-progress-shell mb-6">',
      '  <div class="wizard-progress-desktop">',
      '    <div class="flex flex-wrap items-center justify-between gap-3">',
      '      <div><p class="text-xs font-bold uppercase tracking-[0.18em] text-slateText">wizard progress</p><p class="mt-1 text-sm text-slateText">שלב ' + currentStep + " מתוך " + steps.length + "</p></div>",
      '      <p class="text-sm font-semibold text-ink">' + steps[currentStep - 1] + "</p>",
      "    </div>",
      '    <div class="wizard-progress-track mt-4"><span class="wizard-progress-fill" style="width:' + progress + '%"></span></div>',
      '    <div class="wizard-stage-grid mt-5">' + steps.map(function (title, index) {
        var step = index + 1;
        var cls = step < currentStep ? "wizard-stage is-done" : step === currentStep ? "wizard-stage is-active" : "wizard-stage";
        return '<div class="' + cls + '"><span class="wizard-stage-dot"></span><span class="wizard-stage-label">' + title + "</span></div>";
      }).join("") + "</div>",
      "  </div>",
      '  <div class="wizard-progress-mobile px-1 py-2"><div class="flex items-center justify-between gap-3"><div class="flex items-center gap-3"><span class="wizard-stage is-active"><span class="wizard-stage-dot"></span></span><div><p class="text-sm font-bold text-ink">' + steps[currentStep - 1] + '</p><p class="text-xs text-slateText">שלב ' + currentStep + " מתוך " + steps.length + '</p></div></div><p class="text-sm font-bold text-brand-700">' + Math.round(progress) + '%</p></div><div class="wizard-progress-track mt-4"><span class="wizard-progress-fill" style="width:' + progress + '%"></span></div></div>',
      "</section>"
    ].join("");
  }

  function trackCard(track, index) {
    var normalizedTrack = normalizeTrack(track);
    var meta = trackTypeMeta[normalizedTrack.type] || trackTypeMeta.fixed_non_linked;
    var dynamicFields = meta.hasRateUpdateStation ? [
      input("תדירות תחנת עדכון ריבית", "tracks." + index + ".resetInterval", normalizedTrack.resetInterval, "text", {
        hint: "למשל כל 60 חודשים."
      }),
      input("תאריך תחנת עדכון הריבית הבאה", "tracks." + index + ".nextResetDate", normalizedTrack.nextResetDate, "date")
    ].join("") : "";

    return [
      '<article class="rounded-[28px] border border-line bg-white p-6 shadow-soft">',
      '  <div class="flex items-center justify-between gap-4"><div><p class="text-sm font-bold text-slateText">מסלול ' + (index + 1) + '</p><h3 class="mt-1 text-xl font-bold text-ink">' + App.Helpers.escapeHtml(normalizedTrack.label) + '</h3></div><button type="button" class="rounded-full border border-line px-4 py-2 text-xs font-semibold text-slateText hover:border-danger hover:text-danger" data-remove-track="' + index + '"' + (index === 0 ? ' disabled="disabled"' : "") + '>הסר מסלול</button></div>',
      '  <div class="mt-6 grid gap-3 sm:grid-cols-2">' + [
        factCard("הצמדה", meta.linkageType),
        factCard("אופי הריבית", meta.rateType)
      ].join("") + "</div>",
      '  <div class="mt-4 rounded-[24px] border border-line bg-surface px-5 py-4 text-sm leading-7 text-slateText">' + meta.note + "</div>",
      '  <div class="wizard-track-grid mt-6">' + [
        input("שם מסלול", "tracks." + index + ".label", normalizedTrack.label),
        input("סוג מסלול", "tracks." + index + ".type", normalizedTrack.type, "select", { options: trackTypeOptions(normalizedTrack.type) }),
        input("יתרה נוכחית", "tracks." + index + ".outstandingBalance", normalizedTrack.outstandingBalance, "number", { attrs: 'min="0" step="1000"' }),
        input(meta.rateLabel, "tracks." + index + ".currentRate", normalizedTrack.currentRate, "number", { attrs: 'min="0" step="0.01"' }),
        input("יתרת חודשים", "tracks." + index + ".remainingTermMonths", normalizedTrack.remainingTermMonths, "number", { attrs: 'min="1" step="1"' }),
        input("שיטת סילוקין", "tracks." + index + ".amortizationMethod", normalizedTrack.amortizationMethod, "select", {
          options: '<option value="שפיצר"' + (normalizedTrack.amortizationMethod === "שפיצר" ? " selected" : "") + '>שפיצר</option><option value="קרן שווה"' + (normalizedTrack.amortizationMethod === "קרן שווה" ? " selected" : "") + '>קרן שווה</option>'
        }),
        dynamicFields,
        input("כלל קנס פירעון", "tracks." + index + ".prepaymentPenaltyRule", normalizedTrack.prepaymentPenaltyRule)
      ].join("") + "</div>",
      '  <div class="mt-6 rounded-[24px] border border-brand-100 bg-brand-50 px-5 py-4 text-sm leading-7 text-slateText">הצמדה ואופי הריבית נקבעים אוטומטית לפי סוג המסלול כדי לצמצם טעויות מילוי.</div>',
      "</article>"
    ].join("");
  }

  function renderStepContent(state, step) {
    if (step === 1) {
      return formSection(
        "שלב 1: מידע בסיסי ובנק",
        "מרכזים כאן את פרטי הנכס, התשלום, הבנק וההיסטוריה של המשכנתה.",
        '<div class="space-y-8">' +
          '<div>' +
            '<h3 class="mb-4 text-lg font-semibold text-ink">קטגוריה ראשונה: פרטי הנכס</h3>' +
            '<div class="wizard-track-grid">' + [
              input("יישוב הנכס", "basic.propertySettlement", state.basic.propertySettlement, "text", {
                help: "היישוב או העיר בו נמצא הנכס. תוכל/י למצוא זאת במסמך הרכישה או בתעודת הבעלות מהבנק."
              }),
              input("שווי נכס משוער", "basic.propertyValue", state.basic.propertyValue, "number", {
                attrs: 'min="200000" step="1000"',
                help: "הערכה של שווי הנכס בשוק. אם אתה זוכר/ת את מחיר הרכישה, תוכל/י להשתמש בו. בעלייה בשוק בשנים האחרונות: בערך 5-8% בשנה."
              }),
              input("סוג הנכס", "basic.propertyType", state.basic.propertyType, "select", {
                options: '<option value="מגורים_עצמיים">מגורים עצמיים</option><option value="נכס_מושכר">נכס מושכר (להשקעה)</option>',
                help: "בחר/י את סוג הנכס. סוג הנכס משפיע על גבולות ההלוואה: מגורים עצמיים - עד 75%, נכס להשקעה - עד 50%."
              })
            ].join("") + '</div>' +
          '</div>' +
          '<div>' +
            '<h3 class="mb-4 text-lg font-semibold text-ink">קטגוריה שנייה: פרטי התשלום הנוכחי</h3>' +
            '<div class="wizard-track-grid">' + [
              input("תשלום חודשי נוכחי", "basic.currentMonthlyPayment", state.basic.currentMonthlyPayment, "number", {
                attrs: 'min="500" step="10"',
                help: "ההוצאה החודשית שלך עבור המשכנתה. תוכל/י למצוא זאת בדוח החודשי מהבנק. זה כולל קרן וריבית, לא כולל ביטוח או עמלות נוספות."
              }),
              input("בנק מלווה", "lender.lenderName", state.lender.lenderName, "select", {
                options: lenderOptions.map(function (bank) {
                  return '<option value="' + bank + '"' + (state.lender.lenderName === bank ? " selected" : "") + '>' + bank + '</option>';
                }).join(""),
                help: "בחר/י את הבנק שממנו לקחת את המשכנתה. בדוק/י בדוח החודשי או בהודעות הבנק אם אינך זוכר/ת."
              })
            ].join("") + '</div>' +
          '</div>' +
          '<div>' +
            '<h3 class="mb-4 text-lg font-semibold text-ink">קטגוריה שלישית: משך התקופה</h3>' +
            '<div class="wizard-track-grid">' + [
              input("שנים שחלפו מנטילת המשכנתה", "basic.yearsSinceOrigin", state.basic.yearsSinceOrigin, "number", {
                attrs: 'min="0" max="50" step="1"',
                help: "כמה שנים עברו מאז שלקחת את המשכנתה? זה חשוב כדי לחשב קנסי פירעון מוקדם. בנק ישראל מוריד את הקנס ב-20% אחרי 2 שנים וב-30% אחרי 5 שנים."
              }),
              input("מספר השנים הנותרות", "basic.remainingTermYears", state.basic.remainingTermYears, "number", {
                attrs: 'min="1" max="30" step="1"',
                help: "כמה שנים נותרו עד סיום תשלום המשכנתה? אם לקחת משכנתה ל-30 שנה והשלמת 5 שנים, נותרו 25 שנים. תוכל/י למצוא בדוח החודשי 'תקופת התשלום הנותרת'."
              })
            ].join("") + '</div>' +
          '</div>' +
        '</div>'
      );
    }

    if (step === 2) {
      return '<div class="space-y-6"><section class="rounded-[32px] border border-line bg-white p-8 shadow-soft"><div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between"><div><h2 class="text-3xl font-bold text-ink">שלב 2: פרטי מסלולים</h2><p class="mt-3 text-sm leading-7 text-slateText">לכל מסלול מוצגים רק השדות שרלוונטיים לסוג שבחרתם.</p></div><button type="button" class="rounded-full bg-brand-600 px-5 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700" data-add-track>הוספת מסלול</button></div><div class="mt-6">' + infoNote("הצמדה, אופי הריבית ותחנות העדכון נקבעים אוטומטית לפי סוג המסלול, כדי לצמצם טעויות מילוי.") + "</div></section>" + state.tracks.map(trackCard).join("") + "</div>";
    }

    if (step === 3) {
      return formSection(
        "שלב 3: עלויות מחזור",
        "הסכומים כאן משמשים לחישוב break-even וחיסכון נטו.",
        '<div class="wizard-track-grid mt-8">' + [
          input("עמלת פירעון מוקדם", "costs.prepaymentFee", state.costs.prepaymentFee, "number", {
            attrs: 'min="0" step="100"',
            help: "אם עמלת הפירעון עדיין לא ידועה, אפשר להשאיר 0 ונבדוק זאת בהמשך."
          }),
          input("יועץ / תפעול", "costs.advisor", state.costs.advisor, "number", {
            attrs: 'min="0" step="50"',
            help: "עמלת יועץ משכנתאות: בדרך כלל 1-1.25% מסכום ההלוואה + מע״מ. התחשב בעלויות שלך."
          })
        ].join("") + '</div><div class="mt-6">' + infoNote("הוצאות משפטיות, שמאות ורישום מחושבות אצלנו בהמשך לפי אומדן שמרני ובהתאם לרף החוקי. בפועל ייתכנו הנחות מהבנק.", "warning") + "</div>"
      );
    }

    if (step === 4) {
      return formSection("שלב 4: העדפות משק הבית", "ההמלצה מושפעת מהעדפות הסיכון, התזרים והאופק שלכם.", '<div class="wizard-track-grid mt-8">' + [
        input("אופק החזקה (שנים)", "preferences.holdingPeriodYears", state.preferences.holdingPeriodYears, "number", { attrs: 'min="1" max="30" step="1"' }),
        input("סבילות סיכון", "preferences.riskTolerance", state.preferences.riskTolerance, "select", {
          options: '<option value="low"' + (state.preferences.riskTolerance === "low" ? " selected" : "") + '>נמוכה</option><option value="balanced"' + (state.preferences.riskTolerance === "balanced" ? " selected" : "") + '>מאוזנת</option><option value="high"' + (state.preferences.riskTolerance === "high" ? " selected" : "") + '>גבוהה</option>'
        }),
        input("רגישות לתשלום חודשי", "preferences.paymentSensitivity", state.preferences.paymentSensitivity, "select", {
          options: '<option value="low"' + (state.preferences.paymentSensitivity === "low" ? " selected" : "") + '>נמוכה</option><option value="medium"' + (state.preferences.paymentSensitivity === "medium" ? " selected" : "") + '>בינונית</option><option value="high"' + (state.preferences.paymentSensitivity === "high" ? " selected" : "") + '>גבוהה</option>'
        }),
        input("מה חשוב יותר?", "preferences.goal", state.preferences.goal, "select", {
          options: '<option value="monthly_payment"' + (state.preferences.goal === "monthly_payment" ? " selected" : "") + '>תשלום חודשי נמוך יותר</option><option value="total_cost"' + (state.preferences.goal === "total_cost" ? " selected" : "") + '>עלות כוללת נמוכה יותר</option><option value="risk_reduction"' + (state.preferences.goal === "risk_reduction" ? " selected" : "") + '>צמצום סיכון</option>'
        }),
        input("רתיעה מהצמדה", "preferences.inflationAversion", state.preferences.inflationAversion, "select", {
          options: '<option value="low"' + (state.preferences.inflationAversion === "low" ? " selected" : "") + '>נמוכה</option><option value="medium"' + (state.preferences.inflationAversion === "medium" ? " selected" : "") + '>בינונית</option><option value="high"' + (state.preferences.inflationAversion === "high" ? " selected" : "") + '>גבוהה</option>'
        }),
        input("רתיעה מסיכון תחנת עדכון ריבית", "preferences.resetRiskAversion", state.preferences.resetRiskAversion, "select", {
          options: '<option value="low"' + (state.preferences.resetRiskAversion === "low" ? " selected" : "") + '>נמוכה</option><option value="medium"' + (state.preferences.resetRiskAversion === "medium" ? " selected" : "") + '>בינונית</option><option value="high"' + (state.preferences.resetRiskAversion === "high" ? " selected" : "") + '>גבוהה</option>'
        })
      ].join("") + "</div>");
    }

    if (step === 5) {
      var emailStatus = "";
      if (state.account.email) {
        if (state.account.emailCheckStatus === "checking") {
          emailStatus = '<div class="col-span-full rounded-2xl border border-line bg-surface px-4 py-3 text-xs text-slateText">בודקים זמינות אימייל...</div>';
        } else if (state.account.emailCheckStatus === "available") {
          emailStatus = '<div class="col-span-full rounded-2xl border border-success/20 bg-emerald-50 px-4 py-3 text-xs text-success">האימייל פנוי לשימוש.</div>';
        } else if (state.account.emailCheckStatus === "taken") {
          emailStatus = '<div class="col-span-full rounded-2xl border border-warning/20 bg-amber-50 px-4 py-3 text-xs text-warning">האימייל כבר בשימוש. בחרו כתובת אחרת.</div>';
        } else if (state.account.emailCheckStatus === "error") {
          emailStatus = '<div class="col-span-full rounded-2xl border border-warning/20 bg-amber-50 px-4 py-3 text-xs text-warning">לא ניתן לבדוק זמינות אימייל כרגע.</div>';
        }
      }

      return '<section class="rounded-[32px] border border-line bg-white p-8 shadow-soft"><div class="grid gap-6 lg:grid-cols-[1.1fr,0.9fr]"><div><h2 class="text-3xl font-bold text-ink">שלב 5: פרטי חשבון והרשמה</h2><p class="mt-3 text-sm leading-7 text-slateText">כאן יוצרים את החשבון שישמור את התוצאות וההתראות. אין צורך היה להירשם לפני האשף.</p><div class="wizard-track-grid mt-6">' + [
        input("שם משתמש", "account.username", state.account.username),
        input("אימייל", "account.email", state.account.email, "email", { attrs: 'autocomplete="email"' }),
        emailStatus,
        input("טלפון", "account.phone", state.account.phone, "tel", { attrs: 'autocomplete="tel"' }),
        input("סיסמה", "account.password", state.account.password, "password", { attrs: 'autocomplete="new-password"' }),
        input("אימות סיסמה", "account.confirmPassword", state.account.confirmPassword, "password", { attrs: 'autocomplete="new-password"' }),
        input("אני מאשר/ת את תנאי השימוש.", "account.terms", state.account.terms, "checkbox"),
        input("אני מאשר/ת את מדיניות הפרטיות.", "account.privacy", state.account.privacy, "checkbox")
      ].filter(Boolean).join("") + '</div></div><div class="rounded-[28px] border border-line bg-surface p-6"><h3 class="text-2xl font-bold text-ink">מידע וולונטרי</h3><p class="mt-3 text-sm leading-7 text-slateText">שדות לא חובה שיסייעו להתאמה אישית בהמשך.</p><div class="wizard-track-grid mt-6">' + [
        input("גיל", "demographics.age", state.demographics.age, "number", { attrs: 'min="18" max="120" step="1"' }),
        input("מגדר", "demographics.gender", state.demographics.gender, "select", {
          options: '<option value=""' + (!state.demographics.gender ? " selected" : "") + '>לא נבחר</option><option value="female"' + (state.demographics.gender === "female" ? " selected" : "") + '>אישה</option><option value="male"' + (state.demographics.gender === "male" ? " selected" : "") + '>גבר</option><option value="other"' + (state.demographics.gender === "other" ? " selected" : "") + '>אחר / מעדיף לא לציין</option>'
        }),
        input("מצב משפחתי", "demographics.maritalStatus", state.demographics.maritalStatus, "select", {
          options: '<option value=""' + (!state.demographics.maritalStatus ? " selected" : "") + '>לא נבחר</option><option value="single"' + (state.demographics.maritalStatus === "single" ? " selected" : "") + '>רווק/ה</option><option value="married"' + (state.demographics.maritalStatus === "married" ? " selected" : "") + '>נשוי/אה</option><option value="divorced"' + (state.demographics.maritalStatus === "divorced" ? " selected" : "") + '>גרוש/ה</option><option value="widowed"' + (state.demographics.maritalStatus === "widowed" ? " selected" : "") + '>אלמן/ה</option>'
        }),
        input("עיסוק", "demographics.occupation", state.demographics.occupation)
      ].join("") + "</div></div></div></section>";
    }

    return '<div class="space-y-6"><section class="rounded-[32px] border border-line bg-white p-8 shadow-soft"><h2 class="text-3xl font-bold text-ink">שלב 6: סקירה ושליחה</h2><p class="mt-3 text-sm leading-7 text-slateText">בודקים את הנתונים, מאשרים שהסימולציה הוזנה כראוי, ואז יוצרים את החשבון ושומרים את התוצאות.</p><div class="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">' + [
      App.UI.metricCard({ label: "בנק / מלווה", value: App.Helpers.escapeHtml(state.lender.lenderName), note: state.basic.propertySettlement }),
      App.UI.metricCard({ label: "מסלולים", value: String(state.tracks.length), note: "מסלולים פעילים" }),
      App.UI.metricCard({ label: "יתרה כוללת", value: App.Format.currency(moneySummary(state).totalBalance), note: "סך כל המסלולים" }),
      App.UI.metricCard({ label: "עלויות מחזור", value: App.Format.currency(moneySummary(state).totalFees), note: "כולל אומדן שמרני להוצאות נלוות" })
    ].join("") + '</div></section>' +
      App.UI.table({
        columns: [
          { label: "מסלול", key: "label" },
          { label: "סוג", render: function (row) { return trackTypeLabels[row.type]; } },
          { label: "יתרה", render: function (row) { return App.Format.currency(row.outstandingBalance); } },
          { label: "ריבית", render: function (row) { return App.Format.percent(row.currentRate); } }
        ],
        rows: state.tracks
      }) +
      '<section class="rounded-[32px] border border-line bg-white p-8 shadow-soft"><div class="grid gap-6 lg:grid-cols-2"><div><h3 class="text-2xl font-bold text-ink">פרטי החשבון</h3><div class="mt-4 space-y-3 text-sm text-slateText"><div class="rounded-2xl bg-surface px-4 py-3"><span class="block font-semibold text-ink">שם משתמש</span>' + App.Helpers.escapeHtml(state.account.username) + '</div><div class="rounded-2xl bg-surface px-4 py-3"><span class="block font-semibold text-ink">אימייל</span>' + App.Helpers.escapeHtml(state.account.email) + '</div><div class="rounded-2xl bg-surface px-4 py-3"><span class="block font-semibold text-ink">טלפון</span>' + App.Helpers.escapeHtml(state.account.phone || "לא הוזן") + '</div></div></div><div><h3 class="text-2xl font-bold text-ink">מידע וולונטרי</h3><div class="mt-4 space-y-3 text-sm text-slateText"><div class="rounded-2xl bg-surface px-4 py-3"><span class="block font-semibold text-ink">גיל</span>' + App.Helpers.escapeHtml(state.demographics.age || "לא הוזן") + '</div><div class="rounded-2xl bg-surface px-4 py-3"><span class="block font-semibold text-ink">עיסוק</span>' + App.Helpers.escapeHtml(state.demographics.occupation || "לא הוזן") + '</div></div></div></div><div class="mt-6">' + input("אני מאשר/ת שהפרטים נועדו לסימולציה בלבד וייתכן שאדרש לעדכן מסמכים בהמשך.", "review.confirm", state.review.confirm, "checkbox") + "</div></section></div>";
  }

  function validateStep(state, step) {
    var errors = [];

    if (step === 1) {
      if (!state.basic.propertySettlement || state.basic.propertySettlement.trim().length < 2) {
        errors.push("יש להזין יישוב נכס בן לפחות 2 תווים.");
      }
      if (Number(state.basic.propertyValue) < 200000 || Number(state.basic.propertyValue) > 50000000) {
        errors.push("שווי הנכס חייב להיות בין ₪200,000 ל-₪50,000,000.");
      }
      if (Number(state.basic.currentMonthlyPayment) < 500 || Number(state.basic.currentMonthlyPayment) > 200000) {
        errors.push("התשלום החודשי חייב להיות בין ₪500 ל-₪200,000.");
      }
      if (!state.lender.lenderName) {
        errors.push("יש להשלים שם בנק או מלווה.");
      }
      if (!state.basic.propertyType) {
        errors.push("יש לבחור סוג נכס.");
      }
      if (Number(state.basic.yearsSinceOrigin) < 0 || Number(state.basic.yearsSinceOrigin) > 50) {
        errors.push("שנים שחלפו חייבות להיות בין 0 ל-50.");
      }
      if (Number(state.basic.remainingTermYears) < 1 || Number(state.basic.remainingTermYears) > 30) {
        errors.push("שנים נותרות חייבות להיות בין 1 ל-30.");
      }

      // Cross validation
      var totalYears = Number(state.basic.yearsSinceOrigin) + Number(state.basic.remainingTermYears);
      if (totalYears > 55) {
        errors.push("סך התקופה (שנים שחלפו + שנים נותרות) עולה על 55 שנים. בדוק/י את הנתונים.");
      }

      // LTV check
      var outstandingBalance = state.tracks.reduce(function (sum, track) {
        return sum + Number(track.outstandingBalance || 0);
      }, 0);
      var ltv = (outstandingBalance / Number(state.basic.propertyValue)) * 100;
      var ltvMax = state.basic.propertyType === "נכס_מושכר" ? 50 : 75;
      if (ltv > ltvMax) {
        errors.push("יחס הלוואה (LTV) חורג מהמקסימום המותר (" + ltvMax + "%). בדוק/י את הנתונים.");
      }
    }

    if (step === 2) {
      state.tracks.forEach(function (track, index) {
        var normalizedTrack = normalizeTrack(track);
        if (!normalizedTrack.label || !normalizedTrack.type) {
          errors.push("מסלול " + (index + 1) + " חייב לכלול שם וסוג.");
        }
        if (Number(normalizedTrack.outstandingBalance) <= 0 || Number(normalizedTrack.remainingTermMonths) <= 0) {
          errors.push("מסלול " + (index + 1) + " חייב לכלול יתרה וחודשים חיוביים.");
        }
        if (Number(normalizedTrack.currentRate) <= 0) {
          errors.push("מסלול " + (index + 1) + " חייב לכלול ריבית תקינה.");
        }
        if ((normalizedTrack.type === "adjustable_non_linked" || normalizedTrack.type === "adjustable_linked") && (!normalizedTrack.resetInterval || !normalizedTrack.nextResetDate)) {
          errors.push("למסלול משתנה יש להשלים תדירות תחנת עדכון ריבית ותאריך תחנה הבא.");
        }
      });
    }

    if (step === 3 && (Number(state.costs.prepaymentFee) < 0 || Number(state.costs.advisor) < 0)) {
      errors.push("עלויות אינן יכולות להיות שליליות.");
    }

    if (step === 4 && (!state.preferences.goal || !state.preferences.riskTolerance)) {
      errors.push("יש להשלים העדפות מרכזיות.");
    }

    if (step === 5) {
      var session = App.State.load().session || {};
      if (!state.account.username) {
        errors.push("יש להזין שם משתמש.");
      }
      if (!emailValid(state.account.email)) {
        errors.push("יש להזין כתובת אימייל תקינה.");
      }
      if (state.account.emailCheckStatus === "taken" && session.email !== state.account.email) {
        errors.push("האימייל כבר בשימוש. בחרו כתובת אחרת.");
      }
      if (!phoneValid(state.account.phone)) {
        errors.push("יש להזין מספר טלפון תקין.");
      }
      if (!passwordStrong(state.account.password)) {
        errors.push("הסיסמה חייבת להכיל לפחות 8 תווים.");
      }
      if (state.account.password !== state.account.confirmPassword) {
        errors.push("אימות הסיסמה אינו תואם.");
      }
      if (!state.account.terms || !state.account.privacy) {
        errors.push("יש לאשר את תנאי השימוש ואת מדיניות הפרטיות.");
      }
      if (state.demographics.age && Number(state.demographics.age) < 18) {
        errors.push("אם הוזן גיל, עליו להיות 18 ומעלה.");
      }
    }

    if (step === 6 && !state.review.confirm) {
      errors.push("יש לאשר שהמידע נועד לסימולציה בלבד לפני שליחה.");
    }

    return errors;
  }

  App.Pages.onboarding = function (root) {
    var wizardState = defaultWizardState();
    var currentStep = 1;
    var submitInProgress = false;
    var emailCheckTimer;

    function persistDraft() {
      App.State.save({ onboarding: wizardState });
    }

    function syncInputs() {
      $(root).find("[data-bind]").each(function () {
        var $field = $(this);
        var value = $field.attr("type") === "checkbox"
          ? $field.is(":checked")
          : $field.attr("type") === "number"
            ? ($field.val() === "" ? "" : Number($field.val()))
            : $field.val();
        setByPath(wizardState, $field.data("bind"), value);
      });

      normalizeTracksCollection(wizardState);
      persistDraft();
    }

    function scheduleEmailCheck(email) {
      var session = App.State.load().session || {};
      if (!email || !emailValid(email)) {
        wizardState.account.emailCheckStatus = "";
        wizardState.account.emailAvailable = null;
        return;
      }

      if (session.email && session.email === email) {
        wizardState.account.emailCheckStatus = "available";
        wizardState.account.emailAvailable = true;
        return;
      }

      wizardState.account.emailCheckStatus = "checking";
      wizardState.account.emailAvailable = null;

      if (emailCheckTimer) {
        window.clearTimeout(emailCheckTimer);
      }
      emailCheckTimer = window.setTimeout(function () {
        App.MockApi.checkEmailAvailability(email).then(function (response) {
          wizardState.account.emailAvailable = !!response.available;
          wizardState.account.emailCheckStatus = response.available ? "available" : "taken";
          persistDraft();
          render();
        }).catch(function () {
          wizardState.account.emailCheckStatus = "error";
          persistDraft();
          render();
        });
      }, 450);
    }

    function scrollWizardTop() {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function render(errors, successMessage) {
      var steps = stepDefinitions();
      var isFinalStep = currentStep === steps.length;

      root.innerHTML = [
        progressBar(currentStep),
        successMessage ? '<div class="rounded-[24px] border border-success/20 bg-emerald-50 px-5 py-4 text-sm text-success">' + successMessage + "</div>" : "",
        errors && errors.length ? '<div class="mt-4 rounded-[24px] border border-danger/20 bg-red-50 px-5 py-4 text-sm text-danger">' + errors.join("<br />") + "</div>" : "",
        '<section class="space-y-6">',
        renderStepContent(wizardState, currentStep),
        '<section class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div class="text-sm text-slateText">שלב ' + currentStep + " מתוך " + steps.length + '</div><div class="wizard-actions">' + (currentStep > 1 ? '<button type="button" class="rounded-full border border-line px-5 py-3 text-sm font-semibold text-ink hover:border-brand-600 hover:text-brand-600" data-wizard-prev>חזרה</button>' : "") + (isFinalStep ? '<button type="button" class="rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700" data-wizard-submit' + (submitInProgress ? ' disabled="disabled"' : "") + '>יצירת חשבון ושמירת תוצאות</button>' : '<button type="button" class="rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700" data-wizard-next>לשלב הבא</button>') + "</div></section>",
        "</section>"
      ].join("");

      // Attach help bubble handlers
      $(root).find("[data-help-bubble]").each(function () {
        var $btn = $(this);
        var tooltipText = $btn.data("help-bubble");
        $btn.on("click", function (e) {
          e.preventDefault();
          alert(tooltipText);
        });
      });
    }

    render();
    if (wizardState.account.email) {
      scheduleEmailCheck(wizardState.account.email);
    }

    $(root).on("change input", "[data-bind]", function () {
      syncInputs();
      if ($(this).data("bind") === "account.email") {
        scheduleEmailCheck($(this).val());
      }
      if ($(this).data("bind").indexOf("tracks.") === 0 && /\.type$/.test($(this).data("bind"))) {
        render();
      }
    });

    $(root).on("click", "[data-add-track]", function () {
      syncInputs();
      if (wizardState.tracks.length < 6) {
        wizardState.tracks.push(createTrack(wizardState.tracks.length));
        normalizeTracksCollection(wizardState);
        persistDraft();
        render();
      }
    });

    $(root).on("click", "[data-remove-track]", function () {
      syncInputs();
      if (wizardState.tracks.length > 1) {
        wizardState.tracks.splice(Number($(this).data("remove-track")), 1);
        normalizeTracksCollection(wizardState);
        persistDraft();
        render();
      }
    });

    $(root).on("click", "[data-wizard-prev]", function () {
      syncInputs();
      currentStep = Math.max(1, currentStep - 1);
      render();
      scrollWizardTop();
    });

    $(root).on("click", "[data-wizard-next]", function () {
      syncInputs();
      var errors = validateStep(wizardState, currentStep);
      if (errors.length) {
        render(errors);
        scrollWizardTop();
        return;
      }

      currentStep = Math.min(stepDefinitions().length, currentStep + 1);
      render();
      scrollWizardTop();
    });

    $(root).on("click", "[data-wizard-submit]", function () {
      syncInputs();
      var errors = validateStep(wizardState, currentStep);
      if (errors.length) {
        render(errors);
        scrollWizardTop();
        return;
      }

      submitInProgress = true;
      render([], "שומרים את התיק, יוצרים את החשבון ומכינים את סביבת העבודה האישית.");
      App.MockApi.submitOnboarding(wizardState).then(function (response) {
        submitInProgress = false;
        if (response.status === "email_taken") {
          wizardState.account.emailCheckStatus = "taken";
          render(["האימייל כבר בשימוש. בחרו כתובת אחרת."]);
          scrollWizardTop();
          return;
        }
        if (response.status !== "success") {
          render(["לא ניתן להשלים את השליחה כרגע. נסו שוב."]);
          scrollWizardTop();
          return;
        }
        App.State.save({ onboarding: null });
        render([], "הנתונים נשמרו בהצלחה והחשבון נוצר. מעבירים אותך ללוח המחוונים.");
        window.setTimeout(function () {
          window.location.href = response.redirect;
        }, 700);
      });
    });
  };
})();