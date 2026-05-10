(function () {
  window.App = window.App || {};

  function delay(payload) {
    return new Promise(function (resolve) {
      window.setTimeout(function () {
        resolve(App.Helpers.deepClone(payload));
      }, 180);
    });
  }

  function apiBase() {
    var fromBody = document.body && document.body.dataset && document.body.dataset.apiBase;
    var fromStorage = window.localStorage.getItem("labib-api-base");
    return fromBody || fromStorage || "http://localhost:8001/api/v1";
  }

  function apiRequest(path, options) {
    var config = options || {};
    var headers = $.extend({ "Content-Type": "application/json" }, config.headers || {});
    return fetch(apiBase() + path, {
      method: config.method || "GET",
      headers: headers,
      body: config.body ? JSON.stringify(config.body) : undefined
    }).then(function (response) {
      return response.text().then(function (text) {
        var data = {};
        try {
          data = text ? JSON.parse(text) : {};
        } catch (error) {
          data = {};
        }
        if (!response.ok) {
          var err = new Error(data.detail || "Request failed");
          err.status = response.status;
          err.payload = data;
          throw err;
        }
        return data;
      });
    });
  }

  function sessionInfo() {
    return App.State.load().session || {};
  }

  function mapTrack(apiTrack) {
    return {
      id: apiTrack.id,
      label: apiTrack.label,
      type: apiTrack.track_type,
      outstandingBalance: apiTrack.outstanding_balance,
      currentRate: apiTrack.current_rate,
      originalRate: apiTrack.current_rate,
      remainingTermMonths: apiTrack.remaining_term_months,
      linkageType: apiTrack.linkage_type,
      rateType: apiTrack.rate_type,
      resetInterval: apiTrack.reset_interval,
      nextResetDate: apiTrack.next_reset_date,
      amortizationMethod: apiTrack.amortization_method,
      prepaymentPenaltyRule: apiTrack.prepayment_penalty_rule
    };
  }

  function mapMortgage(apiMortgage) {
    if (!apiMortgage) {
      return deriveMortgage();
    }

    var raw = apiMortgage.raw_payload || {};
    var rawCosts = raw.costs || {};
    var rawPrefs = raw.preferences || {};
    var rawTracks = (raw.tracks || []).map(function (track) {
      return {
        id: track.id || App.Helpers.uid("track"),
        label: track.label,
        type: track.type,
        outstandingBalance: track.outstandingBalance,
        currentRate: track.currentRate,
        originalRate: track.originalRate,
        remainingTermMonths: track.remainingTermMonths,
        linkageType: track.linkageType,
        rateType: track.rateType,
        resetInterval: track.resetInterval,
        nextResetDate: track.nextResetDate,
        amortizationMethod: track.amortizationMethod,
        prepaymentPenaltyRule: track.prepaymentPenaltyRule
      };
    });
    var tracks = apiMortgage.tracks && apiMortgage.tracks.length
      ? apiMortgage.tracks.map(mapTrack)
      : rawTracks;

    var remainingTerm = raw.basic && raw.basic.remainingTermMonths
      ? Number(raw.basic.remainingTermMonths)
      : tracks.reduce(function (max, track) { return Math.max(max, Number(track.remainingTermMonths || 0)); }, 0);

    return {
      lender: (raw.lender && raw.lender.lenderName) || apiMortgage.lender_name,
      originationDate: raw.lender && raw.lender.originationDate,
      originalAmount: raw.lender && raw.lender.originalAmount,
      propertyValue: (raw.basic && raw.basic.propertyValue) || apiMortgage.property_value,
      currentMonthlyPayment: (raw.basic && raw.basic.currentMonthlyPayment) || apiMortgage.current_monthly_payment,
      remainingTermMonths: remainingTerm || 0,
      tracks: tracks,
      outstandingBalance: apiMortgage.outstanding_balance_total,
      refinanceCosts: {
        prepaymentFee: Number(rawCosts.prepaymentFee || apiMortgage.estimated_refinance_cost || 0),
        legalFee: Number(rawCosts.legalFee || 0),
        appraisal: Number(rawCosts.appraisal || 0),
        registration: Number(rawCosts.registration || 0),
        advisor: Number(rawCosts.advisor || 0)
      },
      preferences: {
        holdingPeriodYears: rawPrefs.holdingPeriodYears,
        riskTolerance: rawPrefs.riskTolerance,
        paymentPreference: rawPrefs.goal,
        inflationAversion: rawPrefs.inflationAversion,
        resetRiskAversion: rawPrefs.resetRiskAversion
      }
    };
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
      var session = sessionInfo();
      if (!session.userId) {
        return delay(deriveMortgage());
      }
      return apiRequest("/mortgages/latest?user_id=" + session.userId)
        .then(function (response) {
          return mapMortgage(response.mortgage);
        })
        .catch(function () {
          return deriveMortgage();
        });
    },
    getDashboard: function () {
      var session = sessionInfo();
      if (!session.userId) {
        return delay(deriveDashboard());
      }
      return apiRequest("/mortgages/dashboard?user_id=" + session.userId)
        .then(function (response) {
          return response.dashboard || deriveDashboard();
        })
        .catch(function () {
          return deriveDashboard();
        });
    },
    getAnalysis: function () {
      return Promise.all([App.MockApi.getMortgage(), App.MockApi.getDashboard()]).then(function (results) {
        var mortgage = results[0] || deriveMortgage();
        var dashboard = results[1] || deriveDashboard();
        var analysis = App.Helpers.deepClone(window.MockData.analysis);
        analysis.keepCurrent.monthlyPayment = mortgage.currentMonthlyPayment;
        analysis.refinanceNow.monthlyPayment = dashboard.estimatedRefinancePayment;
        analysis.refinanceNow.breakEvenMonths = dashboard.breakEvenMonths;
        analysis.refinanceNow.projectedSavings = dashboard.projectedNetSavings;
        analysis.refinanceNow.upfrontCost = getUpfrontCosts(mortgage);
        return analysis;
      });
    },
    getPartialRefinance: function () {
      return delay(window.MockData.partialRefinance);
    },
    getScenarios: function () {
      return delay(window.MockData.scenarios);
    },
    getAlerts: function () {
      var session = sessionInfo();
      if (!session.userId) {
        var alerts = App.Helpers.deepClone(window.MockData.alerts);
        var dismissed = App.State.load().alertsDismissed || [];
        alerts.active = alerts.active.filter(function (item) {
          return dismissed.indexOf(item.id) === -1;
        });
        alerts.dismissed = alerts.dismissed.concat(window.MockData.alerts.active.filter(function (item) {
          return dismissed.indexOf(item.id) !== -1;
        }));
        return delay(alerts);
      }
      return apiRequest("/alerts?user_id=" + session.userId).catch(function () {
        return { active: [], history: [], dismissed: [] };
      });
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
      var registerPayload = {
        username: payload.email,
        email: payload.email,
        password: payload.password,
        phone_number: payload.phone || null
      };

      return apiRequest("/auth/register", { method: "POST", body: registerPayload })
        .then(function (response) {
          App.State.save({
            profile: $.extend({}, App.State.load().profile, {
              phone: payload.phone || App.State.load().profile.phone,
              username: payload.email || App.State.load().profile.username
            }),
            session: {
              authenticated: false,
              role: "user",
              email: payload.email,
              userId: response.user_id
            }
          });
          return {
            success: true,
            email: payload.email
          };
        })
        .catch(function (error) {
          if (error.status === 409) {
            return { success: false, code: "email_taken", detail: error.payload && error.payload.detail };
          }
          return { success: false, code: "error" };
        });
    },
    login: function (payload) {
      return apiRequest("/auth/login", {
        method: "POST",
        body: {
          email: payload.email,
          password: payload.password
        }
      }).then(function (response) {
        App.State.save({
          session: {
            authenticated: true,
            role: response.role,
            email: response.email,
            userId: response.user_id
          }
        });

        return {
          status: "success",
          role: response.role,
          redirect: App.Helpers.link(response.role === "admin" ? "pages/admin/dashboard.html" : "pages/dashboard.html")
        };
      }).catch(function (error) {
        if (error.status === 423) {
          return { status: "locked" };
        }
        if (error.status === 401) {
          return { status: "invalid" };
        }
        return { status: "error" };
      });
    },
    forgotPassword: function (email) {
      return apiRequest("/auth/forgot-password", { method: "POST", body: { email: email } })
        .then(function (response) {
          return {
            status: response.status === "ignored" ? "unknown" : "sent",
            email: email
          };
        })
        .catch(function () {
          return { status: "error", email: email };
        });
    },
    resetPassword: function (payload) {
      if (payload.password !== payload.confirmPassword) {
        return delay({ status: "mismatch" });
      }
      return apiRequest("/auth/reset-password", {
        method: "POST",
        body: {
          token: payload.token,
          password: payload.password
        }
      }).then(function () {
        return { status: "success" };
      }).catch(function (error) {
        if (error.status === 400) {
          return { status: "expired" };
        }
        return { status: "error" };
      });
    },
    submitOnboarding: function (payload) {
      var currentState = App.State.load();
      var account = payload.account || {};
      var demographics = payload.demographics || {};
      var session = currentState.session || {};

      var registerPayload = {
        username: account.username || account.email,
        email: account.email,
        password: account.password,
        phone_number: account.phone || null,
        age: demographics.age ? Number(demographics.age) : null,
        gender: demographics.gender || null,
        marital_status: demographics.maritalStatus || null,
        occupation: demographics.occupation || null,
        holding_period_years: payload.preferences.holdingPeriodYears,
        risk_tolerance: payload.preferences.riskTolerance,
        payment_sensitivity: payload.preferences.paymentSensitivity,
        preference_goal: payload.preferences.goal,
        inflation_aversion: payload.preferences.inflationAversion,
        reset_risk_aversion: payload.preferences.resetRiskAversion
      };

      function createMortgage(userId) {
        var rawPayload = App.Helpers.deepClone(payload);
        if (rawPayload.account) {
          rawPayload.account.password = "";
          rawPayload.account.confirmPassword = "";
        }
        var mortgagePayload = {
          lender_name: payload.lender.lenderName,
          property_city: payload.basic.propertySettlement || null,
          property_value: Number(payload.basic.propertyValue || 0),
          current_monthly_payment: Number(payload.basic.currentMonthlyPayment || 0),
          loan_purpose: payload.basic.propertySubtype || null,
          occupancy_status: payload.basic.propertyType || null,
          prepayment_fee: Number(payload.costs.prepaymentFee || 0),
          advisor_cost: Number(payload.costs.advisor || 0),
          bank_cost: Number(payload.costs.bankFees || 0),
          appraisal_cost: payload.costs.appraisalRequired ? 2500 : 0,
          appraisal_required: !!payload.costs.appraisalRequired,
          years_since_origination: Number(payload.basic.yearsSinceOrigin || 0),
          tracks: payload.tracks.map(function (track) {
            return {
              label: track.label,
              track_type: track.type,
              outstanding_balance: Number(track.outstandingBalance || 0),
              current_rate: Number(track.currentRate || 0),
              original_rate: Number(track.originalRate || track.currentRate || 0),
              remaining_term_months: Number(track.remainingTermMonths || 0),
              linkage_type: track.linkageType || null,
              rate_type: track.rateType || null,
              reset_interval: track.resetInterval || null,
              next_reset_date: track.nextResetDate || null,
              amortization_method: track.amortizationMethod || null,
              prepayment_penalty_rule: track.prepaymentPenaltyRule || null,
              original_cpi: track.originalCPI != null && track.originalCPI !== "" ? Number(track.originalCPI) : null,
              bank_margin: track.bankMargin != null && track.bankMargin !== "" ? Number(track.bankMargin) : null,
              years_since_origination: Number(payload.basic.yearsSinceOrigin || 0)
            };
          })
        };

        return apiRequest("/mortgages", {
          method: "POST",
          body: {
            user_id: userId,
            mortgage: mortgagePayload,
            raw_payload: rawPayload
          }
        });
      }

      var registerFlow = session.userId
        ? Promise.resolve({ user_id: session.userId })
        : apiRequest("/auth/register", { method: "POST", body: registerPayload });

      return registerFlow.then(function (response) {
        return createMortgage(response.user_id).then(function () {
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
              email: account.email || currentState.session.email || "yael@example.com",
              userId: response.user_id
            }
          });

          return {
            status: "success",
            redirect: App.Helpers.link("pages/dashboard.html")
          };
        });
      }).catch(function (error) {
        if (error.status === 409) {
          return { status: "email_taken" };
        }
        return { status: "error" };
      });
    },
    dismissAlert: function (alertId) {
      var session = sessionInfo();
      if (!session.userId) {
        App.State.dismissAlert(alertId);
        return this.getAlerts();
      }
      return apiRequest("/alerts/" + alertId + "/dismiss", { method: "POST" })
        .then(function () {
          return App.MockApi.getAlerts();
        })
        .catch(function () {
          return App.MockApi.getAlerts();
        });
    },
    getExpertData: function () {
      return delay(window.MockData.expert);
    },
    submitInterestRequest: function (payload) {
      var session = sessionInfo();
      return apiRequest("/mortgages/requests/interest", {
        method: "POST",
        body: {
          user_id: session.userId || null,
          request_type: "interest",
          source_page: payload.context,
          details: {
            recommendation: payload.recommendation || null
          }
        }
      }).then(function () {
        App.State.save({
          lastInterestRequest: $.extend({}, payload, {
            submittedAt: new Date().toISOString(),
            status: "forwarded"
          })
        });
        return {
          success: true,
          message: "הבקשה הועברה לצוות שלנו. נחזור אליכם בהקדם להמשך טיפול."
        };
      }).catch(function () {
        return {
          success: false,
          message: "לא ניתן לשלוח את הבקשה כרגע. נסו שוב."
        };
      });
    },
    requestAdvisor: function () {
      return delay({ success: true });
    },
    getAdmin: function () {
      return apiRequest("/admin/overview").catch(function () {
        return window.MockData.admin;
      });
    },
    checkEmailAvailability: function (email) {
      return apiRequest("/auth/email-available?email=" + encodeURIComponent(email));
    },
    lockUser: function (userId) {
      return apiRequest("/admin/users/" + userId + "/lock", { method: "POST" });
    }
  };
})();
