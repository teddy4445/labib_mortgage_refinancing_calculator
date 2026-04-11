(function () {
  window.App = window.App || {};

  var publicLinks = [
    { label: "איך זה עובד", href: "index.html#how-it-works" },
    { label: "יתרונות", href: "index.html#benefits" },
    { label: "שאלות נפוצות", href: "index.html#faq" }
  ];

  var appNav = [
    { key: "dashboard", label: "לוח מחוונים", href: "pages/dashboard.html", icon: "&#9684;" },
    { key: "mortgage-workspace", label: "מרחב המשכנתא", href: "pages/mortgage-workspace.html", icon: "&#9635;" },
    { key: "analysis-center", label: "מרכז ניתוח", href: "pages/analysis-center.html", icon: "&#9711;" },
    { key: "partial-refinance", label: "מחזור חלקי", href: "pages/partial-refinance.html", icon: "&#9675;" },
    { key: "scenarios", label: "תרחישים", href: "pages/scenarios.html", icon: "&#9678;" },
    { key: "alerts", label: "התראות", href: "pages/alerts.html", icon: "&#9673;" },
    { key: "settings", label: "הגדרות", href: "pages/settings.html", icon: "&#9881;" }
  ];

  function t(value, fallback) {
    return App.I18n && App.I18n.t ? App.I18n.t(value, fallback) : (value || fallback || "");
  }

  function isOnboardingPage() {
    return document.body.dataset.page === "onboarding";
  }

  function logoMarkup(isAdmin) {
    return [
      '<a href="' + App.Helpers.link("index.html") + '" class="flex items-center gap-3">',
      '  <span class="flex h-11 w-11 items-center justify-center rounded-2xl brand-chip text-lg font-extrabold shadow-soft">LM</span>',
      '  <span class="block text-lg font-bold text-ink">' + t(isAdmin ? "Labib Admin" : "Labib Mortgage Monitor") + "</span>",
      "</a>"
    ].join("");
  }

  function navLinksMarkup(items, activeKey) {
    return items.map(function (item) {
      var active = item.key && item.key === activeKey;
      return '<a href="' + App.Helpers.link(item.href) + '" class="nav-link flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm font-semibold' + (active ? " is-active" : "") + '"><span class="nav-link-icon inline-flex h-8 w-8 items-center justify-center rounded-xl text-sm">' + (item.icon || "&#8226;") + "</span><span>" + item.label + "</span></a>";
    }).join("");
  }

  function mobileMenu(items, extraLinks, signOutHref, isAdmin) {
    var allLinks = items.slice();

    (extraLinks || []).forEach(function (item) {
      allLinks.push(item);
    });

    if (signOutHref) {
      allLinks.push({ label: isAdmin ? "חזרה לאתר הראשי" : "התנתקות", href: signOutHref, icon: "&#8617;" });
    }

    return [
      '<div class="hidden border-t border-line bg-white px-4 pb-4 pt-2 lg:hidden" data-mobile-menu>',
      '  <div class="space-y-2">',
      allLinks.map(function (item) {
        return '<a href="' + App.Helpers.link(item.href) + '" class="nav-link nav-link-mobile flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm font-semibold"><span class="nav-link-icon inline-flex h-8 w-8 items-center justify-center rounded-xl text-sm">' + (item.icon || "&#8226;") + "</span><span>" + item.label + "</span></a>";
      }).join(""),
      '    <label class="mt-2 block rounded-2xl border border-line bg-white px-4 py-3"><span class="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slateText">' + t("Language") + '</span><select data-language-switcher class="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm font-semibold text-ink">' + App.I18n.optionsMarkup() + "</select></label>",
      "  </div>",
      "</div>"
    ].join("");
  }

  function publicHeader() {
    var headerLinks = isOnboardingPage() ? [] : publicLinks;
    var mobileExtraLinks = isOnboardingPage() ? [
      { label: "כניסה", href: "pages/login.html", icon: "&#8658;" }
    ] : [
      { label: "אשף חינמי", href: "pages/onboarding.html", icon: "&#8594;" },
      { label: "כניסה", href: "pages/login.html", icon: "&#8658;" }
    ];

    return [
      '<header class="site-header border-b border-line/80 bg-white/95 backdrop-blur">',
      '  <div class="mx-auto flex max-w-dashboard items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">',
      logoMarkup(false),
      '    <div class="hidden items-center gap-6 lg:flex">' + headerLinks.map(function (link) {
        return '<a href="' + App.Helpers.link(link.href) + '" class="text-sm font-medium text-slateText hover:text-brand-600">' + link.label + "</a>";
      }).join("") + "</div>",
      '    <div class="hidden items-center gap-3 lg:flex">',
      '      <label><span class="sr-only">' + t("Language") + '</span><select data-language-switcher class="rounded-full border border-line bg-white px-4 py-2 text-sm font-semibold text-ink">' + App.I18n.optionsMarkup() + "</select></label>",
      '      <a href="' + App.Helpers.link("pages/login.html") + '" class="rounded-full border border-line px-4 py-2 text-sm font-semibold text-ink">כניסה</a>',
      "    </div>",
      '    <button type="button" class="rounded-full border border-line p-3 lg:hidden" data-mobile-menu-toggle aria-label="פתח ניווט">&#9776;</button>',
      "  </div>",
      mobileMenu(headerLinks, mobileExtraLinks, null, false),
      "</header>"
    ].join("");
  }

  function footer() {
    return [
      '<footer class="border-t border-line/80 bg-white">',
      '  <div class="mx-auto grid max-w-dashboard gap-8 px-4 py-10 sm:px-6 lg:grid-cols-3 lg:px-8">',
      '    <div><h4 class="text-sm font-bold text-ink">אודות</h4><p class="mt-3 text-sm leading-7 text-slateText">המערכת פותחה על ידי Dr. Labib Shami, Economist, ו-Prof. Teddy Lazebnik, Mathematician. זהו כלי מחקרי ו-AI-driven לניתוח משכנתאות קיימות.</p></div>',
      '    <div><h4 class="text-sm font-bold text-ink">קישורים</h4><div class="mt-3 space-y-2 text-sm text-slateText"><a class="block hover:text-brand-600" href="' + App.Helpers.link("pages/consent.html") + '">כתב ויתור והסכמה</a><a class="block hover:text-brand-600" href="' + App.Helpers.link("pages/about.html") + '">אודות</a></div></div>',
      '    <div><h4 class="text-sm font-bold text-ink">יצירת קשר</h4><div class="mt-3 space-y-2 text-sm text-slateText"><p>support@labib.co.il</p><p>ימים א-ה, 09:00-17:00</p></div></div>',
      "</div>",
      "</footer>"
    ].join("");
  }

  function appHeader(isAdmin) {
    var signOutHref = isAdmin ? "index.html" : "pages/login.html";
    var headerLinks = isAdmin ? [
      { label: "דשבורד אדמין", href: "pages/admin/dashboard.html", icon: "&#9642;" }
    ] : appNav;

    return [
      '<header class="site-header border-b border-line/80 bg-white/95 backdrop-blur">',
      '  <div class="mx-auto flex max-w-[1440px] items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">',
      logoMarkup(isAdmin),
      '    <div class="hidden items-center gap-3 lg:flex">',
      '      <label><span class="sr-only">' + t("Language") + '</span><select data-language-switcher class="rounded-full border border-line bg-white px-4 py-2 text-sm font-semibold text-ink">' + App.I18n.optionsMarkup() + "</select></label>",
      '      <a href="' + App.Helpers.link(signOutHref) + '" class="rounded-full border border-line px-4 py-2 text-sm font-semibold text-ink">' + (isAdmin ? "חזרה לאתר" : "התנתקות") + "</a>",
      "    </div>",
      '    <button type="button" class="rounded-full border border-line p-3 lg:hidden" data-mobile-menu-toggle aria-label="פתח ניווט">&#9776;</button>',
      "  </div>",
      mobileMenu(headerLinks, [], signOutHref, isAdmin),
      "</header>"
    ].join("");
  }

  function appSidebar() {
    var pageKey = document.body.dataset.page;
    return [
      '<aside class="hidden py-8 lg:block">',
      '  <div class="noise-bg sticky top-28 overflow-hidden rounded-[28px] border border-line bg-white p-6 shadow-soft">',
      '    <div class="mb-6 flex items-center gap-4 rounded-[24px] border border-brand-100 bg-gradient-to-br from-brand-50 to-amber-50 px-5 py-5">',
      '      <span class="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-xl text-brand-700 shadow-soft">&#9672;</span>',
      '      <div><p class="text-xs font-bold uppercase tracking-[0.18em] text-slateText">workspace</p><p class="text-lg font-bold text-ink">סביבת עבודה</p></div>',
      "    </div>",
      '    <div class="space-y-4">' + navLinksMarkup(appNav, pageKey) + "</div>",
      "  </div>",
      "</aside>"
   ].join("");
  }

  function mobileNav(list, activeKey) {
    return [
      '<div class="mobile-summary-bar fixed inset-x-0 bottom-0 z-40 border-t border-line bg-white px-3 py-3 lg:hidden">',
      '  <div class="grid grid-cols-4 gap-2 text-center">',
      list.slice(0, 4).map(function (item) {
        var active = item.key === activeKey;
        return '<a href="' + App.Helpers.link(item.href) + '" class="mobile-nav-link rounded-2xl border px-2 py-3 text-xs font-semibold' + (active ? " is-active" : "") + '">' + item.label + "</a>";
      }).join(""),
      "  </div>",
      "</div>"
    ].join("");
  }

  App.Layout = {
    init: function () {
      var shellType = document.body.dataset.layout || "public";
      var root = document.querySelector("[data-app-shell]");

      if (!root) {
        return;
      }

      var shells = {
        public: [
          publicHeader(),
          '<main class="mx-auto min-h-[calc(100vh-164px)] max-w-dashboard px-4 py-10 sm:px-6 lg:px-8" data-page-content></main>',
          footer(),
          '<div data-modal-root></div>'
        ].join(""),
        auth: [
          publicHeader(),
          '<main class="mx-auto min-h-[calc(100vh-164px)] max-w-dashboard px-4 py-10 sm:px-6 lg:px-8" data-page-content></main>',
          footer(),
          '<div data-modal-root></div>'
        ].join(""),
        app: [
          appHeader(false),
          '<div class="mx-auto max-w-[1440px] px-4 pb-24 sm:px-6 lg:px-8">',
          '  <div class="lg:grid lg:grid-cols-[290px,minmax(0,1fr)] lg:gap-6">',
          appSidebar(),
          '    <main class="py-8" data-page-content></main>',
          "  </div>",
          "</div>",
          mobileNav(appNav, document.body.dataset.page),
          '<div data-modal-root></div>'
        ].join(""),
        admin: [
          appHeader(true),
          '<main class="mx-auto max-w-[1280px] px-4 py-10 sm:px-6 lg:px-8" data-page-content></main>',
          '<div data-modal-root></div>'
        ].join("")
      };

      root.innerHTML = shells[shellType] || shells.public;

      $(document).on("click", "[data-mobile-menu-toggle]", function () {
        $(this).closest("header").find("[data-mobile-menu]").first().slideToggle(150).toggleClass("hidden");
      });

      $(document).on("change", "[data-language-switcher]", function () {
        App.I18n.setLanguage($(this).val());
      });
    }
  };
})();
