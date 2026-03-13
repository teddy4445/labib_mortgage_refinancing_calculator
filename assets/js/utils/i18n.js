(function () {
  window.App = window.App || {};

  var storageKey = "mortgage-monitor-language";
  var activeLanguage = "he";
  var bundle = {
    meta: {
      code: "he",
      dir: "rtl",
      locale: "he-IL",
      nativeName: "עברית"
    },
    strings: {}
  };
  var supported = {
    he: { code: "he", dir: "rtl", locale: "he-IL", nativeName: "עברית" },
    en: { code: "en", dir: "ltr", locale: "en-US", nativeName: "English" },
    ru: { code: "ru", dir: "ltr", locale: "ru-RU", nativeName: "Русский" },
    ar: { code: "ar", dir: "rtl", locale: "ar", nativeName: "العربية" }
  };
  var originalText = new WeakMap();
  var originalAttrs = new WeakMap();
  var observer;
  var isApplying = false;

  function basePath() {
    return document.body && document.body.dataset.basepath ? document.body.dataset.basepath : ".";
  }

  function resolve(path) {
    var base = basePath();
    return base === "." ? path : base + "/" + path;
  }

  function detectLanguage() {
    var stored = window.localStorage.getItem(storageKey);
    if (stored && supported[stored]) {
      return stored;
    }

    var browser = (navigator.language || "he").toLowerCase();
    if (browser.indexOf("ar") === 0) {
      return "ar";
    }
    if (browser.indexOf("ru") === 0) {
      return "ru";
    }
    if (browser.indexOf("en") === 0) {
      return "en";
    }
    return "he";
  }

  function setDocumentMeta() {
    var meta = bundle.meta || supported[activeLanguage] || supported.he;
    document.documentElement.lang = meta.code;
    document.documentElement.dir = meta.dir;
    document.body.setAttribute("dir", meta.dir);
    document.body.dataset.lang = meta.code;
  }

  function translationEntries() {
    return Object.keys(bundle.strings || {}).sort(function (a, b) {
      return b.length - a.length;
    }).map(function (key) {
      return [key, bundle.strings[key]];
    });
  }

  function translateValue(value) {
    if (!value) {
      return value;
    }

    var result = String(value);
    translationEntries().forEach(function (entry) {
      if (!entry[0]) {
        return;
      }
      result = result.split(entry[0]).join(entry[1]);
    });
    return result;
  }

  function rememberOriginalText(node) {
    if (!originalText.has(node)) {
      originalText.set(node, node.nodeValue);
    }
    return originalText.get(node);
  }

  function rememberOriginalAttr(element, attr) {
    var attrs = originalAttrs.get(element);
    if (!attrs) {
      attrs = {};
      originalAttrs.set(element, attrs);
    }
    if (attrs[attr] === undefined) {
      attrs[attr] = element.getAttribute(attr);
    }
    return attrs[attr];
  }

  function translateTextNode(node) {
    if (!node || !node.nodeValue || !node.nodeValue.trim()) {
      return;
    }
    var source = rememberOriginalText(node);
    node.nodeValue = translateValue(source);
  }

  function translateAttributes(element) {
    ["placeholder", "title", "aria-label"].forEach(function (attr) {
      if (element.hasAttribute && element.hasAttribute(attr)) {
        var original = rememberOriginalAttr(element, attr);
        element.setAttribute(attr, translateValue(original));
      }
    });
  }

  function apply(root) {
    var node = root || document.documentElement;
    if (!node) {
      return;
    }

    if (isApplying) {
      return;
    }

    isApplying = true;
    try {
      if (node.nodeType === Node.TEXT_NODE) {
        translateTextNode(node);
        return;
      }

      if (node.nodeType === Node.ELEMENT_NODE) {
        translateAttributes(node);
      }

      var walker = document.createTreeWalker(node, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {
        acceptNode: function (candidate) {
          if (candidate.nodeType === Node.TEXT_NODE) {
            var parent = candidate.parentElement;
            if (!parent || /SCRIPT|STYLE|NOSCRIPT/.test(parent.tagName)) {
              return NodeFilter.FILTER_REJECT;
            }
            return NodeFilter.FILTER_ACCEPT;
          }
          if (/SCRIPT|STYLE|NOSCRIPT/.test(candidate.tagName)) {
            return NodeFilter.FILTER_REJECT;
          }
          return NodeFilter.FILTER_ACCEPT;
        }
      });

      while (walker.nextNode()) {
        var current = walker.currentNode;
        if (current.nodeType === Node.TEXT_NODE) {
          translateTextNode(current);
        } else {
          translateAttributes(current);
        }
      }

      document.title = translateValue(document.title);
    } finally {
      isApplying = false;
    }
  }

  function observe() {
    if (observer) {
      return;
    }

    observer = new MutationObserver(function (mutations) {
      if (isApplying) {
        return;
      }

      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          apply(node);
        });
      });
    });

    observer.observe(document.documentElement, {
      subtree: true,
      childList: true
    });
  }

  function languageOptionsMarkup() {
    return Object.keys(supported).map(function (code) {
      var language = supported[code];
      return '<option value="' + code + '"' + (code === activeLanguage ? " selected" : "") + ">" + language.nativeName + "</option>";
    }).join("");
  }

  App.I18n = {
    init: function () {
      activeLanguage = detectLanguage();

      return fetch(resolve("assets/i18n/" + activeLanguage + ".json"))
        .then(function (response) {
          if (!response.ok) {
            throw new Error("i18n bundle not found");
          }
          return response.json();
        })
        .then(function (json) {
          bundle = json;
          setDocumentMeta();
          return json;
        })
        .catch(function () {
          activeLanguage = "he";
          bundle = {
            meta: supported.he,
            strings: {}
          };
          setDocumentMeta();
          return bundle;
        });
    },
    apply: apply,
    observe: observe,
    setLanguage: function (nextLanguage) {
      if (!supported[nextLanguage]) {
        return;
      }
      window.localStorage.setItem(storageKey, nextLanguage);
      window.location.reload();
    },
    current: function () {
      return activeLanguage;
    },
    meta: function () {
      return bundle.meta || supported[activeLanguage] || supported.he;
    },
    languages: function () {
      return supported;
    },
    t: function (value, fallback) {
      return translateValue(value || fallback || "");
    },
    translate: translateValue,
    optionsMarkup: languageOptionsMarkup
  };
})();
