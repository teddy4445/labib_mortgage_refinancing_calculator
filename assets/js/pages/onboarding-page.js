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

  function trackTypeOptions(selected) {
    return Object.keys(trackTypeLabels).map(function (key) {
      return '<option value="' + key + '"' + (key === selected ? " selected" : "") + ">" + trackTypeLabels[key] + "</option>";
    }).join("");
  }

  function createTrack(index, seed) {
    return $.extend(true, {
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
    }, seed || {});
  }

  function defaultWizardState() {
    var mortgage = window.MockData.mortgage;
    var stored = App.State.load();
    var existing = stored.onboarding;
    var profile = stored.profile || {};
    var session = stored.session || {};
    var baseState = {
      basic: {
        propertyCity: "תל אביב",
        propertyValue: mortgage.propertyValue,
        currentMonthlyPayment: mortgage.currentMonthlyPayment,
        remainingTermMonths: mortgage.remainingTermMonths,
        loanPurpose: "דירת מגורים",
        occupancyStatus: "מגורים עצמיים"
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
      tracks: mortgage.tracks.map(function (track, index) { return createTrack(index, track); }),
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
        privacy: false
      },
      demographics: {
        age: "",
        gender: "",
        maritalStatus: "",
        occupation: ""
      },
      review: { confirm: false }
    };

    return existing ? $.extend(true, {}, baseState, App.Helpers.deepClone(existing)) : baseState;
  }

  function stepDefinitions() {
    return [
      "מידע בסיסי",
      "בנק ומקור",
      "מבנה מסלולים",
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
    return /^[0-9+\\-\\s()]{9,}$/.test(String(value || ""));
  }

  function input(label, bind, value, type, options) {
    var config = options || {};
    var fieldType = type || "text";
    var attrs = config.attrs || "";
    var hint = config.hint ? '<p class="mt-2 text-xs text-slateText">' + config.hint + "</p>" : "";
    var element = "";

    if (fieldType === "select") {
      element = '<select data-bind="' + bind + '" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm">' + config.options + "</select>";
    } else if (fieldType === "checkbox") {
      return '<div class="col-span-full"><label class="flex items-start gap-3 rounded-2xl border border-line p-4 text-sm text-slateText"><input type="checkbox" data-bind="' + bind + '" class="mt-1 h-4 w-4 rounded border-line text-brand-600 focus:ring-brand-600" ' + (value ? "checked" : "") + ' /><span>' + label + "</span></label></div>";
    } else {
      element = '<input data-bind="' + bind + '" type="' + fieldType + '" value="' + App.Helpers.escapeHtml(value) + '" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm" ' + attrs + " />";
    }

    return '<label class="block"><span class="mb-2 block text-sm font-semibold text-ink">' + label + "</span>" + element + hint + "</label>";
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
    var isVariable = track.type === "prime_floating" || track.type.indexOf("adjustable") === 0;

    return [
      '<article class="rounded-[28px] border border-line bg-white p-6 shadow-soft">',
      '  <div class="flex items-center justify-between gap-4"><div><p class="text-sm font-bold text-slateText">מסלול ' + (index + 1) + '</p><h3 class="mt-1 text-xl font-bold text-ink">' + App.Helpers.escapeHtml(track.label) + '</h3></div><button type="button" class="rounded-full border border-line px-4 py-2 text-xs font-semibold text-slateText hover:border-danger hover:text-danger" data-remove-track="' + index + '"' + (index === 0 ? ' disabled="disabled"' : "") + '>הסר מסלול</button></div>',
      '<div class="wizard-track-grid mt-6">',
      input("שם מסלול", "tracks." + index + ".label", track.label),
      input("סוג מסלול", "tracks." + index + ".type", track.type, "select", { options: trackTypeOptions(track.type) }),
      input("יתרה נוכחית", "tracks." + index + ".outstandingBalance", track.outstandingBalance, "number", { attrs: 'min="0" step="1000"' }),
      input("ריבית נוכחית", "tracks." + index + ".currentRate", track.currentRate, "number", { attrs: 'min="0" step="0.01"' }),
      input("ריבית מקורית", "tracks." + index + ".originalRate", track.originalRate, "number", { attrs: 'min="0" step="0.01"' }),
      input("יתרת חודשים", "tracks." + index + ".remainingTermMonths", track.remainingTermMonths, "number", { attrs: 'min="1" step="1"' }),
      input("סוג הצמדה", "tracks." + index + ".linkageType", track.linkageType, "select", { options: '<option value="לא צמוד"' + (track.linkageType === "לא צמוד" ? " selected" : "") + '>לא צמוד</option><option value="צמוד מדד"' + (track.linkageType === "צמוד מדד" ? " selected" : "") + '>צמוד מדד</option><option value="צמוד מטח"' + (track.linkageType === "צמוד מטח" ? " selected" : "") + '>צמוד מטח</option>' }),
      input("סוג ריבית", "tracks." + index + ".rateType", track.rateType, "select", { options: '<option value="קבועה"' + (track.rateType === "קבועה" ? " selected" : "") + '>קבועה</option><option value="משתנה"' + (track.rateType === "משתנה" ? " selected" : "") + '>משתנה</option>' }),
      input("מרווח / איפוס", "tracks." + index + ".resetInterval", track.resetInterval, "text", { attrs: isVariable ? "" : 'disabled="disabled"', hint: isVariable ? "למשל 60 חודשים." : "רלוונטי למסלולים משתנים בלבד." }),
      input("תאריך איפוס הבא", "tracks." + index + ".nextResetDate", track.nextResetDate, "date", { attrs: isVariable ? "" : 'disabled="disabled"' }),
      input("שיטת סילוקין", "tracks." + index + ".amortizationMethod", track.amortizationMethod, "select", { options: '<option value="שפיצר"' + (track.amortizationMethod === "שפיצר" ? " selected" : "") + '>שפיצר</option><option value="קרן שווה"' + (track.amortizationMethod === "קרן שווה" ? " selected" : "") + '>קרן שווה</option>' }),
      input("כלל קנס פירעון", "tracks." + index + ".prepaymentPenaltyRule", track.prepaymentPenaltyRule),
      "</div></article>"
    ].join("");
  }

  function formSection(title, desc, body) {
    return '<section class="rounded-[32px] border border-line bg-white p-8 shadow-soft"><h2 class="text-3xl font-bold text-ink">' + title + '</h2><p class="mt-3 text-sm leading-7 text-slateText">' + desc + "</p>" + body + "</section>";
  }

  function renderStepContent(state, step) {
    if (step === 1) {
      return formSection("שלב 1: מידע בסיסי", "נאסוף תמונת מצב כללית של הנכס, התשלום והיתרה.", '<div class="wizard-track-grid mt-8">' + [
        input("עיר הנכס", "basic.propertyCity", state.basic.propertyCity),
        input("שווי נכס משוער", "basic.propertyValue", state.basic.propertyValue, "number", { attrs: 'min="0" step="1000"' }),
        input("תשלום חודשי נוכחי", "basic.currentMonthlyPayment", state.basic.currentMonthlyPayment, "number", { attrs: 'min="0" step="10"' }),
        input("יתרת חודשים כוללת", "basic.remainingTermMonths", state.basic.remainingTermMonths, "number", { attrs: 'min="1" step="1"' }),
        input("מטרת ההלוואה", "basic.loanPurpose", state.basic.loanPurpose, "select", { options: '<option value="דירת מגורים"' + (state.basic.loanPurpose === "דירת מגורים" ? " selected" : "") + '>דירת מגורים</option><option value="שדרוג נכס"' + (state.basic.loanPurpose === "שדרוג נכס" ? " selected" : "") + '>שדרוג נכס</option><option value="השקעה"' + (state.basic.loanPurpose === "השקעה" ? " selected" : "") + '>השקעה</option>' }),
        input("סטטוס מגורים", "basic.occupancyStatus", state.basic.occupancyStatus, "select", { options: '<option value="מגורים עצמיים"' + (state.basic.occupancyStatus === "מגורים עצמיים" ? " selected" : "") + '>מגורים עצמיים</option><option value="נכס מושכר"' + (state.basic.occupancyStatus === "נכס מושכר" ? " selected" : "") + '>נכס מושכר</option>' })
      ].join("") + "</div>");
    }

    if (step === 2) {
      return formSection("שלב 2: פרטי הבנק והמקור", "נתונים אלה משפיעים על עמלות, תחנות יציאה והשלמות בהמשך.", '<div class="wizard-track-grid mt-8">' + [
        input("בנק / מלווה", "lender.lenderName", state.lender.lenderName),
        input("תאריך נטילה", "lender.originationDate", state.lender.originationDate, "date"),
        input("סכום מקורי", "lender.originalAmount", state.lender.originalAmount, "number", { attrs: 'min="0" step="1000"' }),
        input("תקופה מקורית בחודשים", "lender.originalTermMonths", state.lender.originalTermMonths, "number", { attrs: 'min="1" step="1"' }),
        input("סניף / ערוץ", "lender.branch", state.lender.branch),
        input("איש קשר / צוות", "lender.accountManager", state.lender.accountManager)
      ].join("") + "</div>");
    }

    if (step === 3) {
      return formSection("שלב 3: מבנה המסלולים", "אפשר לעדכן את מספר המסלולים לפני מילוי הפירוט המלא.", '<div class="mt-8 grid gap-6 lg:grid-cols-[240px,1fr]"><div class="rounded-[28px] border border-line bg-surface p-6">' + input("מספר מסלולים", "tracksMeta.trackCount", state.tracksMeta.trackCount, "number", { attrs: 'min="1" max="6" step="1"' }) + '<button type="button" class="mt-4 w-full rounded-full border border-line px-4 py-3 text-sm font-semibold text-ink hover:border-brand-600 hover:text-brand-600" data-apply-track-count>עדכון מספר המסלולים</button></div><div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"><article class="rounded-[24px] border border-line bg-white p-4 text-sm leading-7 text-slateText">קבועה לא צמודה: יציבות גבוהה.</article><article class="rounded-[24px] border border-line bg-white p-4 text-sm leading-7 text-slateText">פריים / משתנה: גמישות לצד רגישות לריבית.</article><article class="rounded-[24px] border border-line bg-white p-4 text-sm leading-7 text-slateText">מחזור חלקי: מחליפים רק את המסלולים המכבידים.</article></div></div>');
    }

    if (step === 4) {
      return '<div class="space-y-6"><div class="rounded-[32px] border border-line bg-white p-8 shadow-soft"><div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between"><div><h2 class="text-3xl font-bold text-ink">שלב 4: פירוט מסלולים</h2><p class="mt-3 text-sm leading-7 text-slateText">לכל מסלול מזינים יתרה, ריבית, תקופה, הצמדה, סילוקין ותחנות איפוס.</p></div><button type="button" class="rounded-full bg-brand-600 px-5 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700" data-add-track>הוספת מסלול</button></div></div>' + state.tracks.map(trackCard).join("") + "</div>";
    }

    if (step === 5) {
      return formSection("שלב 5: עלויות מחזור", "הסכומים כאן משמשים לחישוב break-even וחיסכון נטו.", '<div class="wizard-track-grid mt-8">' + [
        input("עמלת פירעון מוקדם", "costs.prepaymentFee", state.costs.prepaymentFee, "number", { attrs: 'min="0" step="100"' }),
        input("שכר טרחה משפטי", "costs.legalFee", state.costs.legalFee, "number", { attrs: 'min="0" step="50"' }),
        input("שמאות", "costs.appraisal", state.costs.appraisal, "number", { attrs: 'min="0" step="50"' }),
        input("רישום / טאבו", "costs.registration", state.costs.registration, "number", { attrs: 'min="0" step="50"' }),
        input("יועץ / תפעול", "costs.advisor", state.costs.advisor, "number", { attrs: 'min="0" step="50"' })
      ].join("") + "</div>");
    }

    if (step === 6) {
      return formSection("שלב 6: העדפות משק הבית", "ההמלצה מושפעת מהעדפות הסיכון, התזרים והאופק שלכם.", '<div class="wizard-track-grid mt-8">' + [
        input("אופק החזקה (שנים)", "preferences.holdingPeriodYears", state.preferences.holdingPeriodYears, "number", { attrs: 'min="1" max="30" step="1"' }),
        input("סבילות סיכון", "preferences.riskTolerance", state.preferences.riskTolerance, "select", { options: '<option value="low"' + (state.preferences.riskTolerance === "low" ? " selected" : "") + '>נמוכה</option><option value="balanced"' + (state.preferences.riskTolerance === "balanced" ? " selected" : "") + '>מאוזנת</option><option value="high"' + (state.preferences.riskTolerance === "high" ? " selected" : "") + '>גבוהה</option>' }),
        input("רגישות לתשלום חודשי", "preferences.paymentSensitivity", state.preferences.paymentSensitivity, "select", { options: '<option value="low"' + (state.preferences.paymentSensitivity === "low" ? " selected" : "") + '>נמוכה</option><option value="medium"' + (state.preferences.paymentSensitivity === "medium" ? " selected" : "") + '>בינונית</option><option value="high"' + (state.preferences.paymentSensitivity === "high" ? " selected" : "") + '>גבוהה</option>' }),
        input("מה חשוב יותר?", "preferences.goal", state.preferences.goal, "select", { options: '<option value="monthly_payment"' + (state.preferences.goal === "monthly_payment" ? " selected" : "") + '>תשלום חודשי נמוך יותר</option><option value="total_cost"' + (state.preferences.goal === "total_cost" ? " selected" : "") + '>עלות כוללת נמוכה יותר</option><option value="risk_reduction"' + (state.preferences.goal === "risk_reduction" ? " selected" : "") + '>צמצום סיכון</option>' }),
        input("רתיעה מהצמדה", "preferences.inflationAversion", state.preferences.inflationAversion, "select", { options: '<option value="low"' + (state.preferences.inflationAversion === "low" ? " selected" : "") + '>נמוכה</option><option value="medium"' + (state.preferences.inflationAversion === "medium" ? " selected" : "") + '>בינונית</option><option value="high"' + (state.preferences.inflationAversion === "high" ? " selected" : "") + '>גבוהה</option>' }),
        input("רתיעה מסיכון איפוס", "preferences.resetRiskAversion", state.preferences.resetRiskAversion, "select", { options: '<option value="low"' + (state.preferences.resetRiskAversion === "low" ? " selected" : "") + '>נמוכה</option><option value="medium"' + (state.preferences.resetRiskAversion === "medium" ? " selected" : "") + '>בינונית</option><option value="high"' + (state.preferences.resetRiskAversion === "high" ? " selected" : "") + '>גבוהה</option>' })
      ].join("") + "</div>");
    }

    if (step === 7) {
      return '<section class="rounded-[32px] border border-line bg-white p-8 shadow-soft"><div class="grid gap-6 lg:grid-cols-[1.1fr,0.9fr]"><div><h2 class="text-3xl font-bold text-ink">שלב 7: פרטי חשבון והרשמה</h2><p class="mt-3 text-sm leading-7 text-slateText">כאן יוצרים את החשבון שישמור את התוצאות וההתראות. אין צורך היה להירשם לפני האשף.</p><div class="wizard-track-grid mt-6">' + [
        input("שם משתמש", "account.username", state.account.username),
        input("אימייל", "account.email", state.account.email, "email", { attrs: 'autocomplete="email"' }),
        input("טלפון", "account.phone", state.account.phone, "tel", { attrs: 'autocomplete="tel"' }),
        input("סיסמה", "account.password", state.account.password, "password", { attrs: 'autocomplete="new-password"' }),
        input("אימות סיסמה", "account.confirmPassword", state.account.confirmPassword, "password", { attrs: 'autocomplete="new-password"' }),
        input("אני מאשר/ת את תנאי השימוש.", "account.terms", state.account.terms, "checkbox"),
        input("אני מאשר/ת את מדיניות הפרטיות.", "account.privacy", state.account.privacy, "checkbox")
      ].join("") + '</div></div><div class="rounded-[28px] border border-line bg-surface p-6"><h3 class="text-2xl font-bold text-ink">מידע וולונטרי</h3><p class="mt-3 text-sm leading-7 text-slateText">שדות לא חובה שיסייעו להתאמה אישית בהמשך.</p><div class="wizard-track-grid mt-6">' + [
        input("גיל", "demographics.age", state.demographics.age, "number", { attrs: 'min="18" max="120" step="1"' }),
        input("מגדר", "demographics.gender", state.demographics.gender, "select", { options: '<option value=""' + (!state.demographics.gender ? " selected" : "") + '>לא נבחר</option><option value="female"' + (state.demographics.gender === "female" ? " selected" : "") + '>אישה</option><option value="male"' + (state.demographics.gender === "male" ? " selected" : "") + '>גבר</option><option value="other"' + (state.demographics.gender === "other" ? " selected" : "") + '>אחר / מעדיף לא לציין</option>' }),
        input("מצב משפחתי", "demographics.maritalStatus", state.demographics.maritalStatus, "select", { options: '<option value=""' + (!state.demographics.maritalStatus ? " selected" : "") + '>לא נבחר</option><option value="single"' + (state.demographics.maritalStatus === "single" ? " selected" : "") + '>רווק/ה</option><option value="married"' + (state.demographics.maritalStatus === "married" ? " selected" : "") + '>נשוי/אה</option><option value="divorced"' + (state.demographics.maritalStatus === "divorced" ? " selected" : "") + '>גרוש/ה</option><option value="widowed"' + (state.demographics.maritalStatus === "widowed" ? " selected" : "") + '>אלמן/ה</option>' }),
        input("עיסוק", "demographics.occupation", state.demographics.occupation)
      ].join("") + "</div></div></div></section>";
    }

    return '<div class="space-y-6"><section class="rounded-[32px] border border-line bg-white p-8 shadow-soft"><h2 class="text-3xl font-bold text-ink">שלב 8: סקירה ושליחה</h2><p class="mt-3 text-sm leading-7 text-slateText">בודקים את הנתונים, מאשרים שהסימולציה הוזנה כראוי, ואז יוצרים את החשבון ושומרים את התוצאות.</p><div class="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">' + [
      App.UI.metricCard({ label: "עיר הנכס", value: App.Helpers.escapeHtml(state.basic.propertyCity), note: state.basic.loanPurpose }),
      App.UI.metricCard({ label: "מסלולים", value: String(state.tracks.length), note: "מסלולים פעילים" }),
      App.UI.metricCard({ label: "יתרה כוללת", value: App.Format.currency(moneySummary(state).totalBalance), note: "סך כל המסלולים" }),
      App.UI.metricCard({ label: "עלויות מחזור", value: App.Format.currency(moneySummary(state).totalFees), note: "כולל הוצאות נלוות" })
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
      if (!state.basic.propertyCity) {
        errors.push("יש להזין עיר נכס.");
      }
      if (Number(state.basic.propertyValue) <= 0 || Number(state.basic.currentMonthlyPayment) <= 0) {
        errors.push("יש להזין שווי נכס ותשלום חודשי חיוביים.");
      }
    }

    if (step === 2) {
      if (!state.lender.lenderName || !state.lender.originationDate) {
        errors.push("יש להשלים שם בנק ותאריך נטילה.");
      }
      if (Number(state.lender.originalAmount) <= 0) {
        errors.push("יש להזין סכום מקורי תקין.");
      }
    }

    if (step === 3 && (Number(state.tracksMeta.trackCount) < 1 || Number(state.tracksMeta.trackCount) > 6)) {
      errors.push("מספר המסלולים צריך להיות בין 1 ל-6.");
    }

    if (step === 4) {
      state.tracks.forEach(function (track, index) {
        if (!track.label || !track.type) {
          errors.push("מסלול " + (index + 1) + " חייב לכלול שם וסוג.");
        }
        if (Number(track.outstandingBalance) <= 0 || Number(track.remainingTermMonths) <= 0) {
          errors.push("מסלול " + (index + 1) + " חייב לכלול יתרה וחודשים חיוביים.");
        }
        if ((track.type === "prime_floating" || track.type.indexOf("adjustable") === 0) && (!track.resetInterval || !track.nextResetDate)) {
          errors.push("למסלול משתנה יש להשלים מרווח איפוס ותאריך איפוס.");
        }
      });
    }

    if (step === 5 && (Number(state.costs.prepaymentFee) < 0 || Number(state.costs.legalFee) < 0)) {
      errors.push("עלויות אינן יכולות להיות שליליות.");
    }

    if (step === 6 && (!state.preferences.goal || !state.preferences.riskTolerance)) {
      errors.push("יש להשלים העדפות מרכזיות.");
    }

    if (step === 7) {
      if (!state.account.username) {
        errors.push("יש להזין שם משתמש.");
      }
      if (!emailValid(state.account.email)) {
        errors.push("יש להזין כתובת אימייל תקינה.");
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

    if (step === 8 && !state.review.confirm) {
      errors.push("יש לאשר שהמידע נועד לסימולציה בלבד לפני שליחה.");
    }

    return errors;
  }

  App.Pages.onboarding = function (root) {
    var wizardState = defaultWizardState();
    var currentStep = 1;
    var submitInProgress = false;

    function persistDraft() {
      App.State.save({ onboarding: wizardState });
    }

    function syncInputs() {
      $(root).find("[data-bind]").each(function () {
        var $field = $(this);
        var value = $field.attr("type") === "checkbox" ? $field.is(":checked") : $field.attr("type") === "number" ? ($field.val() === "" ? "" : Number($field.val())) : $field.val();
        setByPath(wizardState, $field.data("bind"), value);
      });
      persistDraft();
    }

    function resizeTracks() {
      var count = Math.max(1, Math.min(6, Number(wizardState.tracksMeta.trackCount || 0)));
      wizardState.tracksMeta.trackCount = count;

      while (wizardState.tracks.length < count) {
        wizardState.tracks.push(createTrack(wizardState.tracks.length));
      }

      while (wizardState.tracks.length > count) {
        wizardState.tracks.pop();
      }

      persistDraft();
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
    }

    render();

    $(root).on("change input", "[data-bind]", function () {
      syncInputs();
      if ($(this).data("bind").indexOf("tracks.") === 0 && /\.type$/.test($(this).data("bind"))) {
        render();
      }
    });

    $(root).on("click", "[data-apply-track-count]", function () {
      syncInputs();
      resizeTracks();
      render();
    });

    $(root).on("click", "[data-add-track]", function () {
      syncInputs();
      if (wizardState.tracks.length < 6) {
        wizardState.tracks.push(createTrack(wizardState.tracks.length));
        wizardState.tracksMeta.trackCount = wizardState.tracks.length;
        persistDraft();
        render();
      }
    });

    $(root).on("click", "[data-remove-track]", function () {
      syncInputs();
      if (wizardState.tracks.length > 1) {
        wizardState.tracks.splice(Number($(this).data("remove-track")), 1);
        wizardState.tracksMeta.trackCount = wizardState.tracks.length;
        persistDraft();
        render();
      }
    });

    $(root).on("click", "[data-wizard-prev]", function () {
      syncInputs();
      currentStep = Math.max(1, currentStep - 1);
      render();
    });

    $(root).on("click", "[data-wizard-next]", function () {
      syncInputs();
      resizeTracks();
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
      resizeTracks();
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
        App.State.save({ onboarding: null });
        render([], "הנתונים נשמרו בהצלחה והחשבון נוצר. מעבירים אותך ללוח המחוונים.");
        window.setTimeout(function () {
          window.location.href = response.redirect;
        }, 700);
      });
    });
  };
})();
