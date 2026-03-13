(function () {
  window.App = window.App || {};

  App.bootstrap = function () {
    App.I18n.init().then(function () {
      App.Layout.init();
      App.UI.init();

      var contentRoot = document.querySelector("[data-page-content]");
      var pageKey = document.body.dataset.page;
      var pageRegistry = App.Pages || {};

      if (pageRegistry[pageKey] && contentRoot) {
        pageRegistry[pageKey](contentRoot);
      }

      App.I18n.apply(document.documentElement);
      App.I18n.observe();
    });
  };

  document.addEventListener("DOMContentLoaded", App.bootstrap);
})();
