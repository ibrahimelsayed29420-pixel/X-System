# بحث مكونات X المفتوحة — 30 أكتوبر 2026

تمت مراجعة 36 مشروعًا. النجوم مأخوذة من GitHub REST وقت الفحص (2026-10-29T20:26:13.588239+00:00) وليست تقييم جودة أو ترتيبًا شاملًا لكل GitHub. هذه مراجعة مصادر وتراخيص أولية، وليست اختبار توافق أو تدقيقًا كاملًا للكود والتبعيات.

## قرار التصميم المقترح

يبقى X المنتج الرئيسي وOllama محرك النموذج المحلي. نبدأ بمكتبات قابلة للتركيب: LangGraph لتنسيق التنفيذ، Mem0 المفتوح بإعداد محلي للذاكرة عند الحاجة، Playwright للأفعال، Agent-Reach للبحث وCrawl4AI لاستخراج الصفحات محليًا. OpenClaw مرشح بوابة القنوات، وHermes مرجع تكميلي للمهارات والذاكرة، دون تشغيل محركين متداخلين. الاختيار مبني على ملاءمة Python الموجود وتقليل الخدمات، وليس أعلى النجوم وحدها.

لا نثبت كل هذه المشاريع. كل مكوّن يتطلب نسخة مثبتة، تراخيص تبعيات/نماذج، اختبار Windows ARM64، حدًا واضحًا للصلاحيات، وإثبات عمل قبل اعتباره مدمجًا. لا تغييرات لشخصية Ollama أو تسجيلات دخول الحسابات في هذه المرحلة.

## المقارنة مرتبة بالنجوم بين المرشحين

