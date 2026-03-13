(function () {
  window.App = window.App || {};

  function locale() {
    return window.App && App.I18n ? App.I18n.meta().locale : "he-IL";
  }

  App.Format = {
    currency: function (value) {
      return new Intl.NumberFormat(locale(), {
        style: "currency",
        currency: "ILS",
        maximumFractionDigits: 0
      }).format(Number(value || 0));
    },
    number: function (value) {
      return new Intl.NumberFormat(locale()).format(Number(value || 0));
    },
    percent: function (value, digits) {
      var precision = typeof digits === "number" ? digits : 2;
      return Number(value || 0).toFixed(precision) + "%";
    },
    date: function (value) {
      if (!value) {
        return window.App && App.I18n ? App.I18n.translate("לא זמין") : "לא זמין";
      }

      return new Intl.DateTimeFormat(locale(), {
        day: "2-digit",
        month: "long",
        year: "numeric"
      }).format(new Date(value));
    },
    shortDateTime: function (value) {
      if (!value) {
        return window.App && App.I18n ? App.I18n.translate("לא זמין") : "לא זמין";
      }

      return new Intl.DateTimeFormat(locale(), {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      }).format(new Date(value));
    },
    relativeMonths: function (value) {
      return App.Format.number(value) + " " + (window.App && App.I18n ? App.I18n.translate("חודשים") : "חודשים");
    }
  };
})();
