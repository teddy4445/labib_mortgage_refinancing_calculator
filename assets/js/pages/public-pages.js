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
        title: "1. את/ה מזינים, המערכת מעבדת",
        body: "יתרות נוכחיות, ריביות, עלויות וכל המידע החשוב על התיק שלך - בשלב אחד פשוט וברור."
      },
      {
        icon: "ai",
        title: "2. ניתוח מדעי, לא שיווקי",
        body: "בדיקה עמוקה של כל אפשרות תחת הנחות בשוק אמיתיות, ללא דחיפה מכירות או הטיות."
      },
      {
        icon: "shield",
        title: "3. המלצה שאת/ה בשליטה",
        body: "תשובה ברורה עם הסבר מלא - בלי לחץ, בלי התחייבות, ובלי הפתעות בהמשך."
      }
    ].map(featureCard).join("");
  }

  function examplePanel() {
    return [
      '<section class="surface-banner mt-20 rounded-[36px] border border-line p-8 shadow-panel">',
      '  <div class="grid gap-8 lg:grid-cols-[0.95fr,1.05fr] lg:items-center">',
      '    <div>',
      '      <h2 class="text-3xl font-extrabold text-ink">כך נראית ההמלצה אחרי סיום האשף</h2>',
      '      <p class="mt-4 text-base leading-8 text-slateText">המערכת מציגה בבירור: מה ההמלצה, כמה אפשר לחסוך, מתי תתפרע את העלות, ומה רמת הסיכון. ורק לאחר אישור עניין משלך, אפשר להעביר בקשה להמשך טיפול עם מומחה.</p>',
      '      <div class="mt-6 grid gap-3 sm:grid-cols-3">',
      '        <div class="metric-slab rounded-[24px] px-4 py-4"><p class="text-sm font-semibold text-slateText">תשלום כיום</p><p class="mt-2 text-2xl font-extrabold text-ink tabular-nums">' + App.Format.currency(7640) + "</p></div>",
      '        <div class="metric-slab rounded-[24px] px-4 py-4"><p class="text-sm font-semibold text-slateText">תשלום מוצע</p><p class="mt-2 text-2xl font-extrabold text-ink tabular-nums">' + App.Format.currency(6980) + "</p></div>",
      '        <div class="metric-slab rounded-[24px] px-4 py-4"><p class="text-sm font-semibold text-slateText">עד איזון</p><p class="mt-2 text-2xl font-extrabold text-ink tabular-nums">17 חודשים</p></div>',
      "      </div>",
      "    </div>",
      '    <div class="glass-panel rounded-[32px] border border-line p-6 shadow-panel">',
      '      <div class="flex items-start justify-between gap-4">',
      '        <div><p class="text-sm font-semibold text-slateText">המלצת המערכת</p><h3 class="mt-2 text-2xl font-extrabold text-ink">מחזור חלקי - הכי חכם כעת</h3></div>',
      "      </div>",
      '      <div class="mt-6 grid gap-4 sm:grid-cols-2">',
      App.UI.metricCard({ label: "חיסכון חודשי", value: App.Format.currency(660), note: "בהשוואה לתיק הקיים" }),
      App.UI.metricCard({ label: "חיסכון מצטבר", value: App.Format.currency(184300), note: "אחרי כל העלויות" }),
      App.UI.metricCard({ label: "צמצום סיכון", value: "מ-74 ל-48", note: "פחות חשיפה לשינויים" }),
      App.UI.metricCard({ label: "סטטוס", value: "מחכה להחלטתך", note: "אתה בשליטה מלאה" }),
      "      </div>",
      '      <div class="mt-6 rounded-[24px] border border-line bg-white px-5 py-4 text-sm leading-7 text-slateText">אם נמצאת חלופה טובה יותר, אנחנו מציגים אותה בבירור, וההחלטה אם להמשיך נשארת בידיים שלך.</div>',
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
        '      <h1 class="max-w-3xl text-balance text-4xl font-extrabold leading-tight text-ink sm:text-5xl lg:text-6xl">למחזר או לא למחזר, זאת השאלה</h1>',
        '      <p class="mt-5 max-w-2xl text-lg leading-8 text-slateText">לקיחת משכנתא היא החלטה פיננסית משמעותית, אבל ניהול נכון שלה לאורך שנות ההחזר חשוב לא פחות. המוניטור מסדר את התמונה: מנתח את התיק שלך, משווה אפשרויות ממשיות, ומציג בבהירות מה כדאי לעשות. ללא טריקים, ללא לחץ. רק מידע שאפשר להסתמך עליו.</p>',
        '      <div class="mt-6 grid gap-3 sm:grid-cols-3">',
        '        <div class="content-card-soft rounded-[24px] border border-line px-4 py-4"><div class="icon-chip">' + icon("compare") + '</div><p class="mt-4 text-sm font-semibold text-ink">השוואה שקופה - שמור, מחזור מלא, או מחזור חלקי</p></div>',
        '        <div class="content-card-soft rounded-[24px] border border-line px-4 py-4"><div class="icon-chip">' + icon("ai") + '</div><p class="mt-4 text-sm font-semibold text-ink">הבנה לפני החלטה - רואים הכל בצורה ברורה</p></div>',
        '        <div class="content-card-soft rounded-[24px] border border-line px-4 py-4"><div class="icon-chip">' + icon("shield") + '</div><p class="mt-4 text-sm font-semibold text-ink">בשליטתך - אנחנו מציגים, את/ה מחליטה/ת</p></div>',
        "      </div>",
        '      <div class="mt-8 flex flex-wrap gap-3">',
        '        <a href="' + App.Helpers.link("pages/onboarding.html") + '" class="rounded-full bg-brand-600 px-7 py-3.5 text-sm font-bold text-white">נסה את האשף החינמי</a>',
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
        '    <div><h2 class="text-3xl font-bold text-ink">שלושה שלבים פשוטים להחלטה חכמה</h2></div>',
        "  </div>",
        '  <div class="grid gap-6 lg:grid-cols-3">' + processCards() + "</div>",
        "</section>",
        examplePanel(),
        '<section id="benefits" class="mt-20 grid gap-6 lg:grid-cols-[1.1fr,0.9fr]">',
        '  <div class="content-card rounded-[32px] border border-line p-8">',
        '    <h2 class="text-3xl font-extrabold text-ink">בהירות מוחלטת, קול אחד</h2>',
        '    <p class="mt-4 text-base leading-8 text-slateText">הממשק בנוי כמו כלי עבודה פיננסי אמיתי: מספרים גדולים וברורים, כרטיסי מידע חכמים, הנחות שאתה רואה, וקו ברור בין: מה ההמלצה, מה הסיכון, מה הצעדים הבאים. תמיד עם הסתייגויות ברורות.</p>',
        '    <div class="mt-8 space-y-4">',
        '      <div class="metric-slab rounded-[24px] p-5"><div class="flex items-center justify-between"><span class="text-sm font-semibold text-slateText">חיסכון חודשי פוטנציאלי</span><span class="text-2xl font-bold tabular-nums text-ink">₪660</span></div></div>',
        '      <div class="metric-slab rounded-[24px] p-5"><div class="flex items-center justify-between"><span class="text-sm font-semibold text-slateText">זמן להחזר ההשקעה</span><span class="text-2xl font-bold tabular-nums text-ink">17 חודשים</span></div></div>',
        '      <div class="metric-slab rounded-[24px] p-5"><div class="flex items-center justify-between"><span class="text-sm font-semibold text-slateText">דרך בדיקה</span><span class="text-2xl font-bold text-ink">מלא + חלקי</span></div></div>',
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
        '  <div class="mb-8"><h2 class="text-3xl font-bold text-ink">שאלות נפוצות - קודם שמתחילים</h2></div>',
        App.UI.accordion(data.faq),
        "</section>",
        '<section class="mt-20 content-card rounded-[32px] border border-line p-8">',
        '  <div class="grid gap-6 lg:grid-cols-[1fr,auto] lg:items-center">',
        '    <div><h2 class="text-3xl font-bold text-ink">רוצה לבדוק את המשכנתא שלך ללא עלות?</h2><p class="mt-3 max-w-2xl text-base leading-7 text-slateText">האשף החינמי אוסף את כל הנתונים, מציג המלצה ברורה, ורק בסוף, אם תרצו, יוצרים חשבון כדי לשמור את התוצאות ולעקוב לאורך זמן.</p></div>',
        '    <div><a href="' + App.Helpers.link("pages/onboarding.html") + '" class="rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white">התחל את האשף</a></div>',
        "  </div>",
        "</section>"
      ].join("");
    });
  };

  App.Pages.consent = function (root) {
    root.innerHTML = [
      App.UI.renderPageHeader({
        eyebrow: "הסכמה משפטית",
        title: "כתב ויתור והסכמה",
        description: "חשוב להבין: המערכת היא כלי בדיקה בלבד, לא ייעוץ מקצועי."
      }),
      '<section class="content-card rounded-[32px] border border-line p-8 shadow-soft"><p class="text-base leading-8 text-slateText">השימוש במוניטור מיועד לסימולציה וניתוח בלבד - על בסיס נתונים שאתה/את מזינים וטובות מידע שעשויות להשתנות. התוצאה אינה ייעוץ פיננסי, משפטי או מס, ואינה הצעה מחייבת לביצוע מחזור. כל החלטה בפועל דורשת בדיקה אנושית, אימות מסמכים, ותיאום מול הבנק ויועצים מקצועיים. בגרסה הבאה יפורסם כאן המסמך המשפטי המלא עם כל ההנחות, ההגבלות ומדיניות הנתונים.</p><div class="mt-6"><a href="' + App.Helpers.link("pages/onboarding.html") + '" class="rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white">המשך לאשף</a></div></section>'
    ].join("");
    return;

    root.innerHTML = [
      App.UI.renderPageHeader({
        eyebrow: "הסכמה משפטית",
        title: "לפני שמתחילים - מה צריך לדעת",
        description: "המערכת עוזרת בבדיקה וניתוח. היא לא מחליפה ייעוץ מקצועי אמיתי."
      }),
      '<section class="grid gap-6 lg:grid-cols-[1.05fr,0.95fr]">',
      '  <article class="content-card rounded-[32px] border border-line p-8">',
      '    <div class="flex items-start justify-between gap-4">',
      '      <div><h2 class="text-3xl font-bold text-ink">זה סימולציה, לא הצעה מחייבת</h2></div>',
      App.UI.badge("warning", "חשוב"),
      "    </div>",
      '    <p class="mt-5 text-base leading-8 text-slateText">כל חישוב מוצג תחת הנחות שוק, עלויות מעבר ותרחישי סיכון שעשויים להשתנות. לפני החלטה, חייב לאמת מול הבנק והיועצים הרלוונטיים את הנתונים הסופיים.</p>',
      '    <ul class="mt-6 space-y-3 text-sm leading-7 text-slateText">',
      '      <li class="rounded-2xl border border-line bg-surface px-4 py-3">המערכת אינה יודעת על כל התנאים המיוחדים שהבנק יכול להציע.</li>',
      '      <li class="rounded-2xl border border-line bg-surface px-4 py-3">עמלות, ריביות ותנאים אחרים עשויים להשתנות עד למועד הביצוע בפועל.</li>',
      '      <li class="rounded-2xl border border-line bg-surface px-4 py-3">התוצאה אינה ערובה לחיסכון בפועל ואינה תחליף לייעוץ אישי של מומחה.</li>',
      '      <li class="rounded-2xl border border-line bg-surface px-4 py-3">המערכת לא מבצעת פעולה אוטומטית. אתה/את בשליטה מלאה.</li>',
      "    </ul>",
      "  </article>",
      '  <form id="consent-form" class="content-card rounded-[32px] border border-line p-8">',
      '    <h3 class="text-2xl font-bold text-ink">אישור והמשך</h3>',
      '    <div class="mt-6 space-y-4 text-sm text-slateText">',
      '      <label class="flex items-start gap-3 rounded-2xl border border-line p-4"><input class="mt-1 h-4 w-4 rounded border-line text-brand-600 focus:ring-brand-600" type="checkbox" name="acknowledge" /><span>קראתי והבנתי שזו סימולציה בלבד.</span></label>',
      '      <label class="flex items-start gap-3 rounded-2xl border border-line p-4"><input class="mt-1 h-4 w-4 rounded border-line text-brand-600 focus:ring-brand-600" type="checkbox" name="limitations" /><span>אני מאשר/ת שהנתונים שאזין משקפים את מבנה המשכנתא שלי ככל שאוכל.</span></label>',
      '      <label class="flex items-start gap-3 rounded-2xl border border-line p-4"><input class="mt-1 h-4 w-4 rounded border-line text-brand-600 focus:ring-brand-600" type="checkbox" name="expert" /><span>אני מעוניין/ת שמומחה יוכל לראות את הניתוח שלי לשם שיחה ממוקדת.</span></label>',
      "    </div>",
      '    <div id="consent-state" class="mt-5 text-sm"></div>',
      '    <button type="submit" class="mt-6 w-full rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white">המשך להזנת נתונים</button>',
      '    <p class="mt-4 text-xs text-slateText">אפשר להפסיק בכל עת. הנתונים נשמרים בדפדפן בלבד, לצורך הדגמה.</p>',
      "  </form>",
      "</section>"
    ].join("");

    $("#consent-form").on("submit", function (event) {
      event.preventDefault();
      var acknowledge = $(this).find('[name="acknowledge"]').is(":checked");
      var limitations = $(this).find('[name="limitations"]').is(":checked");
      var expert = $(this).find('[name="expert"]').is(":checked");

      if (!acknowledge || !limitations) {
        $("#consent-state").html('<div class="rounded-2xl border border-danger/20 bg-red-50 px-4 py-3 text-danger">צריך לאשר את שני התנאים הראשונים.</div>');
        return;
      }

      App.State.save({
        profile: $.extend({}, App.State.load().profile, {
          expertRequested: expert
        })
      });

      $("#consent-state").html('<div class="rounded-2xl border border-success/20 bg-emerald-50 px-4 py-3 text-success">תודה. מעבירים אותך לאשף.</div>');
      window.setTimeout(function () {
        window.location.href = App.Helpers.link("pages/onboarding.html");
      }, 650);
    });
  };

  App.Pages.about = function (root) {
    root.innerHTML = [
      App.UI.renderPageHeader({
        eyebrow: "על המוניטור",
        title: "אודות המוניטור",
        description: "מוצר מחקרי לניתוח משכנתאות, המבוסס על כלכלה, מתמטיקה וכללים ברורים."
      }),
      '<section class="grid gap-6 lg:grid-cols-[1.1fr,0.9fr]">',
      '  <article class="content-card rounded-[32px] border border-line p-8 shadow-panel">',
      '    <h2 class="text-3xl font-extrabold text-ink">בנוי על מחקר, לא על שיווק</h2>',
      '    <p class="mt-4 text-base leading-8 text-slateText">המוניטור פותח כדי לתת לאנשים כלי בדיקה אמיתי ושקוף. המיקוד הוא על השוואה הוגנת, הסברים ברורים, ותרחישי סיכון אמיתיים - לא על דחיפה או מכירות אגרסיביות.</p>',
      '    <div class="mt-8 grid gap-4 md:grid-cols-2">',
      '      <div class="content-card-soft rounded-[24px] border border-line p-5"><p class="text-sm font-bold text-slateText">Dr. Labib Shami</p><p class="mt-2 text-xl font-bold text-ink">כלכלן</p><p class="mt-3 text-sm leading-7 text-slateText">מסגרת כלכלית, דוגמודלים וניתוח עלות-תועלת.</p></div>',
      '      <div class="content-card-soft rounded-[24px] border border-line p-5"><p class="text-sm font-bold text-slateText">Prof\' Teddy Lazebnik</p><p class="mt-2 text-xl font-bold text-ink">מתמטיקאי</p><p class="mt-3 text-sm leading-7 text-slateText">מודלים, תרחישים חזקים ולוגיקה אנליטית.</p></div>',
      "    </div>",
      "  </article>",
      '  <div class="space-y-6">',
      featureCard({
        icon: "ai",
        title: "AI עם שקיפות מלאה",
        body: "המערכת מייצרת המלצה על בסיס נתונים, אך תמיד עם הנחות, מגבלות וכתב ויתור ברור."
      }),
      featureCard({
        icon: "research",
        title: "מחקר עם שפה ברורה",
        body: "הדגש הוא על ניתוח כלכלי, מתמטי ותפעולי של משכנתא קיימת, ולא על שיווק מסלולים חדשים."
      }),
      featureCard({
        icon: "shield",
        title: "השליטה נשארת אצלך",
        body: "גם כשנמצאת חלופה טובה, לא מתבצעת פעולה אוטומטית. ההחלטה אם להמשיך נשארת בידיים שלך, ואנחנו מסייעים רק בהמשך."
      }),
      "  </div>",
      "</section>"
    ].join("");
  };
})();
