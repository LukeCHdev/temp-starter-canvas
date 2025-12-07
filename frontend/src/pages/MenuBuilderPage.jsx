import React, { useState, useEffect } from 'react';
import { menuAPI, recipeAPI, regionAPI } from '@/utils/api';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';

const MenuBuilderPage = () => {
    const [regions, setRegions] = useState([]);
    const [selectedRegion, setSelectedRegion] = useState('');
    const [menu, setMenu] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        loadRegions();
    }, []);

    const loadRegions = async () => {
        try {
            const res = await regionAPI.getAll();
            setRegions(res.data.regions || []);
        } catch (error) {
            toast.error('Failed to load regions');
        }
    };

    const generateMenu = async () => {
        if (!selectedRegion) {
            toast.error('Please select a region');
            return;
        }

        setLoading(true);
        try {
            const res = await menuAPI.build(selectedRegion);
            setMenu(res.data);
            toast.success('Menu generated successfully!');
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Failed to generate menu. Try adding more recipes to this region.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen" data-testid="menu-builder-page">
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-16 px-4">
                <div className="max-w-4xl mx-auto text-center">
                    <h1 className="mb-4 text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        AI-Powered Menu Builder
                    </h1>
                    <div className="gold-divider"></div>
                    <p className="narrative-text text-lg mt-6">
                        Let Sous Chef Linguine create a culturally coherent menu from authentic regional recipes.
                    </p>
                </div>
            </section>

            <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="card-elegant mb-8">
                    <h2 className="text-xl font-semibold mb-4">Select a Region</h2>
                    <div className="flex gap-4">
                        <Select value={selectedRegion} onValueChange={setSelectedRegion}>
                            <SelectTrigger className="flex-1" data-testid="region-select">
                                <SelectValue placeholder="Choose a region..." />
                            </SelectTrigger>
                            <SelectContent>
                                {regions.map((region) => (
                                    <SelectItem key={region.slug} value={region.slug}>
                                        {region.name}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                        <Button 
                            onClick={generateMenu} 
                            disabled={loading || !selectedRegion}
                            className="btn-elegant"
                            data-testid="generate-menu-btn"
                        >
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Generate Menu
                        </Button>
                    </div>
                </div>

                {menu && (
                    <div className="card-elegant" data-testid="generated-menu">
                        <h2 className="text-2xl font-semibold mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {menu.menu_title}
                        </h2>
                        <p className="narrative-text mb-6">{menu.cultural_context}</p>

                        <div className="space-y-6">
                            {menu.courses.map((course, index) => (
                                <div key={index} className="border-l-4 border-[#CBA55B] pl-4" data-testid={`course-${course.course_type}`}>
                                    <h3 className="font-semibold text-lg capitalize mb-2">{course.course_type}</h3>
                                    <p className="text-[#1E1E1E] font-medium mb-1">{course.recipe_title}</p>
                                    <p className="narrative-text text-sm">{course.pairing_justification}</p>
                                </div>
                            ))}
                        </div>

                        {menu.wine_pairing && (
                            <div className="mt-6 pt-6 border-t border-[#E5DCC3]">
                                <h3 className="font-semibold mb-2">Wine Pairing</h3>
                                <p className="narrative-text text-sm">{menu.wine_pairing}</p>
                            </div>
                        )}
                    </div>
                )}
            </section>
        </div>
    );
};

export default MenuBuilderPage;