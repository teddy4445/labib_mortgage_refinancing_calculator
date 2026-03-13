(function () {
  window.App = window.App || {};
  App.Pages = App.Pages || {};

  function renderStatus(root, config) {
    root.innerHTML = [
      '<section class="mx-auto max-w-4xl rounded-[36px] border border-line bg-white p-8 text-center shadow-panel sm:p-12">',
      '  <div class="status-ring mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-surface text-3xl font-extrabold text-brand-600">' + config.symbol + "</div>",
      '  <p class="mt-6 text-sm font-bold uppercase tracking-[0.24em] text-slateText">' + config.eyebrow + "</p>",
      '  <h1 class="mt-3 text-4xl font-extrabold text-ink sm:text-5xl">' + config.title + "</h1>",
      '  <p class="mx-auto mt-4 max-w-2xl text-base leading-8 text-slateText">' + config.description + "</p>",
      (config.extra ? '  <div class="mt-8">' + config.extra + "</div>" : ""),
      '  <div class="mt-8 flex flex-wrap justify-center gap-3">' + config.actions + "</div>",
      "</section>"
    ].join("");
  }

  App.Pages["email-verification"] = function (root) {
    renderStatus(root, {
      symbol: "OK",
      eyebrow: "verification",
      title: "האימייל אומת בהצלחה",
      description: "החשבון מוכן להמשך התהליך. אפשר לעבור למסך הכניסה ולהמשיך לאזור האישי או לאשף.",
      actions: '<a href="' + App.Helpers.link("pages/login.html") + '" class="rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">למסך הכניסה</a><a href="' + App.Helpers.link("index.html") + '" class="rounded-full border border-line px-6 py-3 text-sm font-bold text-ink hover:border-brand-600 hover:text-brand-600">חזרה לאתר</a>'
    });
  };

  App.Pages["session-expired"] = function (root) {
    renderStatus(root, {
      symbol: "00",
      eyebrow: "session",
      title: "הסשן פג תוקף",
      description: "מטעמי אבטחה, יש להיכנס שוב כדי להמשיך לצפות בתוצאות, בניתוחים ובהתראות.",
      actions: '<a href="' + App.Helpers.link("pages/login.html") + '" class="rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">כניסה מחדש</a>'
    });
  };

  App.Pages["status-404"] = function (root) {
    renderStatus(root, {
      symbol: "404",
      eyebrow: "not found",
      title: "העמוד יצא לבדוק ריביות ולא חזר",
      description: "הכתובת הזו לא נמצאה. ייתכן שהקישור השתנה, הוסר, או שפשוט הגעת למסך שלא קיים יותר.",
      extra: '<div class="grid gap-4 sm:grid-cols-3"><div class="rounded-[24px] border border-line bg-surface px-5 py-4 text-sm text-slateText">אפשר להתחיל מחדש מהאשף החינמי.</div><div class="rounded-[24px] border border-line bg-surface px-5 py-4 text-sm text-slateText">אפשר לקפוץ ישר ללוח המחוונים אם כבר קיים חשבון.</div><div class="rounded-[24px] border border-line bg-surface px-5 py-4 text-sm text-slateText">ואפשר גם פשוט להעמיד פנים שזה היה מבחן ניווט.</div></div>',
      actions: '<a href="' + App.Helpers.link("index.html") + '" class="rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">חזרה לעמוד הבית</a><a href="' + App.Helpers.link("pages/onboarding.html") + '" class="rounded-full border border-line px-6 py-3 text-sm font-bold text-ink hover:border-brand-600 hover:text-brand-600">לאשף החינמי</a>'
    });
  };

  App.Pages["status-500"] = function (root) {
    renderStatus(root, {
      symbol: "500",
      eyebrow: "server error",
      title: "שגיאת שרת",
      description: "אירעה תקלה פנימית במערכת ולא ניתן היה לטעון את המידע המבוקש.",
      actions: '<a href="' + App.Helpers.link("pages/dashboard.html") + '" class="rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">נסה שוב</a><a href="' + App.Helpers.link("index.html") + '" class="rounded-full border border-line px-6 py-3 text-sm font-bold text-ink hover:border-brand-600 hover:text-brand-600">לעמוד הבית</a>'
    });
  };

  App.Pages.maintenance = function (root) {
    renderStatus(root, {
      symbol: "!",
      eyebrow: "maintenance",
      title: "המערכת לא זמינה זמנית",
      description: "ייתכן שמתבצע עדכון שוק, תחזוקה מתוזמנת או השהיה זמנית של שכבת הנתונים.",
      actions: '<a href="' + App.Helpers.link("index.html") + '" class="rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">חזרה לדף הבית</a>'
    });
  };

  App.Pages["access-denied"] = function (root) {
    renderStatus(root, {
      symbol: "X",
      eyebrow: "access denied",
      title: "אין הרשאה לצפות במסך הזה",
      description: "העמוד שביקשת מוגבל לפי הרשאות תפקיד, סטטוס חשבון או שיוך ארגוני.",
      actions: '<a href="' + App.Helpers.link("pages/login.html") + '" class="rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">כניסה עם חשבון אחר</a><a href="' + App.Helpers.link("index.html") + '" class="rounded-full border border-line px-6 py-3 text-sm font-bold text-ink hover:border-brand-600 hover:text-brand-600">חזרה לאתר</a>'
    });
  };
})();
