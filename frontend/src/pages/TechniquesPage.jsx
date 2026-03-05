import React, { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { Clock, ChevronRight } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";

function buildHowToSchema(techniques) {
  return {
    "@context": "https://schema.org",
    "@graph": techniques.map((t) => ({
      "@type": "HowTo",
      "name": t.title,
      "description": t.description,
      "step": (t.sections || []).map((s) => ({
        "@type": "HowToStep",
        "text": s.content,
      })),
    })),
  };
}

const CATEGORY_ORDER = [
  "Dry Heat",
  "Moist Heat",
  "Combination",
  "Sauce Technique",
  "Knife Skills",
  "Preparation",
  "Preservation",
  "Flavor Development",
];

function slugifyCategory(cat) {
  return cat.toLowerCase().replace(/\s+/g, "-");
}

const TechniquesPage = () => {
  const [techniques, setTechniques] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { getLocalizedPath } = useLanguage();

  useEffect(() => {
    fetch("/techniques.json")
      .then((r) => {
        if (!r.ok) throw new Error("Failed to fetch");
        return r.json();
      })
      .then(setTechniques)
      .catch(() => setError("Unable to load techniques."))
      .finally(() => setLoading(false));
  }, []);

  // SEO meta
  useEffect(() => {
    const prev = document.title;
    document.title = "Cooking Techniques | Sous Chef Linguine";
    const setMeta = (name, content) => {
      let el = document.querySelector(`meta[name="${name}"]`);
      if (!el) { el = document.createElement("meta"); el.setAttribute("name", name); document.head.appendChild(el); }
      el.setAttribute("content", content);
    };
    setMeta("description", "Learn 20 essential cooking techniques — from blanching to flambe. Step-by-step guides for every skill level.");
    setMeta("title", "Cooking Techniques | Sous Chef Linguine");
    let canonical = document.querySelector('link[rel="canonical"]');
    if (canonical) canonical.href = "https://www.souscheflinguine.com/en/techniques";
    return () => { document.title = prev; };
  }, []);

  // JSON-LD
  useEffect(() => {
    if (!techniques.length) return;
    const id = "techniques-jsonld";
    let s = document.getElementById(id);
    if (!s) { s = document.createElement("script"); s.id = id; s.type = "application/ld+json"; document.head.appendChild(s); }
    s.textContent = JSON.stringify(buildHowToSchema(techniques));
    return () => { const el = document.getElementById(id); if (el) el.remove(); };
  }, [techniques]);

  const grouped = useMemo(() => {
    const map = {};
    techniques.forEach((t) => {
      const cat = t.category || "Other";
      if (!map[cat]) map[cat] = [];
      map[cat].push(t);
    });
    return CATEGORY_ORDER.filter((c) => map[c]).map((c) => ({ name: c, items: map[c] }));
  }, [techniques]);

  return (
    <div className="min-h-screen bg-[#FAF7F0]" data-testid="techniques-page">
      <section className="max-w-5xl mx-auto px-6 pt-16 pb-24">
        <h1 className="text-4xl sm:text-5xl font-serif text-[#1E1E1E] mb-3 text-center">
          Cooking Techniques
        </h1>
        <p className="text-center text-gray-500 mb-10 max-w-xl mx-auto">
          A categorized library of essential culinary methods — from dry heat basics to advanced preservation.
        </p>

        {/* Anchor navigation */}
        {grouped.length > 0 && (
          <nav
            className="flex flex-wrap justify-center gap-x-1 gap-y-2 mb-14"
            aria-label="Technique categories"
            data-testid="category-nav"
          >
            {grouped.map((g, i) => (
              <React.Fragment key={g.name}>
                {i > 0 && <span className="text-gray-300 select-none hidden sm:inline" aria-hidden="true">|</span>}
                <a
                  href={`#${slugifyCategory(g.name)}`}
                  className="text-sm font-medium text-[#6A1F2E] hover:text-[#8B2840] transition-colors px-2 py-1"
                  data-testid={`nav-${slugifyCategory(g.name)}`}
                >
                  {g.name}
                </a>
              </React.Fragment>
            ))}
          </nav>
        )}

        {loading && <p className="text-center text-gray-500">Loading techniques...</p>}
        {error && <p className="text-center text-red-500">{error}</p>}
        {!loading && techniques.length === 0 && <p className="text-center text-gray-500">No techniques available yet.</p>}

        {/* Category sections */}
        <div className="space-y-16">
          {grouped.map((group) => (
            <section
              key={group.name}
              id={slugifyCategory(group.name)}
              className="scroll-mt-24"
              data-testid={`section-${slugifyCategory(group.name)}`}
            >
              <h2 className="text-2xl font-serif text-[#1E1E1E] mb-6 border-b border-[#E8E4DC] pb-3">
                {group.name}
              </h2>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {group.items.map((tech) => (
                  <Link
                    key={tech.id}
                    to={getLocalizedPath(`/techniques/${tech.id}`)}
                    className="group bg-white rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow border border-transparent hover:border-[#6A1F2E]/10"
                    data-testid={`technique-card-${tech.id}`}
                  >
                    <article>
                      <h3 className="text-lg font-serif text-[#1E1E1E] group-hover:text-[#6A1F2E] transition-colors flex items-center justify-between">
                        {tech.title}
                        <ChevronRight className="h-4 w-4 opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all text-[#6A1F2E]" />
                      </h3>
                      <div className="flex items-center gap-2 mt-2 mb-3">
                        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-[#FAF7F0] text-gray-600">
                          {tech.level}
                        </span>
                        <span className="flex items-center text-xs text-gray-400">
                          <Clock className="h-3 w-3 mr-1" />
                          {tech.readTime}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 line-clamp-2">
                        {tech.description}
                      </p>
                    </article>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>
      </section>
    </div>
  );
};

export default TechniquesPage;
