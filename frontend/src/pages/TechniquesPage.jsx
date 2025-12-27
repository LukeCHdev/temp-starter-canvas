import React from 'react';
import { Helmet } from 'react-helmet-async';
import { Construction } from 'lucide-react';

const TechniquesPage = () => {
    return (
        <>
            <Helmet prioritizeSeoTags>
                <meta name="robots" content="noindex, nofollow" data-rh="true" />
                <title>Techniques (Coming Soon) | Sous Chef Linguine</title>
            </Helmet>
            <div className="min-h-screen bg-[#FAF7F0]" data-testid="techniques-page">
                <section className="max-w-4xl mx-auto px-4 py-16 text-center">
                    <Construction className="w-16 h-16 text-amber-600 mx-auto mb-6" />
                    <h1 className="text-4xl font-serif text-[#1E1E1E] mb-4">Cooking Techniques</h1>
                    <p className="text-lg text-gray-600 mb-2">This section is under construction.</p>
                    <p className="text-gray-500">We're working on comprehensive guides for traditional cooking techniques.</p>
                </section>
            </div>
        </>
    );
};

export default TechniquesPage;