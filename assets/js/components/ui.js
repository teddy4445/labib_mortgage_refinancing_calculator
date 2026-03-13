(function () {
  window.App = window.App || {};

  function badge(tone, label) {
    return '<span class="inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold ' + App.Helpers.severityClasses(tone) + '">' + label + "</span>";
  }

  function metricCard(item) {
    return [
      '<article class="rounded-[24px] border border-line bg-white p-5 shadow-soft">',
      '  <p class="text-sm font-semibold text-slateText">' + item.label + "</p>",
      '  <p class="mt-3 text-3xl font-extrabold tabular-nums text-ink">' + item.value + "</p>",
      (item.note ? '  <p class="mt-2 text-sm text-slateText">' + item.note + "</p>" : ""),
      (item.badge ? '  <div class="mt-3">' + badge(item.badge.tone, item.badge.label) + "</div>" : ""),
      "</article>"
    ].join("");
  }

  function table(config) {
    var header = config.columns.map(function (column) {
      return '<th class="px-4 py-3 text-start text-xs font-bold uppercase tracking-[0.18em] text-slateText">' + column.label + "</th>";
    }).join("");

    var rows = (config.rows || []).map(function (row) {
      var cells = config.columns.map(function (column) {
        var value = typeof column.render === "function" ? column.render(row) : row[column.key];
        return '<td class="border-t border-line px-4 py-4 align-top text-sm text-ink">' + value + "</td>";
      }).join("");
      return "<tr>" + cells + "</tr>";
    }).join("");

    if (!rows) {
      rows = '<tr><td colspan="' + config.columns.length + '" class="border-t border-line px-4 py-8 text-center text-sm text-slateText">' + (config.empty || "אין נתונים להצגה") + "</td></tr>";
    }

    return [
      '<div class="table-scroll rounded-[24px] border border-line bg-white shadow-soft">',
      '  <table class="w-full border-collapse">',
      "    <thead><tr>" + header + "</tr></thead>",
      "    <tbody>" + rows + "</tbody>",
      "  </table>",
      "</div>"
    ].join("");
  }

  function tabs(config) {
    var buttons = config.tabs.map(function (tab, index) {
      var active = tab.key === config.active || (!config.active && index === 0);
      return '<button type="button" class="rounded-full px-4 py-2 text-sm font-semibold ' + (active ? "bg-brand-600 text-white" : "bg-surface text-slateText hover:bg-brand-50 hover:text-brand-600") + '" data-tab-button="' + tab.key + '">' + tab.label + "</button>";
    }).join("");

    var panels = config.tabs.map(function (tab, index) {
      var active = tab.key === config.active || (!config.active && index === 0);
      return '<section class="tab-panel" data-tab-panel="' + tab.key + '"' + (active ? "" : ' hidden="hidden"') + ">" + tab.content + "</section>";
    }).join("");

    return [
      '<div class="rounded-[28px] border border-line bg-white shadow-soft" data-tab-group>',
      '  <div class="border-b border-line p-4"><div class="flex flex-wrap gap-2">' + buttons + "</div></div>",
      '  <div class="p-6">' + panels + "</div>",
      "</div>"
    ].join("");
  }

  function accordion(items) {
    return items.map(function (item, index) {
      var open = index === 0;
      return [
        '<div class="rounded-[24px] border border-line bg-white shadow-soft" data-accordion-item>',
        '  <button type="button" class="flex w-full items-center justify-between gap-4 px-6 py-5 text-start" data-accordion-button>',
        '    <span class="text-lg font-bold text-ink">' + item.question + "</span>",
        '    <span class="text-brand-600">' + (open ? "−" : "+") + "</span>",
        "  </button>",
        '  <div class="accordion-panel px-6 pb-6 text-sm leading-7 text-slateText"' + (open ? "" : ' hidden="hidden"') + ">" + item.answer + "</div>",
        "</div>"
      ].join("");
    }).join("");
  }

  function chartPlaceholder(title, items) {
    return [
      '<section class="rounded-[24px] border border-line bg-white p-6 shadow-soft">',
      '  <div class="flex items-center justify-between gap-4">',
      '    <div><h3 class="text-lg font-bold text-ink">' + title + '</h3><p class="mt-1 text-sm text-slateText">המחשה ויזואלית קלה למעבר נתונים ל-API או לספריית גרפים בהמשך.</p></div>',
      '    <span class="rounded-full border border-line px-3 py-1 text-xs font-semibold text-slateText">placeholder chart</span>',
      "  </div>",
      '  <div class="chart-bars mt-6 space-y-4">' + items.map(function (item) {
        return '<div><div class="mb-2 flex items-center justify-between text-sm text-slateText"><span>' + item.label + "</span><span>" + item.value + '</span></div><span class="' + item.className + '" style="width:' + item.width + '%"></span></div>';
      }).join("") + "</div>",
      "</section>"
    ].join("");
  }

  function modalMarkup() {
    return [
      '<div class="modal fixed inset-0 z-50 flex items-center justify-center bg-ink/55 p-4" hidden="hidden" data-modal>',
      '  <div class="w-full max-w-2xl rounded-[28px] bg-white p-6 shadow-panel">',
      '    <div class="flex items-start justify-between gap-4">',
      '      <div><h3 class="text-2xl font-bold text-ink" data-modal-title></h3><p class="mt-2 text-sm text-slateText" data-modal-subtitle></p></div>',
      '      <button type="button" class="rounded-full border border-line px-3 py-2 text-sm font-semibold text-slateText" data-modal-close>סגור</button>',
      "    </div>",
      '    <div class="mt-6" data-modal-body></div>',
      "  </div>",
      "</div>"
    ].join("");
  }

  function compactPageActions(actions) {
    if (!actions) {
      return "";
    }

    return [
      '<section class="mb-6 flex flex-wrap gap-3">',
      actions,
      "</section>"
    ].join("");
  }

  App.UI = {
    badge: badge,
    metricCard: metricCard,
    table: table,
    tabs: tabs,
    accordion: accordion,
    chartPlaceholder: chartPlaceholder,
    renderPageHeader: function (config) {
      var layout = document.body.dataset.layout || "public";

      if (layout === "app" || layout === "admin") {
        return compactPageActions(config.actions || "");
      }

      return [
        '<section class="mb-8 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">',
        "  <div>",
        '    <p class="text-xs font-bold uppercase tracking-[0.22em] text-slateText">' + (config.eyebrow || "mortgage monitor") + "</p>",
        '    <h1 class="mt-3 text-4xl font-extrabold leading-tight text-ink lg:text-5xl">' + config.title + "</h1>",
        '    <p class="mt-3 max-w-3xl text-base leading-7 text-slateText">' + config.description + "</p>",
        "  </div>",
        '  <div class="flex flex-wrap gap-3">' + (config.actions || "") + "</div>",
        "</section>"
      ].join("");
    },
    mountModalRoot: function () {
      var root = document.querySelector("[data-modal-root]");
      if (root && !root.querySelector("[data-modal]")) {
        root.innerHTML = modalMarkup();
      }
    },
    showModal: function (title, body, subtitle) {
      App.UI.mountModalRoot();
      var modal = document.querySelector("[data-modal]");
      if (!modal) {
        return;
      }
      modal.querySelector("[data-modal-title]").innerHTML = title;
      modal.querySelector("[data-modal-subtitle]").innerHTML = subtitle || "";
      modal.querySelector("[data-modal-body]").innerHTML = body;
      modal.hidden = false;
    },
    init: function () {
      $(document).on("click", "[data-tab-button]", function () {
        var button = $(this);
        var tabKey = button.data("tab-button");
        var group = button.closest("[data-tab-group]");
        group.find("[data-tab-button]").removeClass("bg-brand-600 text-white").addClass("bg-surface text-slateText");
        button.removeClass("bg-surface text-slateText").addClass("bg-brand-600 text-white");
        group.find("[data-tab-panel]").attr("hidden", true);
        group.find('[data-tab-panel="' + tabKey + '"]').removeAttr("hidden");
      });

      $(document).on("click", "[data-accordion-button]", function () {
        var item = $(this).closest("[data-accordion-item]");
        var panel = item.find(".accordion-panel");
        var icon = $(this).find("span:last");
        var hidden = panel.attr("hidden") !== undefined;
        panel.attr("hidden", hidden ? null : "hidden");
        icon.text(hidden ? "−" : "+");
      });

      $(document).on("click", "[data-modal-close]", function () {
        $("[data-modal]").attr("hidden", true);
      });

      $(document).on("click", "[data-modal]", function (event) {
        if (event.target === this) {
          $(this).attr("hidden", true);
        }
      });
    }
  };
})();
