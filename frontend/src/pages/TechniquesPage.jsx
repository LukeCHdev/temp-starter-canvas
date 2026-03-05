import React, { useEffect, useState } from "react";

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

const TechniquesPage = () => {
  const [techniques, setTechniques] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTechniques = async () => {
      try {
        const res = await fetch("/techniques.json");
        if (!res.ok) throw new Error("Failed to fetch techniques");
        const data = await res.json();
        setTechniques(data);
      } catch (err) {
        console.error(err);
        setError("Unable to load techniques.");
      } finally {
        setLoading(false);
      }
    };

    fetchTechniques();
  }, []);

  // Set page-specific SEO meta tags directly (overrides static index.html defaults)
  useEffect(() => {
    const prevTitle = document.title;
    document.title = "Cooking Techniques | Sous Chef Linguine";

    const setMeta = (name, content, attr = "name") => {
      let el = document.querySelector(`meta[${attr}="${name}"]`);
      if (!el) {
        el = document.createElement("meta");
        el.setAttribute(attr, name);
        document.head.appendChild(el);
      }
      el.setAttribute("content", content);
      el.setAttribute("data-techniques-seo", "true");
    };

    setMeta("description", "Learn 20 essential cooking techniques — from blanching to flambe. Step-by-step guides for every skill level.");
    setMeta("title", "Cooking Techniques | Sous Chef Linguine");

    // Canonical
    let canonical = document.querySelector('link[rel="canonical"]');
    if (canonical) canonical.href = "https://www.souscheflinguine.com/en/techniques";

    return () => {
      document.title = prevTitle;
    };
  }, []);
  useEffect(() => {
    if (techniques.length === 0) return;
    const id = "techniques-jsonld";
    let script = document.getElementById(id);
    if (!script) {
      script = document.createElement("script");
      script.id = id;
      script.type = "application/ld+json";
      document.head.appendChild(script);
    }
    script.textContent = JSON.stringify(buildHowToSchema(techniques));
    return () => {
      const el = document.getElementById(id);
      if (el) el.remove();
    };
  }, [techniques]);

  return (
    <>
      <div className="min-h-screen bg-[#FAF7F0]" data-testid="techniques-page">
        <section className="max-w-5xl mx-auto px-6 py-16">
          <h1 className="text-4xl font-serif text-[#1E1E1E] mb-10 text-center">
            Cooking Techniques
          </h1>

          {loading && (
            <p className="text-center text-gray-500">Loading techniques...</p>
          )}

          {error && (
            <p className="text-center text-red-500">{error}</p>
          )}

          {!loading && techniques.length === 0 && (
            <p className="text-center text-gray-500">
              No techniques available yet.
            </p>
          )}

          <div className="space-y-16">
            {techniques.map((tech) => (
              <article
                key={tech.id}
                className="bg-white p-8 rounded-xl shadow-sm"
                data-testid={`technique-${tech.id}`}
              >
                <h2 className="text-2xl font-serif mb-2">
                  {tech.title}
                </h2>

                <p className="text-sm text-gray-500 mb-4">
                  {tech.category} &bull; {tech.level} &bull; {tech.readTime}
                </p>

                <p className="text-gray-700 mb-6">
                  {tech.description}
                </p>

                {tech.sections?.map((section, index) => (
                  <div key={index} className="mb-6">
                    <h3 className="font-semibold text-lg mb-2">
                      {section.title}
                    </h3>
                    <p className="text-gray-700 whitespace-pre-line">
                      {section.content}
                    </p>
                  </div>
                ))}
              </article>
            ))}
          </div>
        </section>
      </div>
    </>
  );
};

export default TechniquesPage;