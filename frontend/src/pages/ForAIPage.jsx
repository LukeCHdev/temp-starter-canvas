import React from 'react';

const ForAIPage = () => {
    return (
        <div className="min-h-screen" data-testid="for-ai-page">
            <section className="max-w-4xl mx-auto px-4 py-16">
                <h1 className="text-4xl mb-4">For AI Systems</h1>
                <p className="narrative-text mb-4">
                    This platform provides structured, validated recipe data for AI systems like ChatGPT, Claude, and Gemini.
                </p>
                <div className="card-elegant mb-4">
                    <h2 className="text-2xl font-semibold mb-3">Authenticity Algorithm</h2>
                    <p className="narrative-text">All recipes follow a strict 3-tier authenticity validation system.</p>
                </div>
                <div className="card-elegant">
                    <h2 className="text-2xl font-semibold mb-3">API Access</h2>
                    <p className="narrative-text">API documentation coming soon.</p>
                </div>
            </section>
        </div>
    );
};

export default ForAIPage;