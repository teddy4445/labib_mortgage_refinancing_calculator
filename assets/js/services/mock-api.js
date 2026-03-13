(function () {
  window.App = window.App || {};

  function delay(payload) {
    return new Promise(function (resolve) {
      window.setTimeout(function () {
        resolve(App.Helpers.deepClone(payload));
      }, 180);
    });
  }

  function deriveMortgage() {
    var mortgage = App.Helpers.deepClone(window.MockData.mortgage);
    var state = App.State.load();
    var onboarding = state.onboarding;

    if (onboarding) {
      mortgage.lender = onboarding.lender.lenderName || mortgage.lender;
      mortgage.originationDate = onboarding.lender.originationDate || mortgage.originationDate;
      mortgage.originalAmount = Number(onboarding.lender.originalAmount || mortgage.originalAmount);
      mortgage.propertyValue = Number(onboarding.basic.propertyValue || mortgage.propertyValue);
      mortgage.currentMonthlyPayment = Number(onboarding.basic.currentMonthlyPayment || mortgage.currentMonthlyPayment);
      mortgage.remainingTermMonths = Number(onboarding.basic.remainingTermMonths || mortgage.remainingTermMonths);
      mortgage.tracks = onboarding.tracks.slice();
      mortgage.outstandingBalance = App.Helpers.sumBy(mortgage.tracks, "outstandingBalance");
      mortgage.refinanceCosts = {
        prepaymentFee: Number(onboarding.costs.prepaymentFee || 0),
        legalFee: Number(onboarding.costs.legalFee || 0),
        appraisal: Number(onboarding.costs.appraisal || 0),
        registration: Number(onboarding.costs.registration || 0),
        advisor: Number(onboarding.costs.advisor || 0)
      };
      mortgage.preferences = {
        holdingPeriodYears: onboarding.preferences.holdingPeriodYears,
        riskTolerance: onboarding.preferences.riskTolerance,
        paymentPreference: onboarding.preferences.goal,
        inflationAversion: onboarding.preferences.inflationAversion,
        resetRiskAversion: onboarding.preferences.resetRiskAversion
      };
    }

    return mortgage;
  }

  function deriveDashboard() {
    var mortgage = deriveMortgage();
    var dashboard = App.Helpers.deepClone(window.MockData.dashboard);
    var fees = mortgage.refinanceCosts.prepaymentFee + mortgage.refinanceCosts.legalFee + mortgage.refinanceCosts.appraisal + mortgage.refinanceCosts.registration + mortgage.refinanceCosts.advisor;
    var projectedReduction = Math.max(480, Math.round(mortgage.currentMonthlyPayment * 0.085));

    dashboard.estimatedRefinancePayment = Math.max(mortgage.currentMonthlyPayment - projectedReduction, 5400);
    dashboard.projectedNetSavings = Math.max(62000, Math.round(projectedReduction * Math.min(mortgage.preferences.holdingPeriodYears || 8, 10) * 12 - fees * 1.2));
    dashboard.breakEvenMonths = Math.max(11, Math.round(fees / Math.max(projectedReduction, 1)));
    dashboard.currentMonthlyPayment = mortgage.currentMonthlyPayment;
    dashboard.lastAnalysisTime = new Date().toISOString();

    if (dashboard.breakEvenMonths <= 14) {
      dashboard.recommendation = {
        headline: "מומלץ לפעול כעת למחזור חלקי",
        tone: "success",
        reason: "נקודת האיזון קצרה והפחתת הסיכון המסלולי גבוהה."
      };
      dashboard.urgency = {
        label: "דחיפות גבוהה",
        description: "שילוב של חיסכון חודשי משמעותי וסיכון ריבית פעיל."
      };
    }

    return dashboard;
  }

  function getUpfrontCosts(mortgage) {
    return mortgage.refinanceCosts.prepaymentFee +
      mortgage.refinanceCosts.legalFee +
      mortgage.refinanceCosts.appraisal +
      mortgage.refinanceCosts.registration +
      mortgage.refinanceCosts.advisor;
  }

  App.MockApi = {
    getLandingData: function () {
      return delay(window.MockData.landing);
    },
    getMortgage: function () {
      return delay(deriveMortgage());
    },
    getDashboard: function () {
      return delay(deriveDashboard());
    },
    getAnalysis: function () {
      var mortgage = deriveMortgage();
      var dashboard = deriveDashboard();
      var analysis = App.Helpers.deepClone(window.MockData.analysis);
      analysis.keepCurrent.monthlyPayment = mortgage.currentMonthlyPayment;
      analysis.refinanceNow.monthlyPayment = dashboard.estimatedRefinancePayment;
      analysis.refinanceNow.breakEvenMonths = dashboard.breakEvenMonths;
      analysis.refinanceNow.projectedSavings = dashboard.projectedNetSavings;
      analysis.refinanceNow.upfrontCost = getUpfrontCosts(mortgage);
      return delay(analysis);
    },
    getPartialRefinance: function () {
      return delay(window.MockData.partialRefinance);
    },
    getScenarios: function () {
      return delay(window.MockData.scenarios);
    },
    getAlerts: function () {
      var alerts = App.Helpers.deepClone(window.MockData.alerts);
      var dismissed = App.State.load().alertsDismissed || [];
      alerts.active = alerts.active.filter(function (item) {
        return dismissed.indexOf(item.id) === -1;
      });
      alerts.dismissed = alerts.dismissed.concat(window.MockData.alerts.active.filter(function (item) {
        return dismissed.indexOf(item.id) !== -1;
      }));
      return delay(alerts);
    },
    getProfile: function () {
      return delay(App.State.load().profile);
    },
    updateProfile: function (profile) {
      App.State.save({ profile: profile });
      return delay({ success: true });
    },
    updateNotifications: function (notifications) {
      App.State.save({ notifications: notifications });
      return delay({ success: true });
    },
    signUp: function (payload) {
      App.State.save({
        profile: $.extend({}, App.State.load().profile, {
          phone: payload.phone || App.State.load().profile.phone,
          username: payload.email || App.State.load().profile.username
        }),
        session: {
          authenticated: false,
          role: "user",
          email: payload.email
        }
      });
      return delay({
        success: true,
        email: payload.email
      });
    },
    login: function (payload) {
      var status = "success";
      if (payload.email === "locked@example.com") {
        status = "locked";
      } else if (payload.password !== "Secure123!") {
        status = "invalid";
      }

      if (status === "success") {
        App.State.save({
          session: {
            authenticated: true,
            role: payload.role || "user",
            email: payload.email
          }
        });
      }

      return delay({
        status: status,
        redirect: App.Helpers.link(payload.role === "admin" ? "pages/admin/dashboard.html" : "pages/dashboard.html")
      });
    },
    forgotPassword: function (email) {
      return delay({
        status: email === "unknown@example.com" ? "unknown" : "sent",
        email: email
      });
    },
    resetPassword: function (payload) {
      if (payload.token === "expired") {
        return delay({ status: "expired" });
      }
      if (payload.password !== payload.confirmPassword) {
        return delay({ status: "mismatch" });
      }
      return delay({ status: "success" });
    },
    submitOnboarding: function (payload) {
      var currentState = App.State.load();
      var account = payload.account || {};
      var demographics = payload.demographics || {};
      var profile = $.extend({}, currentState.profile, {
        username: account.username || currentState.profile.username,
        fullName: account.username || currentState.profile.fullName,
        phone: account.phone || currentState.profile.phone,
        age: demographics.age || "",
        gender: demographics.gender || "",
        maritalStatus: demographics.maritalStatus || "",
        occupation: demographics.occupation || "",
        holdingPeriodYears: payload.preferences.holdingPeriodYears,
        riskTolerance: payload.preferences.riskTolerance,
        paymentSensitivity: payload.preferences.paymentSensitivity,
        goal: payload.preferences.goal,
        inflationAversion: payload.preferences.inflationAversion,
        resetRiskAversion: payload.preferences.resetRiskAversion
      });

      App.State.save({
        onboarding: payload,
        profile: profile,
        session: {
          authenticated: true,
          role: "user",
          email: account.email || currentState.session.email || "yael@example.com"
        }
      });
      return delay({
        status: "success",
        redirect: App.Helpers.link("pages/dashboard.html")
      });
    },
    dismissAlert: function (alertId) {
      App.State.dismissAlert(alertId);
      return this.getAlerts();
    },
    getExpertData: function () {
      return delay(window.MockData.expert);
    },
    submitInterestRequest: function (payload) {
      App.State.save({
        lastInterestRequest: $.extend({}, payload, {
          submittedAt: new Date().toISOString(),
          status: "forwarded"
        })
      });
      return delay({
        success: true,
        message: "הבקשה הועברה לצוות שלנו. נחזור אליכם בהקדם להמשך טיפול."
      });
    },
    requestAdvisor: function () {
      return delay({ success: true });
    },
    getAdmin: function () {
      return delay(window.MockData.admin);
    }
  };
})();
