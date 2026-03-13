(function () {
  window.App = window.App || {};
  var uid = 0;

  App.Helpers = {
    deepClone: function (value) {
      return JSON.parse(JSON.stringify(value));
    },
    basePath: function () {
      return document.body.dataset.basepath || ".";
    },
    link: function (path) {
      var base = App.Helpers.basePath();
      return base === "." ? path : base + "/" + path;
    },
    queryParam: function (key) {
      return new URLSearchParams(window.location.search).get(key);
    },
    uid: function (prefix) {
      uid += 1;
      return (prefix || "id") + "-" + uid;
    },
    escapeHtml: function (text) {
      return String(text || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    },
    sumBy: function (items, key) {
      return (items || []).reduce(function (sum, item) {
        return sum + Number(item[key] || 0);
      }, 0);
    },
    severityLabel: function (severity) {
      return {
        high: "גבוהה",
        medium: "בינונית",
        low: "נמוכה"
      }[severity] || severity;
    },
    severityClasses: function (severity) {
      return {
        high: "bg-red-50 text-danger border-danger/20",
        medium: "bg-amber-50 text-warning border-warning/20",
        low: "bg-sky-50 text-accent border-accent/20",
        success: "bg-emerald-50 text-success border-success/20",
        warning: "bg-amber-50 text-warning border-warning/20"
      }[severity] || "bg-slate-100 text-slateText border-line";
    },
    riskTone: function (value) {
      if (value >= 70) {
        return "high";
      }
      if (value >= 50) {
        return "medium";
      }
      return "low";
    }
  };
})();
