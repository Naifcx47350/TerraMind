export const STRINGS = {
  en: {
    appName: "TerraMind",
    profileRole: "Agriculture assistant",
    profileDefaultName: "Developer",
    conversations: "Conversations",
    searchPlaceholder: "Search conversations…",
    searchClear: "Clear search",
    noConversationsMatch: "No conversations match",
    newChat: "New chat",
    newConversation: "New conversation",
    delete: "Delete",
    settings: "Settings",
    appearance: "Appearance",
    language: "Language",
    langEn: "English",
    langAr: "Arabic",
    developerLabels: "Developer labels",
    showSources: "Show sources",
    showConfidence: "Show confidence",
    lightMode: "Light mode",
    darkMode: "Dark mode",
    emptyTitle: "Ask the field.",
    emptySub:
      "Crop diseases · Pesticide guidance · Agronomy\nType in any language or upload a plant photo.",
    emptyChip1: "Brown spots on tomato leaves?",
    emptyChip2: "Best irrigation for corn?",
    emptyChip3: "Which product works for aphids on cotton?",
    composerPlaceholder: "Ask in any language • اسأل بأي لغة…",
    composerCompare: "Same question to all 3 models…",
    compareHint: "Compare mode — Enter sends to all 3 models",
    sendHint: "Enter to send · Shift+Enter for new line",
    compare: "Compare",
    addImage: "Add image",
    dropImage: "Drop image here",
    layoutMode: "Layout",
    layoutStylized: "Stylized",
    layoutSimple: "Simple",
    layoutStylizedHint: "Theme backgrounds and art",
    layoutSimpleHint: "Clean, minimal interface",
    welcomeTitle: "Your farm. Smarter. Better. Together.",
    welcomeBody:
      "Get expert guidance for healthier crops and higher yields.",
    welcomeDismiss: "Got it",
    chooseModel: "Choose model",
    compareDisabled: "Disabled in compare mode",
    toggleSidebar: "Toggle sidebar",
    answeredUsing: "Answered using",
    usingMode: "Using",
    themes: {
      field: "Field",
      forest: "Forest",
      harvest: "Harvest",
      ocean: "Ocean",
      dusk: "Dusk",
    },
    advancedOptions: "Advanced",
    advancedOptionsHint: "Live overrides — saved in browser. Code defaults: src/theme/decorDefaults.js",
    decorProfile: "Profile avatar",
    decorComposer: "Chat corner",
    decorOpacity: "Opacity",
    decorRotation: "Rotation",
    decorSlot: "Asset slot",
  },
  ar: {
    appName: "TerraMind",
    profileRole: "مساعد زراعي",
    profileDefaultName: "Developer",
    conversations: "المحادثات",
    searchPlaceholder: "البحث في المحادثات…",
    searchClear: "مسح البحث",
    noConversationsMatch: "لا توجد محادثات مطابقة",
    newChat: "محادثة جديدة",
    newConversation: "محادثة جديدة",
    delete: "حذف",
    settings: "الإعدادات",
    appearance: "المظهر",
    language: "اللغة",
    langEn: "English",
    langAr: "العربية",
    developerLabels: "تسميات المطور",
    showSources: "إظهار المصادر",
    showConfidence: "إظهار الثقة",
    lightMode: "الوضع الفاتح",
    darkMode: "الوضع الداكن",
    emptyTitle: "اسأل الحقل.",
    emptySub:
      "أمراض المحاصيل · إرشادات المبيدات · علم زراعة\nاكتب بأي لغة أو ارفع صورة للنبات.",
    emptyChip1: "ما علاج الصدأ في القمح؟",
    emptyChip2: "أفضل ري للذرة؟",
    emptyChip3: "ما أفضل حل للمن على القطن؟",
    composerPlaceholder: "اسأل بأي لغة • Ask in any language…",
    composerCompare: "نفس السؤال لجميع النماذج الثلاثة…",
    compareHint: "وضع المقارنة — Enter يرسل لجميع النماذج",
    sendHint: "Enter للإرسال · Shift+Enter سطر جديد",
    compare: "مقارنة",
    addImage: "إضافة صورة",
    dropImage: "أفلت الصورة هنا",
    layoutMode: "التخطيط",
    layoutStylized: "مزخرف",
    layoutSimple: "بسيط",
    layoutStylizedHint: "خلفيات وفن حسب المظهر",
    layoutSimpleHint: "واجهة نظيفة وبسيطة",
    welcomeTitle: "مزرعتك. أذكى. أفضل. معًا.",
    welcomeBody: "احصل على إرشادات خبراء لمحاصيل أكثر صحة وغلة أعلى.",
    welcomeDismiss: "حسنًا",
    chooseModel: "اختر النموذج",
    compareDisabled: "معطل في وضع المقارنة",
    toggleSidebar: "إظهار/إخفاء الشريط",
    answeredUsing: "تمت الإجابة باستخدام",
    usingMode: "يستخدم",
    themes: {
      field: "حقل",
      forest: "غابة",
      harvest: "حصاد",
      ocean: "محيط",
      dusk: "غسق",
    },
    advancedOptions: "متقدم",
    advancedOptionsHint: "تجاوزات مباشرة — تُحفظ في المتصفح. الافتراضيات: src/theme/decorDefaults.js",
    decorProfile: "صورة الملف",
    decorComposer: "زاوية الدردشة",
    decorOpacity: "الشفافية",
    decorRotation: "الدوران",
    decorSlot: "ملف الزخرفة",
  },
};

export function uiLang(settings) {
  return settings?.language === "ar" ? "ar" : "en";
}

export function tr(settings, key) {
  const lang = uiLang(settings);
  const parts = key.split(".");
  let node = STRINGS[lang];
  for (const p of parts) {
    node = node?.[p];
  }
  if (node != null) return node;
  node = STRINGS.en;
  for (const p of parts) {
    node = node?.[p];
  }
  return node ?? key;
}

export function isRtlUi(settings) {
  return uiLang(settings) === "ar";
}
