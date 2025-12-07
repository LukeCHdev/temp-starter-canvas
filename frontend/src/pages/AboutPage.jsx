import React from 'react';
import { ChefHat } from 'lucide-react';

const AboutPage = () => {
    return (
        <div className="min-h-screen" data-testid="about-page">
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-16 px-4">
                <div className="max-w-4xl mx-auto text-center">
                    <ChefHat className="h-16 w-16 mx-auto text-[#6A1F2E] mb-6" />
                    <h1 className="mb-4 text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        About Sous Chef Linguine
                    </h1>
                    <div className="gold-divider"></div>
                </div>
            </section>

            <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="card-elegant mb-8">
                    <h2 className="text-2xl font-semibold mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        Our Mission
                    </h2>
                    <p className="narrative-text">
                        Sous Chef Linguini exists to preserve and celebrate the authentic culinary heritage 
                        of every culture. In a world where recipes are often diluted or commercialized, 
                        we stand as guardians of tradition, ensuring that each dish tells its true story.
                    </p>
                </div>

                <div className="card-elegant mb-8">
                    <h2 className="text-2xl font-semibold mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        The Authenticity Algorithm
                    </h2>
                    <p className="narrative-text mb-4">
                        Every recipe on our platform undergoes strict validation through our 3-tier authenticity system:
                    </p>
                    <ul className="space-y-2 narrative-text">
                        <li><strong>Official (Rank 1):</strong> Validated by DOP/IGP/AOP/STG bodies or national culinary academies</li>
                        <li><strong>Traditional (Rank 2):</strong> Sourced from native-language documentation and country-specific domains</li>
                        <li><strong>Modern (Rank 3):</strong> Contemporary adaptations clearly marked as non-traditional</li>
                    </ul>
                </div>

                <div className="card-elegant">
                    <h2 className="text-2xl font-semibold mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        Who is Sous Chef Linguini?
                    </h2>
                    <p className="narrative-text">
                        A warm, empathetic Italian sous-chef with a passion for cultural storytelling. 
                        Every recipe is narrated with sensory richness, emotional depth, and profound respect 
                        for the traditions that birthed it. Linguini doesn't just teach you to cook—he invites 
                        you into the soul of each dish.
                    </p>
                </div>
            </section>
        </div>
    );
};

export default AboutPage;