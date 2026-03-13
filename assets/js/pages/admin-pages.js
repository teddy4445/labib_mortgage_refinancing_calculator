(function () {
  window.App = window.App || {};
  App.Pages = App.Pages || {};

  function adminAuthShell() {
    return [
      '<section class="mx-auto max-w-[620px]">',
      '  <div class="auth-card rounded-[36px] border border-line p-8 sm:p-10">',
      '    <div id="admin-login-state"></div>',
      '    <p class="text-xs font-bold uppercase tracking-[0.22em] text-slateText">admin access</p>',
      '    <h1 class="mt-4 text-4xl font-extrabold leading-tight text-ink">כניסה לאזור התפעול</h1>',
      '    <p class="mt-4 text-base leading-8 text-slateText">מסך זה מיועד לניהול פעילות האתר, מעקב שימוש באשף, בקשות עזרה, סטטוס מקורות הנתונים וטבלת המשתמשים.</p>',
      '    <div class="mt-6 grid gap-3">',
      '      <div class="rounded-[24px] border border-line bg-surface px-5 py-4 text-sm leading-7 text-slateText">בדמו זה מספיק להשתמש בסיסמה Secure123! כדי לעבור לדשבורד.</div>',
      '      <div class="rounded-[24px] border border-line bg-surface px-5 py-4 text-sm leading-7 text-slateText">הדשבורד נשאר בעמוד יחיד, ללא ניווט פנימי וללא אזורים נפרדים.</div>',
      "    </div>",
      '    <form id="admin-login-form" class="mt-8 space-y-5">',
      '      <div><label class="mb-2 block text-sm font-semibold text-ink">אימייל אדמין</label><input name="email" type="email" value="ops@labib.co.il" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm" /></div>',
      '      <div><label class="mb-2 block text-sm font-semibold text-ink">סיסמה</label><input name="password" type="password" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm" placeholder="Secure123!" /></div>',
      '      <div id="admin-login-errors" class="text-sm"></div>',
      '      <button type="submit" class="w-full rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">כניסה לאדמין</button>',
      "    </form>",
      "  </div>",
      "</section>"
    ].join("");
  }

  function adminStatCard(item) {
    return [
      '<article class="rounded-[24px] border border-line bg-white p-5 shadow-soft">',
      '  <p class="text-sm font-semibold text-slateText">' + item.label + "</p>",
      '  <p class="mt-3 text-3xl font-extrabold text-ink">' + item.value + "</p>",
      '  <p class="mt-2 text-sm font-semibold text-accent">' + item.change + "</p>",
      "</article>"
    ].join("");
  }

  function dayLabel(offset) {
    var date = new Date();
    date.setDate(date.getDate() - offset);
    return new Intl.DateTimeFormat(App.I18n.meta().locale, { day: "2-digit", month: "2-digit" }).format(date);
  }

  function buildSeries(base, range, amplitude) {
    var items = [];
    for (var offset = 29; offset >= 0; offset -= 1) {
      items.push({
        label: dayLabel(offset),
        value: base + ((offset * 7) % range) + ((offset % 3) * amplitude)
      });
    }
    return items;
  }

  function axisTicks(max) {
    var rounded = Math.max(5, Math.ceil(max / 5) * 5);
    return [rounded, Math.round(rounded * 0.75), Math.round(rounded * 0.5), Math.round(rounded * 0.25), 0];
  }

  function linePath(series, max) {
    return series.map(function (item, index) {
      var x = series.length === 1 ? 0 : (index / (series.length - 1)) * 100;
      var y = 100 - ((item.value / max) * 100);
      return (index === 0 ? "M" : "L") + x + " " + y;
    }).join(" ");
  }

  function lineChart(title, subtitle, series, color, dotColor) {
    var max = Math.max.apply(null, series.map(function (item) { return item.value; })) || 1;
    var ticks = axisTicks(max);
    var labels = [series[0], series[5], series[11], series[17], series[23], series[29]];

    return [
      '<section class="rounded-[28px] border border-line bg-white p-6 shadow-soft">',
      '  <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">',
      '    <div><h2 class="text-2xl font-bold text-ink">' + title + '</h2><p class="text-sm leading-7 text-slateText">' + subtitle + "</p></div>",
      '    <p class="text-sm font-semibold text-slateText">30 ימים אחרונים</p>',
      "  </div>",
      '  <div class="line-chart mt-6">',
      '    <div class="line-chart-y-axis">' + ticks.map(function (tick) {
        return "<span>" + tick + "</span>";
      }).join("") + "</div>",
      '    <div class="line-chart-grid">' + ticks.map(function () {
        return "<span></span>";
      }).join("") + "</div>",
      '    <div class="line-chart-plot"><svg viewBox="0 0 100 100" preserveAspectRatio="none"><path d="' + linePath(series, max) + '" fill="none" stroke-width="2.8" stroke="' + color + '"></path>' + series.map(function (item, index) {
        var x = series.length === 1 ? 0 : (index / (series.length - 1)) * 100;
        var y = 100 - ((item.value / max) * 100);
        return '<circle cx="' + x + '" cy="' + y + '" r="1.7" fill="' + dotColor + '"></circle>';
      }).join("") + "</svg></div>",
      '    <div class="line-chart-x-axis">' + labels.map(function (item) {
        return "<span>" + item.label + "</span>";
      }).join("") + "</div>",
      "  </div>",
      "</section>"
    ].join("");
  }

  function sourceTone(status) {
    if (status.indexOf("תקין") >= 0) {
      return "success";
    }
    if (status.indexOf("איחור") >= 0) {
      return "warning";
    }
    return "neutral";
  }

  App.Pages["admin-login"] = function (root) {
    root.innerHTML = adminAuthShell();

    $("#admin-login-form").on("submit", function (event) {
      event.preventDefault();
      var payload = {
        email: $(this).find('[name="email"]').val(),
        password: $(this).find('[name="password"]').val(),
        role: "admin"
      };

      App.MockApi.login(payload).then(function (response) {
        if (response.status !== "success") {
          $("#admin-login-errors").html('<div class="rounded-2xl border border-danger/20 bg-red-50 px-4 py-3 text-danger">הכניסה נכשלה. בדקו את פרטי הזיהוי.</div>');
          return;
        }

        $("#admin-login-state").html('<div class="mb-5 rounded-2xl border border-success/20 bg-emerald-50 px-4 py-3 text-success">הכניסה אושרה. מעבירים אותך לדשבורד האדמין.</div>');
        window.setTimeout(function () {
          window.location.href = App.Helpers.link("pages/admin/dashboard.html");
        }, 650);
      });
    });
  };

  App.Pages["admin-dashboard"] = function (root) {
    App.MockApi.getAdmin().then(function (admin) {
      var wizardSeries = buildSeries(18, 22, 4);
      var helpSeries = buildSeries(4, 10, 2);
      var users = admin.users.rows.map(function (row, index) {
        return $.extend({
          email: ["yael@example.com", "amir@example.com", "barak-family@example.com"][index] || ("user" + index + "@example.com"),
          phone: ["050-555-0182", "052-431-2201", "054-778-4410"][index] || "050-000-0000",
          locked: false
        }, row);
      });
      var searchTerm = "";
      var statusFilter = "all";

      function filteredUsers() {
        return users.filter(function (row) {
          var statusMatch = statusFilter === "all" ? true : row.status === statusFilter;
          var haystack = [row.name, row.city, row.email, row.phone, row.portfolio].join(" ").toLowerCase();
          var searchMatch = !searchTerm || haystack.indexOf(searchTerm.toLowerCase()) >= 0;
          return statusMatch && searchMatch;
        });
      }

      function renderAdminPage() {
        root.innerHTML = [
          '<section class="mb-6 rounded-[28px] border border-line bg-white p-6 shadow-soft"><h1 class="text-3xl font-extrabold text-ink">תפעול ומעקב אתר</h1><p class="mt-3 text-sm leading-7 text-slateText">עמוד אחד שמרכז פעילות שוטפת, שימוש באשף, בקשות עזרה, סטטוס מקורות נתונים וטבלת משתמשים.</p></section>',
          '<section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">' + admin.dashboard.stats.map(adminStatCard).join("") + "</section>",
          '<section class="mt-6 rounded-[28px] border border-line bg-white p-6 shadow-soft"><div class="grid gap-6 xl:grid-cols-2">' +
            lineChart("שימוש באשף ב-30 הימים האחרונים", "מספר ההפעלות היומי של האשף החינמי.", wizardSeries, "#123b6b", "#123b6b") +
            lineChart("בקשות עזרה ב-30 הימים האחרונים", "מספר פניות שנוצרו לאחר אישור עניין או בקשת עזרה.", helpSeries, "#d97706", "#d97706") +
          "</div></section>",
          '<section class="mt-6 rounded-[28px] border border-line bg-white p-6 shadow-soft"><div class="grid gap-6 lg:grid-cols-[0.8fr,1.2fr] lg:items-start"><div><h2 class="text-2xl font-bold text-ink">מקורות נתונים</h2><p class="mt-3 text-sm leading-7 text-slateText">סטטוס עדכון אחרון לכל מקור שוק שמזין את ההמלצות.</p><div class="mt-5 rounded-[24px] border border-line bg-surface p-5"><p class="text-sm font-semibold text-slateText">עדכון מערכת אחרון</p><p class="mt-3 text-3xl font-extrabold text-ink">2026-03-13 06:45</p><div class="mt-3">' + App.UI.badge("success", "תקין") + "</div></div></div>" +
            App.UI.table({
              columns: [
                { label: "מקור", key: "source" },
                { label: "סטטוס", render: function (row) { return App.UI.badge(sourceTone(row.status), row.status); } },
                { label: "עודכן לאחרונה", key: "updated" }
              ],
              rows: admin.marketData.sources
            }) +
          "</div></section>",
          '<section class="mt-6 rounded-[28px] border border-line bg-white p-6 shadow-soft"><div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"><div><h2 class="text-2xl font-bold text-ink">טבלת משתמשים</h2><p class="mt-3 text-sm leading-7 text-slateText">חיפוש, סינון ונעילת משתמשים מהעמוד הראשי.</p></div><div class="grid gap-3 sm:grid-cols-2"><label class="block"><span class="mb-2 block text-xs font-bold uppercase tracking-[0.18em] text-slateText">חיפוש</span><input type="search" data-admin-search class="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink" placeholder="שם, אימייל, טלפון, עיר" value="' + App.Helpers.escapeHtml(searchTerm) + '" /></label><label class="block"><span class="mb-2 block text-xs font-bold uppercase tracking-[0.18em] text-slateText">סטטוס</span><select data-admin-status class="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink"><option value="all"' + (statusFilter === "all" ? " selected" : "") + '>הכל</option><option value="פעיל"' + (statusFilter === "פעיל" ? " selected" : "") + '>פעיל</option><option value="בהמתנה"' + (statusFilter === "בהמתנה" ? " selected" : "") + '>בהמתנה</option><option value="נעול"' + (statusFilter === "נעול" ? " selected" : "") + '>נעול</option></select></label></div></div><div class="mt-5">' +
            App.UI.table({
              columns: [
                { label: "שם", key: "name" },
                { label: "אימייל", key: "email" },
                { label: "טלפון", key: "phone" },
                { label: "עיר", key: "city" },
                { label: "תיק", key: "portfolio" },
                { label: "סטטוס", render: function (row) { return row.locked ? App.UI.badge("danger", "נעול") : App.UI.badge(row.status === "פעיל" ? "success" : "warning", row.status); } },
                { label: "נראה לאחרונה", key: "lastSeen" },
                { label: "פעולה", render: function (row) { return '<button type="button" class="rounded-full border border-line px-4 py-2 text-xs font-semibold text-ink hover:border-brand-600 hover:text-brand-600" data-lock-user="' + row.email + '">' + (row.locked ? "שחרור" : "נעילה") + "</button>"; } }
              ],
              rows: filteredUsers(),
              empty: "לא נמצאו משתמשים לפי החיפוש או הסינון שנבחרו."
            }) +
          "</div></section>"
        ].join("");
      }

      renderAdminPage();

      $(root).on("input", "[data-admin-search]", function () {
        searchTerm = $(this).val();
        renderAdminPage();
      });

      $(root).on("change", "[data-admin-status]", function () {
        statusFilter = $(this).val();
        renderAdminPage();
      });

      $(root).on("click", "[data-lock-user]", function () {
        var email = $(this).data("lock-user");
        users = users.map(function (row) {
          if (row.email !== email) {
            return row;
          }

          return $.extend({}, row, {
            locked: !row.locked,
            status: row.locked ? "פעיל" : "נעול"
          });
        });
        renderAdminPage();
      });
    });
  };
})();
