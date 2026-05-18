# 🤖 AI Pipeline — Integration Guide for Frontend Team

> **Last Updated:** 2026-05-18 | **Latest Commit:** `397e74a` (main branch)

---

## 📁 ملفات الـ AI Integration في الباك إند

| الغرض | المسار |
|--------|--------|
| كل الـ Endpoints (75+ route) | `app/api/v1/ai_pipeline.py` |
| الـ Service اللي بتكلم الـ AI الخارجي | `app/services/ai_pipeline_service.py` |
| الـ Request/Response Schemas | `app/schemas/ai_pipeline.py` |
| حماية الاستهلاك (Rate Limiting) | `app/api/dependencies.py` → `check_ai_usage` |

---

## 🌐 Base URL

```
http://localhost:8000/api/v1/ai/
```

---

## 🔐 Authentication

كل الـ Endpoints محتاجة **Bearer Token** في الـ Header:

```http
Authorization: Bearer <access_token>
```

احصل على الـ Token من: `POST /api/v1/auth/login`

---

## 📋 قائمة الـ Endpoints (مقسمة بالقسم)

### 🔧 System
| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `POST` | `/ai/run` | تشغيل الـ AI Pipeline للمستخدم |
| `GET` | `/ai/status` | حالة الـ Pipeline |
| `GET` | `/ai/health` | Health Check |
| `GET` | `/ai/version-check` | Version Check |

### 👤 Profile
| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `/ai/profile` | نتيجة تحليل البروفايل |
| `GET` | `/ai/questionnaire` | جلب الاستبيان |
| `POST` | `/ai/rerun/profile` | إعادة تشغيل تحليل البروفايل |

### 💡 Idea
| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `/ai/idea` | جلب الفكرة المولدة |
| `POST` | `/ai/idea-intake` | إدخال فكرة جديدة |
| `GET` | `/ai/idea-intake` | جلب الفكرة المدخلة |
| `POST` | `/ai/idea-intake/start-chat` | بدء شات حول الفكرة |
| `POST` | `/ai/idea-intake/run-problems` | تشغيل تحليل المشاكل للفكرة |

### 🚨 Problems
| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `/ai/problems` | جلب المشاكل المحللة |
| `POST` | `/ai/rerun/problems` | إعادة تحليل المشاكل |

### 👥 Customers
| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `POST` | `/ai/customers` | توليد تحليل العملاء |
| `GET` | `/ai/customers` | جلب تحليل العملاء |
| `POST` | `/ai/customers/regenerate` | إعادة التوليد |
| `POST` | `/ai/customers/regenerate-custom` | إعادة التوليد بـ Custom Prompt |
| `POST` | `/ai/customers/chat` | شات حول تحليل العملاء |
| `POST` | `/ai/customers/chat/stream` | شات Streaming |

### 🏆 Competition
| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `POST` | `/ai/competition` | توليد تحليل المنافسة |
| `GET` | `/ai/competition` | جلب تحليل المنافسة |
| `POST` | `/ai/competition/regenerate` | إعادة التوليد |
| `POST` | `/ai/competition/regenerate-custom` | إعادة التوليد بـ Custom Prompt |
| `POST` | `/ai/competition/chat` | شات حول المنافسة |
| `POST` | `/ai/competition/chat/stream` | شات Streaming |

### 📈 Market Potential
| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `POST` | `/ai/market-potential` | توليد تحليل السوق |
| `GET` | `/ai/market-potential` | جلب تحليل السوق |
| `POST` | `/ai/market-potential/regenerate` | إعادة التوليد |
| `POST` | `/ai/market-potential/regenerate-custom` | إعادة التوليد بـ Custom Prompt |
| `POST` | `/ai/market-potential/chat` | شات |
| `POST` | `/ai/market-potential/chat/stream` | شات Streaming |

### 💡 Idea Strategy
| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `POST` | `/ai/idea-strategy` | توليد استراتيجية الفكرة |
| `GET` | `/ai/idea-strategy` | جلب الاستراتيجية |
| `POST` | `/ai/idea-strategy/regenerate` | إعادة التوليد |
| `POST` | `/ai/idea-strategy/regenerate-custom` | إعادة التوليد بـ Custom Prompt |
| `POST` | `/ai/idea-strategy/chat` | شات |
| `POST` | `/ai/idea-strategy/chat/stream` | شات Streaming |

