(function () {
  window.App = window.App || {};
  var storageKey = "mortgage-monitor-state";

  function defaults() {
    return App.Helpers.deepClone(window.MockData.initialState);
  }

  function load() {
    var raw = window.localStorage.getItem(storageKey);
    if (!raw) {
      return defaults();
    }

    try {
      return $.extend(true, {}, defaults(), JSON.parse(raw));
    } catch (error) {
      return defaults();
    }
  }

  function write(state) {
    window.localStorage.setItem(storageKey, JSON.stringify(state));
    return state;
  }

  App.State = {
    load: load,
    save: function (partial) {
      var current = load();
      var next = $.extend(true, {}, current, partial || {});
      return write(next);
    },
    replace: write,
    dismissAlert: function (alertId) {
      var current = load();
      if (current.alertsDismissed.indexOf(alertId) === -1) {
        current.alertsDismissed.push(alertId);
      }
      return write(current);
    },
    reset: function () {
      return write(defaults());
    }
  };
})();
