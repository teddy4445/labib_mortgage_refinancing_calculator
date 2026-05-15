window.MockData = {
  initialState: {
    session: {
      authenticated: false,
      role: "user",
      email: ""
    },
    onboarding: null,
    alertsDismissed: [],
    notifications: {
      email: true,
      sms: false,
      weeklyDigest: true,
      severeOnly: false
    },
    profile: {
      username: "",
      fullName: "",
      city: "תל אביב",
      phone: "050-555-0182",
      age: "",
      gender: "",
      maritalStatus: "",
      occupation: "",
      holdingPeriodYears: 8,
      riskTolerance: "balanced",
      paymentSensitivity: "medium",
      goal: "monthly_payment",
      inflationAversion: "high",
      resetRiskAversion: "medium"
    }
  },
  landing: {
    benefits: [
      {
        title: "השוואה בין המשכנתא הקיימת לשוק הנוכחי",
        body: "המערכת בודקת את מבנה המסלולים הקיים, עלויות היציאה והחלופות בשוק כדי לזהות אם יש חלון פעולה אמיתי."
      },
      {
        title: "זיהוי חיסכון נטו ולא רק ריבית",
        body: "המלצות מוצגות יחד עם עמלות, נקודת איזון, סיכון הצמדה וסיכון ריבית כדי למנוע החלטות חלקיות."
      },
      {
        title: "מעקב שוטף והתראות",
        body: "התראות על שינויי ריבית, עוגנים, תקופות איפוס וחריגה ממדיניות הסיכון האישית נשמרות לאורך זמן."
      }
    ],
    faq: [
      {
        question: "מתי כדאי בכלל לבדוק מחזור משכנתא?",
        answer: "כאשר המרווח בין העלות הנוכחית לעלות האלטרנטיבית גדל, כאשר מסלול עומד לפני איפוס, או כאשר פרופיל הסיכון שלכם השתנה."
      },
      {
        question: "האם המערכת נותנת ייעוץ פיננסי מחייב?",
        answer: "לא. זו מערכת המלצה וסימולציה. היא מיועדת לתמוך בקבלת החלטה ולסייע בהכנה לשיחה עם הבנק או עם יועץ מקצועי."
      },
      {
        question: "האם מוצגים גם עלויות ועמלות?",
        answer: "כן. נכללים קנסות פירעון מוקדם, הוצאות משפטיות, שמאות, רישום והנחות תפעוליות שניתנות להתאמה."
      },
      {
        question: "אפשר לבדוק מחזור חלקי בלבד?",
        answer: "כן. המערכת מציגה בנפרד מחזור מלא מול מחזור חלקי ומסבירה אילו מסלולים כדאי להשאיר ואילו לשקול להחליף."
      }
    ]
  },
  mortgage: {
    lender: "Mizrahi Tefahot Bank Ltd.",
    originationDate: "2020-11-15",
    originalAmount: 1540000,
    propertyValue: 2480000,
    currentMonthlyPayment: 7640,
    outstandingBalance: 1182000,
    remainingTermMonths: 233,
    refinanceCosts: {
      prepaymentFee: 12400,
      legalFee: 2800,
      appraisal: 1850,
      registration: 760,
      advisor: 2400
    },
    preferences: {
      holdingPeriodYears: 8,
      riskTolerance: "מאוזן",
      paymentPreference: "הפחתת תשלום חודשי",
      inflationAversion: "גבוהה",
      resetRiskAversion: "בינונית"
    },
    tracks: [
      {
        id: "trk-fixed-linked",
        label: "קבועה צמודה",
        type: "fixed_linked",
        outstandingBalance: 402000,
        currentRate: 3.25,
        originalRate: 2.8,
        remainingTermMonths: 188,
        linkageType: "צמוד מדד",
        rateType: "קבועה",
        resetInterval: "ללא",
        nextResetDate: "לא רלוונטי",
        amortizationMethod: "שפיצר",
        prepaymentPenaltyRule: "רגיש לפער ריביות",
        riskTag: "חשיפה למדד"
      },
      {
        id: "trk-prime",
        label: "פריים",
        type: "prime_floating",
        outstandingBalance: 360000,
        currentRate: 5.95,
        originalRate: 1.6,
        remainingTermMonths: 233,
        linkageType: "לא צמוד",
        rateType: "משתנה",
        resetInterval: "חודשי",
        nextResetDate: "2026-04-01",
        amortizationMethod: "שפיצר",
        prepaymentPenaltyRule: "קנס נמוך",
        riskTag: "חשיפה לריבית"
      },
      {
        id: "trk-adjustable",
        label: "משתנה כל 5",
        type: "adjustable_non_linked",
        outstandingBalance: 420000,
        currentRate: 4.75,
        originalRate: 3.35,
        remainingTermMonths: 206,
        linkageType: "לא צמוד",
        rateType: "משתנה",
        resetInterval: "60 חודשים",
        nextResetDate: "2027-10-01",
        amortizationMethod: "קרן שווה",
        prepaymentPenaltyRule: "תלוי תחנת יציאה",
        riskTag: "סיכון איפוס"
      }
    ]
  },
  dashboard: {
    recommendation: {
      headline: "מומלץ לבחון מחזור חלקי בתוך 45 יום",
      tone: "warning",
      reason: "מסלול הפריים התייקר, ובשני מסלולים קבועים ניתן לשפר את העלות הכוללת בלי להאריך משמעותית את התקופה."
    },
    urgency: {
      label: "דחיפות בינונית-גבוהה",
      description: "פער העלות כבר משמעותי, אך קנס היציאה במסלול הקבוע עדיין סביר."
    },
    estimatedRefinancePayment: 6980,
    projectedNetSavings: 184300,
    breakEvenMonths: 17,
    lastAnalysisTime: "2026-03-12T16:45:00+02:00",
    recentAlerts: [
      {
        id: "al-1",
        severity: "high",
        title: "מסלול הפריים עלה מעל סף ההתראה",
        message: "עליית הריבית הגדילה את התשלום החודשי בכ-410 ש\"ח לעומת הרבעון הקודם.",
        timestamp: "2026-03-12T10:05:00+02:00"
      },
      {
        id: "al-2",
        severity: "medium",
        title: "פער חיסכון חיובי במחזור חלקי",
        message: "המערכת מזהה נקודת איזון קצרה מ-18 חודשים עבור החלפת שני מסלולים.",
        timestamp: "2026-03-11T08:20:00+02:00"
      },
      {
        id: "al-3",
        severity: "low",
        title: "עודכן עוגן שוק לאינפלציה",
        message: "תרחיש הבסיס עודכן על בסיס פרסום ציפיות אינפלציה עדכניות.",
        timestamp: "2026-03-09T13:40:00+02:00"
      }
    ]
  },
  analysis: {
    keepCurrent: {
      monthlyPayment: 7640,
      totalRemainingCost: 1689000,
      riskScore: 74,
      inflationExposure: "גבוהה",
      resetExposure: "בינונית"
    },
    refinanceNow: {
      monthlyPayment: 6980,
      totalRemainingCost: 1486200,
      upfrontCost: 20210,
      breakEvenMonths: 17,
      npv: 112400,
      projectedSavings: 184300,
      riskScore: 48,
      inflationExposure: "נמוכה יותר",
      resetExposure: "נמוכה"
    },
    explanation: [
      "עיקר התרומה מגיעה מהחלפת מסלול הפריים ומסלול המשתנה כל 5 למסלול קבוע לא צמוד קצר יותר.",
      "גם לאחר קנסות ועלויות מעבר, תזרים המזומנים המצטבר חוזר לחיוב לאחר 17 חודשים.",
      "ירידה בחשיפה למדד ולתחנות איפוס משפרת את עמידות התיק בתרחיש אינפלציה מתמשך."
    ],
    assumptions: [
      "החזקה בנכס למשך 8 שנים לפחות.",
      "אין גרירת משכנתא או מכירת נכס בטווח הקצר.",
      "הוצאות נלוות משוקללות לפי טווחי שוק עדכניים אך אינן הצעה מחייבת."
    ],
    paymentPath: [
      { month: "0", current: 0, proposed: -20210 },
      { month: "12", current: -91680, proposed: -83760 },
      { month: "24", current: -183360, proposed: -167520 },
      { month: "36", current: -275040, proposed: -251280 },
      { month: "60", current: -458400, proposed: -418800 }
    ]
  },
  partialRefinance: {
    refinance: [
      {
        label: "פריים",
        savingsContribution: 74200,
        riskReduction: "גבוהה",
        reason: "רגישות מלאה לעליית ריבית בנק ישראל."
      },
      {
        label: "משתנה כל 5",
        savingsContribution: 68100,
        riskReduction: "בינונית",
        reason: "חלון איפוס קרוב ושיפור בעלות הכוללת."
      }
    ],
    keep: [
      {
        label: "קבועה צמודה",
        savingsContribution: 0,
        riskReduction: "נמוכה",
        reason: "קנס יציאה עדיין גבוה יחסית לתועלת בטווח ההחזקה."
      }
    ],
    constraints: [
      "נדרש לבדוק אפשרות פיצול בטאבו ובהסכמי הבנק עבור מחזור חלקי.",
      "עמלת פירעון עשויה להשתנות עד למועד הביצוע בפועל.",
      "במקרה של שינוי מהותי בשווי הנכס יש לעדכן את יחס המימון."
    ]
  },
  scenarios: {
    verdict: "ההמלצה למחזור חלקי נשארת חיובית ב-5 מתוך 7 תרחישים שנבדקו.",
    rows: [
      { name: "בסיס", payment: 6980, savings: 184300, breakEven: 17, verdict: "חיובי" },
      { name: "אינפלציה גבוהה", payment: 7060, savings: 166400, breakEven: 18, verdict: "חיובי" },
      { name: "אינפלציה נמוכה", payment: 6940, savings: 191900, breakEven: 16, verdict: "חיובי" },
      { name: "עליית ריבית", payment: 7150, savings: 149800, breakEven: 19, verdict: "זהיר" },
      { name: "ירידת ריבית", payment: 6810, savings: 209600, breakEven: 15, verdict: "חיובי מאוד" },
      { name: "אחזקה קצרה", payment: 6980, savings: 38400, breakEven: 17, verdict: "גבולי" },
      { name: "לחץ תזרימי", payment: 6880, savings: 158600, breakEven: 18, verdict: "חיובי" }
    ],
    sensitivity: [
      { label: "עמלת פירעון מוקדם", impact: "השפעה בינונית", note: "עלייה של 20% דוחה את נקודת האיזון בחודש אחד." },
      { label: "ריבית מסלול מוצע", impact: "השפעה גבוהה", note: "סטייה של 0.4% משנה את החיסכון בכ-28 אלף ש\"ח." },
      { label: "תקופת החזקה", impact: "השפעה גבוהה", note: "מתחת ל-4 שנים מחזור מלא מאבד כדאיות." }
    ]
  },
  alerts: {
    active: [
      {
        id: "act-1",
        severity: "high",
        title: "עליית תשלום במסלול פריים",
        category: "ריבית",
        description: "התשלום במסלול הפריים עלה ב-5.7% לעומת הניתוח הקודם.",
        timestamp: "2026-03-12T10:05:00+02:00"
      },
      {
        id: "act-2",
        severity: "medium",
        title: "נקודת איזון השתפרה ל-17 חודשים",
        category: "חיסכון",
        description: "הפחתה בעלויות הכניסה קיצרה את זמן החזר ההשקעה.",
        timestamp: "2026-03-11T08:20:00+02:00"
      },
      {
        id: "act-3",
        severity: "low",
        title: "תחנת איפוס עתידית במסלול משתנה",
        category: "תזמון",
        description: "המסלול המשתנה יגיע לתחנת איפוס באוקטובר 2027.",
        timestamp: "2026-03-07T09:00:00+02:00"
      }
    ],
    history: [
      {
        id: "his-1",
        severity: "medium",
        title: "עודכן מרווח שוק למסלול קבוע",
        category: "שוק",
        description: "ירידה של 0.18% בריבית החלופית למסלול קבוע לא צמוד.",
        timestamp: "2026-02-18T12:15:00+02:00"
      }
    ],
    dismissed: [
      {
        id: "dis-1",
        severity: "low",
        title: "תזכורת לאימות נתוני שמאות",
        category: "מסמכים",
        description: "המלצה לעדכן שמאות לפני פנייה לבנק.",
        timestamp: "2026-01-22T11:00:00+02:00"
      }
    ]
  },
  expert: {
    actions: [
      "איסוף דפי יתרה עדכניים לכל מסלול.",
      "בדיקת עמלת פירעון מוקדם מול הבנק הקיים.",
      "קבלת שתי הצעות חלופיות לפחות להשוואה.",
      "אימות השפעת המחזור על תזרים חודשי ותקופת החזקה."
    ],
    documents: [
      "תעודת זהות וספח.",
      "נסח טאבו או אישור זכויות.",
      "שלושה תלושי שכר או דוחות הכנסה.",
      "דוח יתרות משכנתא מפורט.",
      "שמאות עדכנית אם נדרשת."
    ]
  },
  admin: {
    dashboard: {
      stats: [
        { label: "ניתוחים שבוצעו היום", value: 184, change: "+12%" },
        { label: "תיקים בהמתנה לבדיקת אנליסט", value: 26, change: "-3" },
        { label: "חריגות מדיניות פעילות", value: 8, change: "+2" },
        { label: "משימות ETL פתוחות", value: 3, change: "ללא שינוי" }
      ],
      queue: [
        { customer: "יעל לוי", recommendation: "מחזור חלקי", analyst: "נועם", updated: "18:10", status: "ממתין לאישור" },
        { customer: "אמיר כהן", recommendation: "מעקב בלבד", analyst: "שירה", updated: "17:42", status: "טיוטה" },
        { customer: "משפחת ברק", recommendation: "מחזור מלא", analyst: "ניצן", updated: "17:06", status: "מוכן לשליחה" }
      ]
    },
    marketData: {
      sources: [
        { source: "עוגני בנקים", status: "תקין", updated: "2026-03-13 06:45" },
        { source: "אינפלציה וציפיות", status: "תקין", updated: "2026-03-12 21:10" },
        { source: "שערי אג\"ח", status: "איחור קל", updated: "2026-03-13 05:55" }
      ],
      curves: [
        { tenor: "5 שנים קבועה", rate: 4.18, delta: -0.12 },
        { tenor: "10 שנים קבועה", rate: 4.42, delta: -0.08 },
        { tenor: "פריים", rate: 6.0, delta: 0.25 }
      ]
    },
    policies: {
      thresholds: [
        { name: "סף חיסכון חודשי להמלצה", value: "₪350" },
        { name: "נקודת איזון מקסימלית", value: "24 חודשים" },
        { name: "תקרת חשיפת מדד לאחר מחזור", value: "25%" },
        { name: "סף דחיפות גבוה", value: "סיכון מעל 70 או איפוס מתחת ל-90 יום" }
      ]
    },
    users: {
      rows: [
        { name: "יעל לוי", city: "תל אביב", portfolio: "3 מסלולים", status: "פעיל", lastSeen: "היום 18:02" },
        { name: "אמיר כהן", city: "חיפה", portfolio: "2 מסלולים", status: "בהמתנה", lastSeen: "היום 16:18" },
        { name: "משפחת ברק", city: "מודיעין", portfolio: "4 מסלולים", status: "פעיל", lastSeen: "היום 15:11" }
      ]
    },
    legal: {
      versions: [
        { item: "כתב ויתור כללי", version: "v3.4", updated: "2026-03-08", owner: "מחלקה משפטית" },
        { item: "הנחות מודל CPI", version: "v2.1", updated: "2026-02-27", owner: "ניהול סיכונים" }
      ]
    },
    auditLogs: {
      rows: [
        { time: "18:12", actor: "system", action: "market-data-refresh", status: "success" },
        { time: "17:55", actor: "analyst:noam", action: "recommendation-approved", status: "success" },
        { time: "17:34", actor: "admin:shir", action: "policy-threshold-update", status: "warning" }
      ]
    }
  }
};