### 💼 Business Model
| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `POST` | `/ai/business-model` | توليد نموذج العمل |
| `GET` | `/ai/business-model` | جلب نموذج العمل |
| `POST` | `/ai/business-model/regenerate` | إعادة التوليد |
| `POST` | `/ai/business-model/regenerate-custom` | إعادة التوليد بـ Custom Prompt |
| `POST` | `/ai/business-model/chat` | شات |
| `POST` | `/ai/business-model/chat/stream` | شات Streaming |

### ⚙️ Functions List
| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `POST` | `/ai/functions-list` | توليد قائمة الوظائف |
| `GET` | `/ai/functions-list` | جلب قائمة الوظائف |
| `POST` | `/ai/functions-list/regenerate` | إعادة التوليد |
| `POST` | `/ai/functions-list/regenerate-custom` | إعادة التوليد بـ Custom Prompt |
| `POST` | `/ai/functions-list/chat` | شات |
| `POST` | `/ai/functions-list/chat/stream` | شات Streaming |

### 🗺️ MVP Planning
| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `POST` | `/ai/mvp-planning` | توليد خطة الـ MVP |
| `GET` | `/ai/mvp-planning` | جلب خطة الـ MVP |
| `POST` | `/ai/mvp-planning/regenerate` | إعادة التوليد |
| `POST` | `/ai/mvp-planning/regenerate-custom` | إعادة التوليد بـ Custom Prompt |
| `POST` | `/ai/mvp-planning/chat` | شات |
| `POST` | `/ai/mvp-planning/chat/stream` | شات Streaming |

### 💰 Unit Economics
| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `POST` | `/ai/unit-economics` | توليد الاقتصاديات |
| `GET` | `/ai/unit-economics` | جلب الاقتصاديات |
| `POST` | `/ai/unit-economics/regenerate` | إعادة التوليد |
| `POST` | `/ai/unit-economics/regenerate-custom` | إعادة التوليد بـ Custom Prompt |
| `POST` | `/ai/unit-economics/chat` | شات |
| `POST` | `/ai/unit-economics/chat/stream` | شات Streaming |

### 🚀 Go-To-Market
| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `POST` | `/ai/go-to-market` | توليد استراتيجية الإطلاق |
| `GET` | `/ai/go-to-market` | جلب الاستراتيجية |
| `POST` | `/ai/go-to-market/regenerate` | إعادة التوليد |
| `POST` | `/ai/go-to-market/regenerate-custom` | إعادة التوليد بـ Custom Prompt |
| `POST` | `/ai/go-to-market/chat` | شات |
| `POST` | `/ai/go-to-market/chat/stream` | شات Streaming |

### 💬 Chat
| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `POST` | `/ai/chat` | الشات الأساسي مع الـ AI |
| `POST` | `/ai/chat/stream` | شات Streaming |
| `POST` | `/ai/general-chat` | General Chatbot |
| `POST` | `/ai/general-chat/stream` | General Chatbot Streaming |
| `POST` | `/ai/explain` | شرح أي محتوى بالـ AI |

---

## 🔒 نظام حماية الاستهلاك (Rate Limiting)

كل الـ AI Endpoints محمية تلقائياً بالـ Dependency `check_ai_usage` اللي بتعمل:
1. تتحقق من باقة المستخدم (Plan)
2. لو الباقة فيها `"ai_analysis": false` → ترجع **403 Forbidden**
3. لو اليوزر خلص طلباته → ترجع **429 Too Many Requests**
4. لو كل حاجة تمام → تسمح بالطلب وتزود العداد +1

---

## 🖥️ Swagger UI (التوثيق التفاعلي)

```
http://localhost:8000/docs
```

ابحثي عن الـ Sections اللي بتبدأ بـ `AI -`

---

## ⚠️ ملاحظة مهمة للـ AI Assistants (Cursor / Copilot)

لو الـ AI في الـ IDE قالك "مفيش integration"، ده لأنه بيقرأ بس الملفات المفتوحة. افتحي الملف ده يدوياً:
```
app/api/v1/ai_pipeline.py
```
وساعتها هيشوف كل الـ 75+ endpoint.
