import React, { useEffect, useState } from 'react';
import { regionAPI } from '@/utils/api';
import { Globe } from 'lucide-react';
import { toast } from 'sonner';

const RegionsPage = () => {
    const [regions, setRegions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadRegions();
    }, []);

    const loadRegions = async () => {
        try {
            const res = await regionAPI.getAll();
            setRegions(res.data.regions || []);
        } catch (error) {
            toast.error('Failed to load regions');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen" data-testid="regions-page">
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-16 px-4">
                <div className="max-w-4xl mx-auto text-center">
                    <h1 className="mb-4 text-[#1E1E1E]" style={{ fontFamily: 'var(--font-heading)' }}>
                        Culinary Regions of the World
                    </h1>
                    <div className="gold-divider"></div>
                    <p className="narrative-text text-lg mt-6">
                        Explore authentic cuisines from every corner of the globe, each region 
                        preserving centuries of tradition and cultural heritage.
                    </p>
                </div>
            </section>

            <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
                {loading ? (
                    <div className="text-center py-12" data-testid="loading-state">
                        <p className="text-[#1E1E1E]/60">Loading regions...</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8" data-testid="regions-grid">
                        {regions.map((region) => (
                            <div key={region.slug} className="card-elegant" id={region.slug} data-testid={`region-${region.slug}`}>
                                <Globe className="h-12 w-12 text-[#CBA55B] mb-4" />
                                <h2 className="text-2xl font-semibold mb-3">{region.name}</h2>
                                <p className="narrative-text mb-4">{region.description}</p>
                                <div className="text-sm text-[#1E1E1E]/60">
                                    <strong>Countries:</strong> {region.countries.join(', ')}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>
        </div>
    );
};

export default RegionsPage;