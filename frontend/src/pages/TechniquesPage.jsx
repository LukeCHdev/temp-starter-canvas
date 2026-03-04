import React, { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";

const TechniquesPage = () => {
  const [techniques, setTechniques] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTechniques = async () => {
      try {
        const res = await fetch("/api/techniques");
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

  return (
    <>
      <Helmet prioritizeSeoTags>
        <title>Cooking Techniques | Sous Chef Linguine</title>
        <meta
          name="description"
          content="Learn essential cooking techniques including frying, sauces, knife skills, and more."
        />
      </Helmet>

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
                key={tech.slug}
                className="bg-white p-8 rounded-xl shadow-sm"
              >
                <h2 className="text-2xl font-serif mb-2">
                  {tech.title}
                </h2>

                <p className="text-sm text-gray-500 mb-4">
                  {tech.category} • {tech.difficulty} • {tech.readTime} min read
                </p>

                <p className="text-gray-700 mb-6">
                  {tech.introduction}
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