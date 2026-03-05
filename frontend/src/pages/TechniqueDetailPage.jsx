import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Clock } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";

/** Resolve a multilingual field: object → pick lang, string → pass through */
const loc = (field, lang) => {
  if (!field) return "";
  if (typeof field === "string") return field;
  return field[lang] || field.en || Object.values(field)[0] || "";
};

const TechniqueDetailPage = () => {
  const { id } = useParams();
  const [technique, setTechnique] = useState(null);
  const [loading, setLoading] = useState(true);
  const { language, getLocalizedPath } = useLanguage();
  const lang = language || "en";

  useEffect(() => {
    fetch("/techniques.json")
      .then((r) => r.json())
      .then((data) => setTechnique(data.find((t) => t.id === id) || null))
      .catch(() => setTechnique(null))
      .finally(() => setLoading(false));
  }, [id]);

  // SEO meta
  useEffect(() => {
    if (!technique) return;
    const prev = document.title;
    document.title = `${loc(technique.title, lang)} — Cooking Technique | Sous Chef Linguine`;
    const setMeta = (name, content) => {
      let el = document.querySelector(`meta[name="${name}"]`);
      if (!el) { el = document.createElement("meta"); el.setAttribute("name", name); document.head.appendChild(el); }
      el.setAttribute("content", content);
    };
    setMeta("description", loc(technique.description, lang));
    return () => { document.title = prev; };
  }, [technique, lang]);

  // JSON-LD
  useEffect(() => {
    if (!technique) return;
    const sid = "technique-detail-jsonld";
    let s = document.getElementById(sid);
    if (!s) { s = document.createElement("script"); s.id = sid; s.type = "application/ld+json"; document.head.appendChild(s); }
    s.textContent = JSON.stringify({
      "@context": "https://schema.org",
      "@type": "HowTo",
      "name": loc(technique.title, lang),
      "description": loc(technique.description, lang),
      "step": (technique.sections || []).map((sec) => ({
        "@type": "HowToStep",
        "name": loc(sec.title, lang),
        "text": loc(sec.content, lang),
      })),
    });
    return () => { const el = document.getElementById(sid); if (el) el.remove(); };
  }, [technique, lang]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FAF7F0] flex items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  if (!technique) {
    return (
      <div className="min-h-screen bg-[#FAF7F0] flex flex-col items-center justify-center gap-4" data-testid="technique-not-found">
        <p className="text-gray-600 text-lg">Technique not found.</p>
        <Link to={getLocalizedPath("/techniques")} className="text-[#6A1F2E] hover:underline flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" /> Back to all techniques
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAF7F0]" data-testid="technique-detail-page">
      <article className="max-w-3xl mx-auto px-6 pt-12 pb-24">
        <Link
          to={getLocalizedPath("/techniques")}
          className="inline-flex items-center gap-1 text-sm text-[#6A1F2E] hover:text-[#8B2840] mb-8 transition-colors"
          data-testid="back-link"
        >
          <ArrowLeft className="h-4 w-4" /> All Techniques
        </Link>

        <h1 className="text-4xl font-serif text-[#1E1E1E] mb-4" data-testid="technique-title">
          {loc(technique.title, lang)}
        </h1>

        <div className="flex items-center gap-3 mb-6">
          <span className="text-xs font-medium px-3 py-1 rounded-full bg-[#6A1F2E]/10 text-[#6A1F2E]">
            {technique.category}
          </span>
          <span className="text-xs font-medium px-3 py-1 rounded-full bg-gray-100 text-gray-600">
            {technique.level}
          </span>
          <span className="flex items-center text-xs text-gray-400">
            <Clock className="h-3 w-3 mr-1" />
            {technique.readTime}
          </span>
        </div>

        <p className="text-gray-700 text-lg leading-relaxed mb-10" data-testid="technique-description">
          {loc(technique.description, lang)}
        </p>

        <div className="space-y-8">
          {technique.sections?.map((section, i) => (
            <section key={i} className="bg-white rounded-lg p-6 shadow-sm" data-testid={`section-${i}`}>
              <h2 className="text-xl font-serif text-[#1E1E1E] mb-3">
                {loc(section.title, lang)}
              </h2>
              <p className="text-gray-700 whitespace-pre-line leading-relaxed">
                {loc(section.content, lang)}
              </p>
            </section>
          ))}
        </div>
      </article>
    </div>
  );
};

export default TechniqueDetailPage;