| المشروع | النجوم | ترخيص GitHub الآلي | القرار | الجزء المفيد وحدوده |
|---|---:|---|---|---|
| [openclaw/openclaw](https://github.com/openclaw/openclaw) | 393,373 | MIT | مرشح تكامل | بوابة القنوات والجلسات والأدوات: لا نشغّل مساعدًا موازيًا تلقائيًا؛ نحدد واجهة الربط بعد اختبار ARM64. |
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | 258,464 | MIT | مرجع تكميلي | المهارات المتراكمة والذاكرة والشخصية: نختار الوظائف المكملة دون تكرار محرك تنفيذ كامل. |
| [n8n-io/n8n](https://github.com/n8n-io/n8n) | 209,025 | NOASSERTION | ليس الاختيار الأول لشرط الترخيص | مرجع تدفقات العمل: Sustainable Use مع أجزاء Enterprise؛ ليس ترخيصًا مفتوحًا بلا قيود استخدام. |
| [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl) | 196,735 | AGPL-3.0 | بديل احتياطي | استخراج بيانات الويب: AGPL، والخدمة السحابية تشمل قدرات إضافية؛ لا نساوي بينهما. |
| [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) | 143,975 | GPL-3.0 | مرشح محتوى لاحقًا | تدفقات توليد ومعالجة الصور: GPL؛ الأوزان منفصلة وقد تحتاج GPU وذاكرة أكبر؛ لم يختبر على Surface. |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | 119,485 | MIT | اختبار تكميلي | قرارات التنقل المرئية بالمتصفح: مكتبة MIT، بينما الاستدلال والمتصفحات السحابية قد تكون مدفوعة؛ نختبر المحلي فقط. |
| [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) | 106,217 | MIT | مدمج جزئيًا ومختبر | بحث الويب وGitHub ومعلومات YouTube: بحث الويب يستخدم خدمات خارجية؛ حسابات السوشيال التجريبية غير مفعلة. |
| [odysseus-dev/odysseus](https://github.com/odysseus-dev/odysseus) | 94,694 | AGPL-3.0 | مرجع فقط — تثبيت موقوف | أفكار مساحة العمل والبريد والمهام: AGPL؛ لا استئناف تثبيته أو تشغيله بعد إيقافه بطلب المستخدم. |
| [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai) | 86,535 | Apache-2.0 | مرشح أول | استخراج محتوى صفحات عامة محليًا: حفظ إشعارات المصدر والتحقق من متطلبات الإسناد؛ التشغيل الذاتي غير الخدمة السحابية المدفوعة. |
| [docling-project/docling](https://github.com/docling-project/docling) | 69,817 | MIT | مرشح أول للملفات | قراءة PDF والجداول والمستندات: الكود MIT؛ تراخيص النماذج منفصلة، والدعم المعلن لا يغني عن اختبار الجهاز. |
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | 68,861 | NOASSERTION | مؤجل لشرط المجانية | فيديوهات بالقوالب البرمجية: ترخيص خاص؛ مجانية محددة بالأفراد وحجم المؤسسة، فلا نعتبره مجانيًا لكل حالات شركة العمل. |
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | 68,060 | Apache-2.0 | مرشح أول | ذاكرة تفضيلات إبراهيم وحقائق العمل: المكتبة المفتوحة بإعداد محلي؛ لا نتبع إعداد المنصة السحابية أو ننشئ حسابًا تلقائيًا. |
| [FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) | 66,035 | NOASSERTION | مرشح أول للمحتوى | مونتاج ومقاسات وترجمة الفيديو: LGPL/GPL بحسب إعداد البناء والمكتبات؛ لا يولد مشاهد بالذكاء الاصطناعي وحده. |
| [microsoft/autogen](https://github.com/microsoft/autogen) | 61,623 | CC-BY-4.0 | مستبعد من التنفيذ الجديد | مرجع تاريخي فقط: README يعلن انتهاء الصيانة ويوصي بـ Microsoft Agent Framework، رغم أن حقل archived بالـAPI ما زال false. |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | 60,258 | MIT | بديل احتياطي | أدوار فريق الوكلاء: لا يجمع مع كل محركات الوكلاء؛ المكون المفتوح فقط وليس AMP التجاري. |
| [twentyhq/twenty](https://github.com/twentyhq/twenty) | 60,076 | NOASSERTION | بديل CRM لاحقًا | تنظيم العملاء والصفقات: ترخيص مركب: AGPL مع استثناءات وأجزاء تجارية، لا يعتمد على حقل NOASSERTION وحده. |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | 44,113 | MIT | مرشح أول | تنسيق مهام X وحفظ مراحل التنفيذ والاستئناف: مكتبة قابلة للدمج في Python الحالي؛ LangSmith السحابي ليس شرطًا لتشغيل المكتبة. |
| [gitroomhq/postiz-app](https://github.com/gitroomhq/postiz-app) | 40,096 | AGPL-3.0 | مرشح أول لاحقًا | جدولة ونشر السوشيال: AGPL؛ تراخيص المنصات وOAuth والموافقات ورسوم الجهات الخارجية مستقلة. |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | 38,818 | Apache-2.0 | مثبت ومختبر محليًا سابقًا | تنفيذ خطوات المتصفح: اختبار صفحة محلية نجح؛ لا يثبت الوصول إلى حسابات العمل أو إتاحته تلقائيًا للنموذج المحلي. |
| [chatwoot/chatwoot](https://github.com/chatwoot/chatwoot) | 38,569 | NOASSERTION | مرشح عند توحيد المحادثات | صندوق بريد ورسائل موحد: المجتمع MIT؛ enterprise تجاري؛ وصول واتساب لا يُضمن مجانًا. |
| [qdrant/qdrant](https://github.com/qdrant/qdrant) | 35,312 | Apache-2.0 | مرشح أول عند الحاجة | استرجاع المعلومات المتجهية: نختار التشغيل المحلي، ونختبر المكتبة/التبعيات على الجهاز. |
| [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) | 30,756 | MIT | اختبار بعد LangGraph | التخطيط والمهارات والتفويض: مبني على LangGraph؛ نجاحه مرتبط بنموذج قادر على استدعاء الأدوات. |
| [chroma-core/chroma](https://github.com/chroma-core/chroma) | 29,604 | Apache-2.0 | بديل احتياطي | مخزن ذاكرة متجهية: لا نضيفه بالتوازي مع Qdrant دون مبرر. |
| [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | 26,297 | MIT | بديل اختبار | التعرف الصوتي: ليس ONNX؛ لا يستبدل مسار المستخدم الحالي دون قياس دقة وسرعة. |
| [letta-ai/letta](https://github.com/letta-ai/letta) | 25,290 | Apache-2.0 | بديل احتياطي | ذاكرة وكيل مستمرة: لا نشغّل مخزني ذاكرة متنافسين بلا حاجة. |
| [activepieces/activepieces](https://github.com/activepieces/activepieces) | 25,282 | NOASSERTION | مرشح أول لاحقًا | تدفقات التكامل والأحداث: Community MIT؛ نستبعد مجلدات Enterprise التجارية. |
| [k2-fsa/OmniVoice](https://github.com/k2-fsa/OmniVoice) | 16,076 | Apache-2.0 | تبعية موجودة للصوت | محرك توليد الصوت: لا تنزيل أو تدريب جديد؛ نموذج الصوت الحالي يعمل لكن بطيء. |
| [k2-fsa/sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) | 15,599 | Apache-2.0 | موجود في X | تشغيل التعرف والصوت عبر ONNX: المحرك يدعم Windows ARM64 بحسب README، لكن جودة العامية تتعلق بالنموذج؛ التراخيص منفصلة. |
| [microsoft/agent-framework](https://github.com/microsoft/agent-framework) | 14,374 | MIT | بديل احتياطي | تنسيق الوكلاء وMCP: البديل الذي تشير إليه وثائق AutoGen؛ لا حاجة لمحرك إضافي في البداية. |
| [MemTensor/MemOS](https://github.com/MemTensor/MemOS) | 12,180 | Apache-2.0 | مرجع واختبار لاحق | إدارة الذاكرة واسترجاعها: مفيد لكن أقل أولوية من حل واحد بسيط للذاكرة. |
| [snakers4/silero-vad](https://github.com/snakers4/silero-vad) | 10,561 | MIT | مرشح أول للصوت | تمييز بداية الكلام ونهايته: لا يفهم كلمة تمام ولا ينفذ التعرف على الكلام وحده؛ اختبار الضوضاء مطلوب. |
| [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl) | 6,078 | GPL-3.0 | احتياطي موجود | صوت سريع محلي: GPL؛ المستخدم رفض جودة الصوت، فلا يعاد تفعيله تلقائيًا. |
| [frappe/crm](https://github.com/frappe/crm) | 3,883 | AGPL-3.0 | مرشح CRM لاحقًا | دورة العملاء والمتابعة: AGPL؛ بناء CRM مؤجل بطلب إبراهيم، وليست أولوية التنفيذ الحالية. |
| [dscripka/openWakeWord](https://github.com/dscripka/openWakeWord) | 2,891 | Apache-2.0 | دراسة فقط | نداء يا إكس: تدريب واختبار عبارة عربية مطلوبان؛ تحقق مستقل من ترخيص النماذج الجاهزة وعدم افتراض صلاحيتها التجارية. |
| [MohammedAly22/VoiceTuT-TTS](https://github.com/MohammedAly22/VoiceTuT-TTS) | 45 | Apache-2.0 | موجود في X | صوت حسن المختار: الكود Apache؛ تراخيص الأوزان والمراجع مستقلة. بطء CPU مثبت في اختباراتنا. |
| [Sapheron/AgenticCRM](https://github.com/Sapheron/AgenticCRM) | 23 | MIT | مرجع متخصص لاحقًا | واتساب والصفقات والوكلاء: 23 نجمة وقت الفحص، مرحلة مبكرة، و11 خدمة؛ ليس أساس المشروع لمجرد تطابق الوصف. |

## ما ينقصه ربط مخصص

- Yahoo: تكامل بريد موثق واختبار حساب إبراهيم؛ تسجيل الدخول في المتصفح ليس اتصال IMAP/SMTP أو OAuth جاهزًا.
- Property Finder: مراجعة وصول API المتاح لحساب الشركة؛ لا يوجد موصل متحقق منه في المشاريع التي فحصناها.
- WhatsApp Business: بوابة جلسات الويب تختلف عن Cloud API. لا نجزم بإتاحة المجموعات أو كل البيانات أو مجانية الخدمة الرسمية.
- Meta / TikTok: موافقات وصلاحيات كل منصة تبقى مطلوبة حتى مع مكون مفتوح المصدر.
- المصرية والصوت: نحتاج مقارنة تسجيلات فعلية بموافقة إبراهيم؛ النجوم لا تثبت دقة العامية أو سرعة حسن.

## ترتيب العمل بعد البحث

1. تثبيت تصميم طبقات X واختيار واجهات الأدوات والذاكرة دون تشغيل خدمات مكررة.
2. بناء شخصية X على Ollama: الهوية واللهجة المهنية والذاكرة والصلاحيات، ثم قياس التزام النموذج بها وقدرته على الأدوات.
3. دمج واختبار كل مكوّن مع سجل مصدر وترخيص وإصدار ونتيجة؛ إدارة العملاء تبقى مؤجلة.

الكود المجاني لا يضمن نماذج أو استضافة أو APIs مجانية. NOASSERTION ليس حكمًا بعدم وجود ترخيص: تراخيص Activepieces وChatwoot وTwenty وn8n وRemotion وFFmpeg راجعت منفصلة وحفظت نسخة محلية. AutoGen مثال على تعارض حالة README مع metadata؛ نأخذ التحذير بالصيانة بجدية.

ملف evidence.json وسجلات README وLICENSE المجاورة توثق المصادر. المرشح لا يعني أنه مثبت أو متصل بحساباتك.