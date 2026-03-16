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
      '    <div class="mt-6 hidden">',
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
    var change = item.change ? '<p class="mt-2 text-sm font-semibold text-accent">' + item.change + "</p>" : "";
    return [
      '<article class="rounded-[24px] border border-line bg-white p-5 shadow-soft">',
      '  <p class="text-sm font-semibold text-slateText">' + item.label + "</p>",
      '  <p class="mt-3 text-3xl font-extrabold text-ink">' + item.value + "</p>",
      change,
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

  function seriesFromApi(items) {
    if (!items || !items.length) {
      return [];
    }
    return items.map(function (item) {
      var date = new Date(item.date);
      var label = new Intl.DateTimeFormat(App.I18n.meta().locale, { day: "2-digit", month: "2-digit" }).format(date);
      return {
        label: label,
        value: item.value
      };
    });
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
    if (!status) {
      return "neutral";
    }
    if (status === "healthy" || status.indexOf("תקין") >= 0) {
      return "success";
    }
    if (status === "delayed" || status.indexOf("איחור") >= 0) {
      return "warning";
    }
    if (status === "failed") {
      return "high";
    }
    return "neutral";
  }

  function sourceStatusLabel(status) {
    if (status === "healthy") {
      return "תקין";
    }
    if (status === "delayed") {
      return "באיחור";
    }
    if (status === "failed") {
      return "כשל";
    }
    return status || "לא זמין";
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
        if (response.role !== "admin") {
          App.State.save({ session: { authenticated: false, role: "user", email: null, userId: null } });
          $("#admin-login-errors").html('<div class="rounded-2xl border border-warning/20 bg-amber-50 px-4 py-3 text-warning">לחשבון הזה אין הרשאת אדמין.</div>');
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
      var overview = admin && admin.metrics ? admin : null;
      var metrics = overview ? overview.metrics : (admin.dashboard && admin.dashboard.stats) || [];
      var wizardSeries = overview ? seriesFromApi(overview.wizard_usage_last_30_days) : [];
      var helpSeries = overview ? seriesFromApi(overview.help_requests_last_30_days) : [];
      var dataSources = overview ? overview.data_sources : (admin.marketData && admin.marketData.sources) || [];
      var users = overview ? overview.users : (admin.users && admin.users.rows) || [];

      if (!wizardSeries.length) {
        wizardSeries = buildSeries(18, 22, 4);
      }
      if (!helpSeries.length) {
        helpSeries = buildSeries(4, 10, 2);
      }

      users = users.map(function (row) {
        return {
          id: row.id,
          username: row.username || row.name,
          email: row.email,
          phone: row.phone_number || row.phone,
          status: row.status,
          role: row.role,
          created_at: row.created_at,
          locked: row.status === "locked" || row.locked
        };
      });
      var searchTerm = "";
      var statusFilter = "all";

      function filteredUsers() {
        return users.filter(function (row) {
          var statusMatch = statusFilter === "all" ? true : row.status === statusFilter;
          var haystack = [row.username, row.email, row.phone].join(" ").toLowerCase();
          var searchMatch = !searchTerm || haystack.indexOf(searchTerm.toLowerCase()) >= 0;
          return statusMatch && searchMatch;
        });
      }

      function statusLabel(status) {
        if (status === "active") {
          return "פעיל";
        }
        if (status === "pending") {
          return "בהמתנה";
        }
        if (status === "locked") {
          return "נעול";
        }
        return status || "לא זמין";
      }

      function statusTone(status) {
        if (status === "active") {
          return "success";
        }
        if (status === "pending") {
          return "warning";
        }
        if (status === "locked") {
          return "high";
        }
        return "neutral";
      }

      function roleLabel(role) {
        return role === "admin" ? "אדמין" : "משתמש";
      }

      function lastUpdateTime() {
        if (!dataSources || !dataSources.length) {
          return "לא זמין";
        }
        var latest = null;
        dataSources.forEach(function (source) {
          if (source.last_success_at) {
            var date = new Date(source.last_success_at);
            if (!latest || date > latest) {
              latest = date;
            }
          }
        });
        return latest ? App.Format.shortDateTime(latest.toISOString()) : "לא זמין";
      }

      function renderAdminPage() {
        root.innerHTML = [
          '<section class="mb-6 rounded-[28px] border border-line bg-white p-6 shadow-soft"><h1 class="text-3xl font-extrabold text-ink">תפעול ומעקב אתר</h1><p class="mt-3 text-sm leading-7 text-slateText">עמוד אחד שמרכז פעילות שוטפת, שימוש באשף, בקשות עזרה, סטטוס מקורות נתונים וטבלת משתמשים.</p></section>',
          '<section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">' + (metrics.length ? metrics.map(adminStatCard).join("") : "") + "</section>",
          '<section class="mt-6 rounded-[28px] border border-line bg-white p-6 shadow-soft"><div class="grid gap-6 xl:grid-cols-2">' +
            lineChart("שימוש באשף ב-30 הימים האחרונים", "מספר ההפעלות היומי של האשף החינמי.", wizardSeries, "#123b6b", "#123b6b") +
            lineChart("בקשות עזרה ב-30 הימים האחרונים", "מספר פניות שנוצרו לאחר אישור עניין או בקשת עזרה.", helpSeries, "#d97706", "#d97706") +
          "</div></section>",
          '<section class="mt-6 rounded-[28px] border border-line bg-white p-6 shadow-soft"><div class="grid gap-6 lg:grid-cols-[0.8fr,1.2fr] lg:items-start"><div><h2 class="text-2xl font-bold text-ink">מקורות נתונים</h2><p class="mt-3 text-sm leading-7 text-slateText">סטטוס עדכון אחרון לכל מקור שוק שמזין את ההמלצות.</p><div class="mt-5 rounded-[24px] border border-line bg-surface p-5"><p class="text-sm font-semibold text-slateText">עדכון מערכת אחרון</p><p class="mt-3 text-3xl font-extrabold text-ink">' + lastUpdateTime() + '</p><div class="mt-3">' + App.UI.badge("success", "תקין") + "</div></div></div>" +
            App.UI.table({
              columns: [
                { label: "מקור", key: "source" },
                { label: "סטטוס", render: function (row) { return App.UI.badge(sourceTone(row.status), sourceStatusLabel(row.status)); } },
                { label: "עודכן לאחרונה", key: "updated" }
              ],
              rows: dataSources.map(function (source) {
                return {
                  source: source.display_name || source.source,
                  status: source.status,
                  updated: source.last_success_at ? App.Format.shortDateTime(source.last_success_at) : "לא זמין"
                };
              })
            }) +
          "</div></section>",
          '<section class="mt-6 rounded-[28px] border border-line bg-white p-6 shadow-soft"><div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"><div><h2 class="text-2xl font-bold text-ink">טבלת משתמשים</h2><p class="mt-3 text-sm leading-7 text-slateText">חיפוש, סינון ונעילת משתמשים מהעמוד הראשי.</p></div><div class="grid gap-3 sm:grid-cols-2"><label class="block"><span class="mb-2 block text-xs font-bold uppercase tracking-[0.18em] text-slateText">חיפוש</span><input type="search" data-admin-search class="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink" placeholder="שם, אימייל, טלפון" value="' + App.Helpers.escapeHtml(searchTerm) + '" /></label><label class="block"><span class="mb-2 block text-xs font-bold uppercase tracking-[0.18em] text-slateText">סטטוס</span><select data-admin-status class="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink"><option value="all"' + (statusFilter === "all" ? " selected" : "") + '>הכל</option><option value="active"' + (statusFilter === "active" ? " selected" : "") + '>פעיל</option><option value="pending"' + (statusFilter === "pending" ? " selected" : "") + '>בהמתנה</option><option value="locked"' + (statusFilter === "locked" ? " selected" : "") + '>נעול</option></select></label></div></div><div class="mt-5">' +
            App.UI.table({
              columns: [
                { label: "שם משתמש", key: "username" },
                { label: "אימייל", key: "email" },
                { label: "טלפון", key: "phone" },
                { label: "סטטוס", render: function (row) { return App.UI.badge(statusTone(row.status), statusLabel(row.status)); } },
                { label: "תפקיד", render: function (row) { return roleLabel(row.role); } },
                { label: "נוצר", render: function (row) { return row.created_at ? App.Format.shortDateTime(row.created_at) : "לא זמין"; } },
                { label: "פעולה", render: function (row) { return row.locked ? '<span class="text-xs font-semibold text-slateText">נעול</span>' : '<button type="button" class="rounded-full border border-line px-4 py-2 text-xs font-semibold text-ink hover:border-brand-600 hover:text-brand-600" data-lock-user="' + row.id + '">נעילה</button>'; } }
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
        var id = $(this).data("lock-user");
        App.MockApi.lockUser(id).then(function () {
          users = users.map(function (row) {
            if (row.id !== id) {
              return row;
            }
            return $.extend({}, row, { locked: true, status: "locked" });
          });
          renderAdminPage();
        });
      });
    });
  };
})();
