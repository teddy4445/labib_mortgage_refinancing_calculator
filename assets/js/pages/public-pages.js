(function () {
  window.App = window.App || {};
  App.Pages = App.Pages || {};

  function icon(name) {
    var icons = {
      compare: '<svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 7h14M5 12h9M5 17h14" stroke-linecap="round"/><circle cx="17" cy="12" r="2.5"/></svg>',
      ai: '<svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3v4M12 17v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M3 12h4M17 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" stroke-linecap="round"/><circle cx="12" cy="12" r="4.5"/></svg>',
      shield: '<svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3l7 3v5c0 4.7-2.8 7.8-7 10-4.2-2.2-7-5.3-7-10V6l7-3z" stroke-linejoin="round"/><path d="M9.5 12.2l1.7 1.8 3.3-3.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
      action: '<svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M7 12h10M13 8l4 4-4 4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
      research: '<svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 4h9a3 3 0 0 1 3 3v13l-4-2-4 2-4-2-4 2V7a3 3 0 0 1 3-3z" stroke-linejoin="round"/></svg>'
    };

    return icons[name] || icons.action;
  }

  function featureCard(item) {
    return [
      '<article class="content-card rounded-[28px] border border-line p-6">',
      '  <div class="icon-chip">' + icon(item.icon) + "</div>",
      '  <h3 class="mt-4 text-2xl font-bold text-ink">' + item.title + "</h3>",
      '  <p class="mt-3 text-sm leading-7 text-slateText">' + item.body + "</p>",
      "</article>"
    ].join("");
  }

  function processCards() {
    return [
      {
        icon: "compare",
        title: "1. מעלים את מבנה המשכנתא הקיים",
        body: "יתרות, מסלולים, ריביות, תחנות איפוס, עלויות יציאה והעדפות משק בית, בתוך אשף חינמי אחד."
      },
      {
        icon: "ai",
        title: "2. המנוע ה-AI-driven בונה השוואה",
        body: "המערכת משווה בין שמירה על המצב הקיים, מחזור מלא ומחזור חלקי, תחת הנחות שוק ותרחישי סיכון."
      },
      {
        icon: "shield",
        title: "3. מקבלים המלצה עם הסבר",
        body: "החיסכון, break-even, הדחיפות, הסיכונים והמגבלות מוצגים יחד עם כתב ויתור ברור."
      }
    ].map(featureCard).join("");
  }

  function examplePanel() {
    return [
      '<section class="surface-banner mt-20 rounded-[36px] border border-line p-8 shadow-panel">',
      '  <div class="grid gap-8 lg:grid-cols-[0.95fr,1.05fr] lg:items-center">',
      '    <div>',
      '      <h2 class="text-3xl font-extrabold text-ink">כך נראה מסך ההחלטה אחרי סיום האשף</h2>',
      '      <p class="mt-4 text-base leading-8 text-slateText">הדוגמה ממחישה איך המערכת מציגה המלצה מבוססת AI, חיסכון נטו, רמת דחיפות ונקודת איזון. רק לאחר אישור עניין מצד הלקוח אפשר להעביר בקשה להמשך טיפול.</p>',
      '      <div class="mt-6 grid gap-3 sm:grid-cols-3">',
      '        <div class="metric-slab rounded-[24px] px-4 py-4"><p class="text-sm font-semibold text-slateText">תשלום כיום</p><p class="mt-2 text-2xl font-extrabold text-ink tabular-nums">' + App.Format.currency(7640) + "</p></div>",
      '        <div class="metric-slab rounded-[24px] px-4 py-4"><p class="text-sm font-semibold text-slateText">תשלום מוצע</p><p class="mt-2 text-2xl font-extrabold text-ink tabular-nums">' + App.Format.currency(6980) + "</p></div>",
      '        <div class="metric-slab rounded-[24px] px-4 py-4"><p class="text-sm font-semibold text-slateText">Break-even</p><p class="mt-2 text-2xl font-extrabold text-ink tabular-nums">17 חודשים</p></div>',
      "      </div>",
      "    </div>",
      '    <div class="glass-panel rounded-[32px] border border-line p-6 shadow-panel">',
      '      <div class="flex items-start justify-between gap-4">',
      '        <div><p class="text-sm font-semibold text-slateText">המלצת מערכת</p><h3 class="mt-2 text-2xl font-extrabold text-ink">מחזור חלקי עדיף כעת</h3></div>',
      "      </div>",
      '      <div class="mt-6 grid gap-4 sm:grid-cols-2">',
      App.UI.metricCard({ label: "חיסכון חודשי", value: App.Format.currency(660), note: "כולל השוואה מול המסלולים הקיימים" }),
      App.UI.metricCard({ label: "חיסכון מצטבר", value: App.Format.currency(184300), note: "אחרי עלויות מעבר משוערות" }),
      App.UI.metricCard({ label: "ירידת סיכון", value: "74 ← 48", note: "צמצום חשיפה לפריים ולמדד" }),
      App.UI.metricCard({ label: "סטטוס", value: "ממתין לאישור לקוח", note: "אין מימוש אוטומטי של ההמלצה" }),
      "      </div>",
      '      <div class="mt-6 rounded-[24px] border border-line bg-white px-5 py-4 text-sm leading-7 text-slateText">אם נמצאה חלופה טובה יותר, המערכת מבקשת אישור עניין בלבד ומעבירה את הבקשה לצוות להמשך טיפול.</div>',
      "    </div>",
      "  </div>",
      "</section>"
    ].join("");
  }

  App.Pages.landing = function (root) {
    App.MockApi.getLandingData().then(function (data) {
      root.innerHTML = [
        '<section class="hero-shell hero-grid overflow-hidden rounded-[40px] border border-line px-6 py-10 shadow-panel sm:px-8 lg:px-10">',
        '  <div class="grid gap-10 lg:grid-cols-[1.08fr,0.92fr] lg:items-center">',
        '    <div>',
        '      <h1 class="max-w-3xl text-balance text-4xl font-extrabold leading-tight text-ink sm:text-5xl lg:text-6xl">האם כדאי למחזר את המשכנתא עכשיו?</h1>',
        '      <p class="mt-5 max-w-2xl text-lg leading-8 text-slateText">Labib הוא כלי החלטה AI-driven למחזור ומעקב של משכנתא קיימת. הוא משווה בין התיק הנוכחי לחלופות שוק, מסביר חיסכון נטו, סיכון, דחיפות ו-break-even, ומבהיר מתי נדרש ייעוץ אנושי לפני פעולה.</p>',
        '      <div class="mt-6 grid gap-3 sm:grid-cols-3">',
        '        <div class="content-card-soft rounded-[24px] border border-line px-4 py-4"><div class="icon-chip">' + icon("compare") + '</div><p class="mt-4 text-sm font-semibold text-ink">השוואה בין תיק קיים, מחזור מלא ומחזור חלקי</p></div>',
        '        <div class="content-card-soft rounded-[24px] border border-line px-4 py-4"><div class="icon-chip">' + icon("ai") + '</div><p class="mt-4 text-sm font-semibold text-ink">ניתוח AI-driven עם הסבר, הנחות ודחיפות</p></div>',
        '        <div class="content-card-soft rounded-[24px] border border-line px-4 py-4"><div class="icon-chip">' + icon("shield") + '</div><p class="mt-4 text-sm font-semibold text-ink">כלי המלצה בלבד, לא תחליף לייעוץ מקצועי</p></div>',
        "      </div>",
        '      <div class="mt-8 flex flex-wrap gap-3">',
        '        <a href="' + App.Helpers.link("pages/onboarding.html") + '" class="rounded-full bg-brand-600 px-7 py-3.5 text-sm font-bold text-white">נסו את האשף החינמי</a>',
        '        <a href="' + App.Helpers.link("pages/login.html") + '" class="rounded-full border border-line px-7 py-3.5 text-sm font-bold text-ink">כניסה לחשבון קיים</a>',
        "      </div>",
        "    </div>",
        '    <div class="content-card overflow-hidden rounded-[32px] border border-line p-0">',
        '      <img src="' + App.Helpers.link("assets/images/header.png") + '" alt="Mortgage dashboard preview" class="h-full w-full object-cover" />',
        "    </div>",
        "  </div>",
        "</section>",
        '<section id="how-it-works" class="mt-20">',
        '  <div class="mb-8 flex items-end justify-between gap-4">',
        '    <div><h2 class="text-3xl font-bold text-ink">אשף אחד, ניתוח אחד, החלטה ברורה יותר</h2></div>',
        "  </div>",
        '  <div class="grid gap-6 lg:grid-cols-3">' + processCards() + "</div>",
        "</section>",
        examplePanel(),
        '<section id="benefits" class="mt-20 grid gap-6 lg:grid-cols-[1.1fr,0.9fr]">',
        '  <div class="content-card rounded-[32px] border border-line p-8">',
        '    <h2 class="text-3xl font-extrabold text-ink">יותר בהירות, פחות רעש</h2>',
        '    <p class="mt-4 text-base leading-8 text-slateText">הממשק בנוי ככלי עבודה פיננסי: מספרים גדולים, כרטיסים ברורים, הנחות גלויות והפרדה בין תוצאות, סיכון והשלבים הבאים. ההמלצות מבוססות AI, אך תמיד מוצגות עם מגבלות וכתב ויתור.</p>',
        '    <div class="mt-8 space-y-4">',
        '      <div class="metric-slab rounded-[24px] p-5"><div class="flex items-center justify-between"><span class="text-sm font-semibold text-slateText">חיסכון חודשי מזוהה</span><span class="text-2xl font-bold tabular-nums text-ink">₪660</span></div></div>',
        '      <div class="metric-slab rounded-[24px] p-5"><div class="flex items-center justify-between"><span class="text-sm font-semibold text-slateText">Break-even משוער</span><span class="text-2xl font-bold tabular-nums text-ink">17 חודשים</span></div></div>',
        '      <div class="metric-slab rounded-[24px] p-5"><div class="flex items-center justify-between"><span class="text-sm font-semibold text-slateText">מודל השוואה</span><span class="text-2xl font-bold text-ink">מלא + חלקי</span></div></div>',
        "    </div>",
        "  </div>",
        '  <div class="space-y-6">' + data.benefits.map(function (item, index) {
          return featureCard({
            icon: index === 0 ? "compare" : index === 1 ? "action" : "shield",
            title: item.title,
            body: item.body
          });
        }).join("") + "</div>",
        "</section>",
        '<section id="faq" class="mt-20">',
        '  <div class="mb-8"><h2 class="text-3xl font-bold text-ink">שאלות נפוצות לפני שמתחילים</h2></div>',
        App.UI.accordion(data.faq),
        "</section>",
        '<section class="mt-20 content-card rounded-[32px] border border-line p-8">',
        '  <div class="grid gap-6 lg:grid-cols-[1fr,auto] lg:items-center">',
        '    <div><h2 class="text-3xl font-bold text-ink">רוצים לבדוק את המשכנתא הקיימת ללא עלות?</h2><p class="mt-3 max-w-2xl text-base leading-7 text-slateText">האשף החינמי אוסף את נתוני המשכנתא, מציג המלצה AI-driven, ורק בסוף יוצר את החשבון האישי כדי לשמור את התוצאות ולעקוב אחריהן לאורך זמן.</p></div>',
        '    <div><a href="' + App.Helpers.link("pages/onboarding.html") + '" class="rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white">התחלת אשף חינמי</a></div>',
        "  </div>",
        "</section>"
      ].join("");
    });
  };

  App.Pages.consent = function (root) {
    root.innerHTML = [
      App.UI.renderPageHeader({
        eyebrow: "legal disclaimer",
        title: "כתב ויתור והסכמה",
        description: "העמוד מרכז נוסח משפטי ראשוני עד לפרסום המסמך המלא."
      }),
      '<section class="content-card rounded-[32px] border border-line p-8 shadow-soft"><p class="text-base leading-8 text-slateText">השימוש במערכת מיועד לסימולציה, ניטור והמלצה תומכת החלטה בלבד, על בסיס נתונים שהמשתמש מזין והנחות שוק שעשויות להשתנות, ולכן אין לראות בתוצאה ייעוץ פיננסי, ייעוץ משפטי, ייעוץ מס, שיווק משכנתא, התחייבות לחיסכון, הצעה מחייבת או אישור לביצוע מחזור בפועל; כל החלטה מחייבת בדיקה אנושית, אימות מסמכים, בדיקת עמלות, בדיקת זכאות ותיאום מול הגורם המלווה והיועצים הרלוונטיים, ובגרסה הבאה יפורסם כאן המסמך המשפטי המלא לרבות כל ההנחות, ההחרגות, אופן עיבוד הנתונים, מדיניות פרטיות והליך אישור העניין להמשך טיפול.</p><div class="mt-6"><a href="' + App.Helpers.link("pages/onboarding.html") + '" class="rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white">להמשך לאשף</a></div></section>'
    ].join("");
    return;

    root.innerHTML = [
      App.UI.renderPageHeader({
        eyebrow: "legal disclaimer",
        title: "לפני שממשיכים, חשוב להבין מה המערכת כן ומה היא לא",
        description: "המערכת היא כלי AI-driven לתמיכה בהחלטה על בסיס נתונים והנחות שוק. היא אינה מחליפה ייעוץ פיננסי, משפטי, מיסויי או משכנתאי אישי."
      }),
      '<section class="grid gap-6 lg:grid-cols-[1.05fr,0.95fr]">',
      '  <article class="content-card rounded-[32px] border border-line p-8">',
      '    <div class="flex items-start justify-between gap-4">',
      '      <div><h2 class="text-3xl font-bold text-ink">סימולציה מחקרית, לא הצעה מחייבת</h2></div>',
      App.UI.badge("warning", "נדרש אישור"),
      "    </div>",
      '    <p class="mt-5 text-base leading-8 text-slateText">כל חישוב מוצג תחת הנחות של שוק, עלויות מעבר, אומדנים ותסריטי סיכון שעשויים להשתנות. יש לאמת מול הגורם המלווה והיועצים הרלוונטיים את הנתונים הסופיים לפני קבלת החלטה.</p>',
      '    <ul class="mt-6 space-y-3 text-sm leading-7 text-slateText">',
      '      <li class="rounded-2xl border border-line bg-surface px-4 py-3">המערכת אינה מכירה את כל התנאים המסחריים האפשריים של הבנק או הגוף המממן.</li>',
      '      <li class="rounded-2xl border border-line bg-surface px-4 py-3">עמלות פירעון מוקדם, מדד, ריבית ועוגנים עשויים להשתנות עד למועד הביצוע בפועל.</li>',
      '      <li class="rounded-2xl border border-line bg-surface px-4 py-3">התוצאה אינה מהווה התחייבות לחיסכון בפועל ואינה תחליף לייעוץ מקצועי מותאם אישית.</li>',
      '      <li class="rounded-2xl border border-line bg-surface px-4 py-3">המערכת אינה מבצעת פעולה אוטומטית על בסיס ההמלצה. היא מבקשת אישור עניין בלבד.</li>',
      "    </ul>",
      "  </article>",
      '  <form id="consent-form" class="content-card rounded-[32px] border border-line p-8">',
      '    <h3 class="text-2xl font-bold text-ink">אישור והמשך לאשף החינמי</h3>',
      '    <div class="mt-6 space-y-4 text-sm text-slateText">',
      '      <label class="flex items-start gap-3 rounded-2xl border border-line p-4"><input class="mt-1 h-4 w-4 rounded border-line text-brand-600 focus:ring-brand-600" type="checkbox" name="acknowledge" /><span>קראתי והבנתי שהמערכת מציגה סימולציה והמלצה בלבד.</span></label>',
      '      <label class="flex items-start gap-3 rounded-2xl border border-line p-4"><input class="mt-1 h-4 w-4 rounded border-line text-brand-600 focus:ring-brand-600" type="checkbox" name="limitations" /><span>אני מאשר/ת שהנתונים שאזין משקפים ככל האפשר את מבנה המשכנתא הקיים.</span></label>',
      '      <label class="flex items-start gap-3 rounded-2xl border border-line p-4"><input class="mt-1 h-4 w-4 rounded border-line text-brand-600 focus:ring-brand-600" type="checkbox" name="expert" /><span>אופציונלי: אני מעוניין/ת שגם מומחה יוכל לראות את הסיכום לאחר שאאשר עניין בהמשך.</span></label>',
      "    </div>",
      '    <div id="consent-state" class="mt-5 text-sm"></div>',
      '    <button type="submit" class="mt-6 w-full rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white">המשך להזנת המשכנתא</button>',
      '    <p class="mt-4 text-xs text-slateText">אפשר להפסיק בכל שלב. הנתונים נשמרים בדפדפן לצורך הדגמה בלבד.</p>',
      "  </form>",
      "</section>"
    ].join("");

    $("#consent-form").on("submit", function (event) {
      event.preventDefault();
      var acknowledge = $(this).find('[name="acknowledge"]').is(":checked");
      var limitations = $(this).find('[name="limitations"]').is(":checked");
      var expert = $(this).find('[name="expert"]').is(":checked");

      if (!acknowledge || !limitations) {
        $("#consent-state").html('<div class="rounded-2xl border border-danger/20 bg-red-50 px-4 py-3 text-danger">יש לאשר את שני הסעיפים המחייבים לפני המשך.</div>');
        return;
      }

      App.State.save({
        profile: $.extend({}, App.State.load().profile, {
          expertRequested: expert
        })
      });

      $("#consent-state").html('<div class="rounded-2xl border border-success/20 bg-emerald-50 px-4 py-3 text-success">האישור התקבל. מעבירים אותך לאשף החינמי.</div>');
      window.setTimeout(function () {
        window.location.href = App.Helpers.link("pages/onboarding.html");
      }, 650);
    });
  };

  App.Pages.about = function (root) {
    root.innerHTML = [
      App.UI.renderPageHeader({
        eyebrow: "about labib",
        title: "אודות Labib Mortgage Monitor",
        description: "Labib הוא מוצר מחקרי ו-AI-driven לניתוח משכנתאות קיימות, ניטור הזדמנויות למחזור והצגת המלצות ברורות לצד הנחות, מגבלות וצעדים הבאים."
      }),
      '<section class="grid gap-6 lg:grid-cols-[1.1fr,0.9fr]">',
      '  <article class="content-card rounded-[32px] border border-line p-8 shadow-panel">',
      '    <h2 class="text-3xl font-extrabold text-ink">פיתוח מבוסס מחקר, כלכלה ומתמטיקה</h2>',
      '    <p class="mt-4 text-base leading-8 text-slateText">המוצר פותח כדי לתת למחזיקי משכנתאות קיימות כלי החלטה רציני, שקוף ושימושי. במקום שיח שיווקי, המיקוד הוא בהשוואה, explainability, robust scenarios וכתבי ויתור ברורים.</p>',
      '    <div class="mt-8 grid gap-4 md:grid-cols-2">',
      '      <div class="content-card-soft rounded-[24px] border border-line p-5"><p class="text-sm font-bold text-slateText">Dr. Labib Shami</p><p class="mt-2 text-xl font-bold text-ink">Economist</p><p class="mt-3 text-sm leading-7 text-slateText">פיתוח המסגרת הכלכלית, מדדי הכדאיות ותצוגת העלות-תועלת.</p></div>',
      '      <div class="content-card-soft rounded-[24px] border border-line p-5"><p class="text-sm font-bold text-slateText">Prof\' Teddy Lazebnik</p><p class="mt-2 text-xl font-bold text-ink">Mathematician</p><p class="mt-3 text-sm leading-7 text-slateText">פיתוח המודלים, תרחישי הרובסטיות והלוגיקה האנליטית.</p></div>',
      "    </div>",
      "  </article>",
      '  <div class="space-y-6">',
      featureCard({
        icon: "ai",
        title: "AI-driven, אבל שקוף",
        body: "המערכת מייצרת המלצה מבוססת נתונים, אך תמיד מציגה גם הנחות, מגבלות, רגישות וכתב ויתור ברור."
      }),
      featureCard({
        icon: "research",
        title: "Research-based by design",
        body: "הדגש הוא על ניתוח כלכלי, מתמטי ותפעולי של משכנתא קיימת, ולא על שיווק אגרסיבי של מסלולים חדשים."
      }),
      featureCard({
        icon: "shield",
        title: "Human confirmation stays in the loop",
        body: "גם כשנמצאת חלופה טובה יותר, המערכת אינה מפעילה אותה. היא מבקשת את אישור הלקוח ומעבירה את הבקשה להמשך טיפול."
      }),
      "  </div>",
      "</section>"
    ].join("");
  };
})();
