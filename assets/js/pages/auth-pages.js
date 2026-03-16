(function () {
  window.App = window.App || {};
  App.Pages = App.Pages || {};

  function authShell(config) {
    return [
      '<section class="mx-auto max-w-[620px]">',
      '  <div class="auth-card rounded-[36px] border border-line p-8 sm:p-10">',
      '    <div id="auth-state"></div>',
      '    <p class="text-xs font-bold uppercase tracking-[0.22em] text-slateText">' + config.eyebrow + "</p>",
      '    <h1 class="mt-4 text-4xl font-extrabold leading-tight text-ink">' + config.title + "</h1>",
      '    <p class="mt-4 text-base leading-8 text-slateText">' + config.description + "</p>",
      '    <div class="mt-8">' + config.form + "</div>",
      "  </div>",
      "</section>"
    ].join("");
  }

  function emailValid(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || ""));
  }

  function passwordStrong(value) {
    return String(value || "").length >= 8;
  }

  function phoneValid(value) {
    return /^[0-9+\-\s()]{9,}$/.test(String(value || ""));
  }

  App.Pages.signup = function (root) {
    root.innerHTML = authShell({
      eyebrow: "signup",
      title: "פותחים חשבון לשמירת תוצאות והתראות",
      description: "אפשר להתחיל מהאשף החינמי גם בלי התחברות מוקדמת. דף זה מיועד למי שרוצה ליצור חשבון ישירות ולשמור את הניתוחים האישיים.",
      highlights: [
        "שמירת ניתוחים, התראות ובקשות עניין במקום אחד.",
        "מעקב שוטף אחר הזדמנויות מחזור והסברים על break-even.",
        "המערכת מציגה המלצות AI-driven, אך אינה מחליפה ייעוץ מקצועי."
      ],
      form: [
        '<form id="signup-form" class="space-y-5">',
        '  <div><label class="mb-2 block text-sm font-semibold text-ink">אימייל</label><input name="email" type="email" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm" placeholder="name@example.com" /></div>',
        '  <div><label class="mb-2 block text-sm font-semibold text-ink">טלפון</label><input name="phone" type="tel" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm" placeholder="050-555-0182" /></div>',
        '  <div><label class="mb-2 block text-sm font-semibold text-ink">סיסמה</label><input name="password" type="password" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm" placeholder="לפחות 8 תווים" /></div>',
        '  <div><label class="mb-2 block text-sm font-semibold text-ink">אימות סיסמה</label><input name="confirmPassword" type="password" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm" placeholder="הזן/י שוב" /></div>',
        '  <label class="flex items-start gap-3 rounded-2xl border border-line p-4 text-sm text-slateText"><input type="checkbox" name="terms" class="mt-1 h-4 w-4 rounded border-line text-brand-600 focus:ring-brand-600" /><span>אני מאשר/ת את תנאי השימוש.</span></label>',
        '  <label class="flex items-start gap-3 rounded-2xl border border-line p-4 text-sm text-slateText"><input type="checkbox" name="privacy" class="mt-1 h-4 w-4 rounded border-line text-brand-600 focus:ring-brand-600" /><span>אני מאשר/ת את מדיניות הפרטיות והחזקת הנתונים לצורך הניתוח.</span></label>',
        '  <div id="signup-errors" class="space-y-2 text-sm"></div>',
        '  <button type="submit" class="w-full rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">פתיחת חשבון</button>',
        '  <p class="text-center text-sm text-slateText">אפשר גם להתחיל מהאשף החינמי בלי הרשמה מוקדמת. <a class="font-bold text-brand-600" href="' + App.Helpers.link("pages/onboarding.html") + '">לפתיחת האשף</a></p>',
        '  <p class="text-center text-sm text-slateText">יש כבר חשבון? <a class="font-bold text-brand-600" href="' + App.Helpers.link("pages/login.html") + '">למסך הכניסה</a></p>',
        "</form>"
      ].join("")
    });

    $("#signup-form").on("submit", function (event) {
      event.preventDefault();
      var payload = {
        email: $(this).find('[name="email"]').val().trim(),
        phone: $(this).find('[name="phone"]').val().trim(),
        password: $(this).find('[name="password"]').val(),
        confirmPassword: $(this).find('[name="confirmPassword"]').val(),
        terms: $(this).find('[name="terms"]').is(":checked"),
        privacy: $(this).find('[name="privacy"]').is(":checked")
      };
      var errors = [];

      if (!emailValid(payload.email)) {
        errors.push("יש להזין כתובת אימייל תקינה.");
      }
      if (!phoneValid(payload.phone)) {
        errors.push("יש להזין מספר טלפון תקין.");
      }
      if (!passwordStrong(payload.password)) {
        errors.push("הסיסמה חייבת להכיל לפחות 8 תווים.");
      }
      if (payload.password !== payload.confirmPassword) {
        errors.push("אימות הסיסמה אינו תואם.");
      }
      if (!payload.terms || !payload.privacy) {
        errors.push("יש לאשר את תנאי השימוש ואת מדיניות הפרטיות.");
      }

      if (errors.length) {
        $("#signup-errors").html(errors.map(function (error) {
          return '<div class="rounded-2xl border border-danger/20 bg-red-50 px-4 py-3 text-danger">' + error + "</div>";
        }).join(""));
        return;
      }

      App.MockApi.signUp(payload).then(function (response) {
        if (!response.success) {
          var message = response.code === "email_taken"
            ? "האימייל כבר רשום במערכת. נסו להתחבר או השתמשו בכתובת אחרת."
            : "לא ניתן להשלים הרשמה כרגע. נסו שוב.";
          $("#signup-errors").html('<div class="rounded-2xl border border-danger/20 bg-red-50 px-4 py-3 text-danger">' + message + "</div>");
          return;
        }
        $("#auth-state").html('<div class="mb-5 rounded-2xl border border-success/20 bg-emerald-50 px-4 py-3 text-sm text-success">החשבון נפתח עבור ' + App.Helpers.escapeHtml(response.email) + ".</div>");
        $("#signup-form").replaceWith(
          '<div class="rounded-[28px] border border-line bg-surface p-6 text-center">' +
            '<h2 class="text-2xl font-bold text-ink">ההרשמה הושלמה</h2>' +
            '<p class="mt-3 text-sm leading-7 text-slateText">אפשר להמשיך למסך הכניסה או לעבור ישירות לכתב הוויתור ולהתחיל את האשף.</p>' +
            '<div class="mt-6 flex flex-wrap justify-center gap-3">' +
              '<a class="rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700" href="' + App.Helpers.link("pages/consent.html") + '">המשך לאשף</a>' +
              '<a class="rounded-full border border-line px-6 py-3 text-sm font-bold text-ink hover:border-brand-600 hover:text-brand-600" href="' + App.Helpers.link("pages/login.html") + '">כניסה לחשבון</a>' +
            "</div>" +
          "</div>"
        );
      });
    });
  };

  App.Pages.login = function (root) {
    root.innerHTML = authShell({
      eyebrow: "login",
      title: "כניסה לחשבון",
      description: "הכניסה מיועדת לצפייה בתוצאות, התראות ומעקב קיים. אפשר להמשיך גם ישירות לאשף החינמי אם עוד אין חשבון.",
      highlights: [
        "Password for demo: Secure123!.",
        "הכתובת locked@example.com תציג מצב נעילה.",
        "האשף החינמי פתוח גם ללא התחברות מוקדמת."
      ],
      form: [
        '<form id="login-form" class="space-y-5">',
        '  <div><label class="mb-2 block text-sm font-semibold text-ink">אימייל</label><input name="email" type="email" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm" placeholder="yael@example.com" value="yael@example.com" /></div>',
        '  <div><label class="mb-2 block text-sm font-semibold text-ink">סיסמה</label><input name="password" type="password" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm" placeholder="Secure123!" /></div>',
        '  <div class="flex items-center justify-between gap-3 text-sm"><label class="flex items-center gap-2 text-slateText"><input type="checkbox" name="remember" class="h-4 w-4 rounded border-line text-brand-600 focus:ring-brand-600" />זכור אותי</label><a class="font-semibold text-brand-600" href="' + App.Helpers.link("pages/forgot-password.html") + '">שכחתי סיסמה</a></div>',
        '  <div id="login-errors" class="space-y-2 text-sm"></div>',
        '  <button type="submit" class="w-full rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">כניסה</button>',
        '  <p class="text-center text-sm text-slateText">עוד אין חשבון? <a class="font-bold text-brand-600" href="' + App.Helpers.link("pages/onboarding.html") + '">התחלת האשף החינמי</a></p>',
        "</form>"
      ].join("")
    });

    $("#login-form").on("submit", function (event) {
      event.preventDefault();
      var payload = {
        email: $(this).find('[name="email"]').val().trim(),
        password: $(this).find('[name="password"]').val(),
        remember: $(this).find('[name="remember"]').is(":checked")
      };

      if (!emailValid(payload.email) || !payload.password) {
        $("#login-errors").html('<div class="rounded-2xl border border-danger/20 bg-red-50 px-4 py-3 text-danger">יש להזין אימייל וסיסמה.</div>');
        return;
      }

      App.MockApi.login(payload).then(function (response) {
        if (response.status === "invalid") {
          $("#login-errors").html('<div class="rounded-2xl border border-danger/20 bg-red-50 px-4 py-3 text-danger">פרטי ההתחברות אינם תואמים. בדקו את האימייל והסיסמה ונסו שוב.</div>');
          return;
        }

        if (response.status === "locked") {
          $("#login-errors").html('<div class="rounded-2xl border border-warning/20 bg-amber-50 px-4 py-3 text-warning">החשבון ננעל זמנית עקב ניסיונות כושלים מרובים. אפשר לאפס סיסמה או להמתין 15 דקות.</div>');
          return;
        }

        if (response.status === "error") {
          $("#login-errors").html('<div class="rounded-2xl border border-warning/20 bg-amber-50 px-4 py-3 text-warning">לא ניתן להתחבר כרגע. בדקו חיבור ונסו שוב.</div>');
          return;
        }

        $("#auth-state").html('<div class="mb-5 rounded-2xl border border-success/20 bg-emerald-50 px-4 py-3 text-sm text-success">הכניסה בוצעה בהצלחה. מעבירים אותך ללוח המחוונים.</div>');
        window.setTimeout(function () {
          window.location.href = response.redirect;
        }, 650);
      });
    });
  };

  App.Pages.forgotPassword = function (root) {
    root.innerHTML = authShell({
      eyebrow: "password recovery",
      title: "איפוס גישה לחשבון",
      description: "הזינו כתובת אימייל ותקבלו קישור לאיפוס. לצורך הדגמה, unknown@example.com יציג אזהרה על כתובת לא מוכרת.",
      highlights: [
        "המערכת אינה חושפת אם קיים חשבון אמיתי מחוץ לסביבת הדמו.",
        "אפשר לעבור מכאן ישירות למסך איפוס הסיסמה לצורך הדגמה.",
        "קישור ישן או לא תקף יפנה למצב expired."
      ],
      form: [
        '<form id="forgot-form" class="space-y-5">',
        '  <div><label class="mb-2 block text-sm font-semibold text-ink">אימייל</label><input name="email" type="email" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm" placeholder="name@example.com" /></div>',
        '  <div id="forgot-state" class="space-y-2 text-sm"></div>',
        '  <button type="submit" class="w-full rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">שליחת קישור איפוס</button>',
        '  <p class="text-center text-sm text-slateText"><a class="font-bold text-brand-600" href="' + App.Helpers.link("pages/login.html") + '">חזרה למסך הכניסה</a></p>',
        "</form>"
      ].join("")
    });

    $("#forgot-form").on("submit", function (event) {
      event.preventDefault();
      var email = $(this).find('[name="email"]').val().trim();
      if (!emailValid(email)) {
        $("#forgot-state").html('<div class="rounded-2xl border border-danger/20 bg-red-50 px-4 py-3 text-danger">יש להזין כתובת אימייל תקינה.</div>');
        return;
      }

      App.MockApi.forgotPassword(email).then(function (response) {
        if (response.status === "unknown") {
          $("#forgot-state").html('<div class="rounded-2xl border border-warning/20 bg-amber-50 px-4 py-3 text-warning">לא נמצאה כתובת מוכרת במערכת ההדגמה. בדקו את האיות או פנו לתמיכה.</div>');
          return;
        }

        if (response.status === "error") {
          $("#forgot-state").html('<div class="rounded-2xl border border-warning/20 bg-amber-50 px-4 py-3 text-warning">לא ניתן לשלוח קישור איפוס כרגע. נסו שוב.</div>');
          return;
        }

        $("#forgot-state").html(
          '<div class="rounded-2xl border border-success/20 bg-emerald-50 px-4 py-3 text-success">קישור איפוס נשלח ל-' + App.Helpers.escapeHtml(response.email) + '.</div>' +
          '<div class="rounded-2xl border border-line bg-surface px-4 py-3 text-slateText"><a class="font-bold text-brand-600" href="' + App.Helpers.link("pages/reset-password.html") + '">מעבר למסך איפוס סיסמה</a></div>'
        );
      });
    });
  };

  App.Pages.resetPassword = function (root) {
    var token = App.Helpers.queryParam("token") || "valid";
    var expired = token === "expired";

    root.innerHTML = authShell({
      eyebrow: "reset password",
      title: "בחירת סיסמה חדשה",
      description: expired ? "הקישור המבוקש כבר אינו פעיל. יש לבקש קישור חדש ולהתחיל מחדש." : "אפשר להגדיר סיסמה חדשה ולחזור למסך הכניסה. התאמה לא תקינה בין השדות תוצג ישירות בטופס.",
      highlights: expired ? [] : [
        "במצב הדגמה: ?token=expired יציג קישור שפג תוקפו.",
        "התאמת הסיסמאות נבדקת לפני השליחה.",
        "לאחר הצלחה אפשר לחזור ולהיכנס עם הסיסמה החדשה."
      ],
      form: expired ? (
        '<div class="rounded-[28px] border border-warning/20 bg-amber-50 p-6 text-warning">' +
          '<h2 class="text-2xl font-bold">תוקף הקישור פג</h2>' +
          '<p class="mt-3 text-sm leading-7">יש לבקש קישור חדש לאיפוס סיסמה. הקישור הקיים אינו פעיל עוד.</p>' +
          '<div class="mt-6"><a class="rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700" href="' + App.Helpers.link("pages/forgot-password.html") + '">לבקשת קישור חדש</a></div>' +
        "</div>"
      ) : [
        '<form id="reset-form" class="space-y-5">',
        '  <div><label class="mb-2 block text-sm font-semibold text-ink">סיסמה חדשה</label><input name="password" type="password" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm" placeholder="לפחות 8 תווים" /></div>',
        '  <div><label class="mb-2 block text-sm font-semibold text-ink">אימות סיסמה חדשה</label><input name="confirmPassword" type="password" class="w-full rounded-2xl border-line bg-white px-4 py-3 text-sm" placeholder="הזן/י שוב" /></div>',
        '  <div id="reset-state" class="space-y-2 text-sm"></div>',
        '  <button type="submit" class="w-full rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700">שמירת סיסמה חדשה</button>',
        '  <p class="text-center text-sm text-slateText"><a class="font-bold text-brand-600" href="' + App.Helpers.link("pages/login.html") + '">חזרה למסך הכניסה</a></p>',
        "</form>"
      ].join("")
    });

    if (!expired) {
      $("#reset-form").on("submit", function (event) {
        event.preventDefault();
        var payload = {
          token: token,
          password: $(this).find('[name="password"]').val(),
          confirmPassword: $(this).find('[name="confirmPassword"]').val()
        };

        if (!passwordStrong(payload.password)) {
          $("#reset-state").html('<div class="rounded-2xl border border-danger/20 bg-red-50 px-4 py-3 text-danger">הסיסמה צריכה להכיל לפחות 8 תווים.</div>');
          return;
        }

        App.MockApi.resetPassword(payload).then(function (response) {
          if (response.status === "mismatch") {
            $("#reset-state").html('<div class="rounded-2xl border border-danger/20 bg-red-50 px-4 py-3 text-danger">הסיסמאות אינן תואמות.</div>');
            return;
          }

          if (response.status === "expired") {
            $("#reset-state").html('<div class="rounded-2xl border border-warning/20 bg-amber-50 px-4 py-3 text-warning">תוקף הקישור פג. יש לבקש קישור חדש.</div>');
            return;
          }

          if (response.status === "error") {
            $("#reset-state").html('<div class="rounded-2xl border border-warning/20 bg-amber-50 px-4 py-3 text-warning">לא ניתן לעדכן סיסמה כרגע. נסו שוב.</div>');
            return;
          }

          $("#reset-form").replaceWith(
            '<div class="rounded-[28px] border border-success/20 bg-emerald-50 p-6 text-center text-success">' +
              '<h2 class="text-2xl font-bold">הסיסמה עודכנה בהצלחה</h2>' +
              '<p class="mt-3 text-sm leading-7">אפשר להיכנס כעת עם הסיסמה החדשה.</p>' +
              '<div class="mt-6"><a class="rounded-full bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-soft hover:bg-brand-700" href="' + App.Helpers.link("pages/login.html") + '">חזרה לכניסה</a></div>' +
            "</div>"
          );
        });
      });
    }
  };
})();
