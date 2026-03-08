import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Save, Wand2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';
import { ImageManager } from '@/components/admin/ImageManager';

const API_URL = process.env.REACT_APP_BACKEND_URL || import.meta?.env?.VITE_BACKEND_URL || '';

// Template for new recipe
const RECIPE_TEMPLATE = {
    recipe_name: "",
    origin_country: "",
    origin_region: "",
    origin_continent: "",
    dish_type: "",
    status: "draft",
    tradition_score: 5.0,
    innovation_score: 5.0,
    difficulty_score: 5.0,
    history_and_origin: "",
    description: "",
    ingredients: [],
    preparation_method: [],
    serving_suggestions: "",
    common_mistakes: [],
    tips_and_tricks: [],
    no_go_rules: [],
    photos: []
};

export const AdminNewRecipePage = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState(RECIPE_TEMPLATE);
    const [jsonMode, setJsonMode] = useState(false);
    const [jsonInput, setJsonInput] = useState(JSON.stringify(RECIPE_TEMPLATE, null, 2));
    const [saving, setSaving] = useState(false);
    const [tempImageUrl, setTempImageUrl] = useState(null);

    const getAuthHeaders = () => {
        const token = localStorage.getItem('admin_token');
        return { Authorization: `Bearer ${token}` };
    };

    const generateSlug = (name, country) => {
        return `${name}-${country}`
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-|-$/g, '');
    };

    const handleInputChange = (field, value) => {
        setFormData(prev => {
            const updated = { ...prev, [field]: value };
            
            // Auto-generate slug when name or country changes
            if (field === 'recipe_name' || field === 'origin_country') {
                const name = field === 'recipe_name' ? value : prev.recipe_name;
                const country = field === 'origin_country' ? value : prev.origin_country;
                if (name && country) {
                    updated.slug = generateSlug(name, country);
                }
            }
            
            setJsonInput(JSON.stringify(updated, null, 2));
            return updated;
        });
    };

    const handleJsonChange = (value) => {
        setJsonInput(value);
        try {
            const parsed = JSON.parse(value);
            setFormData(parsed);
        } catch (e) {
            // Invalid JSON, don't update form data
        }
    };

    // Handle image change from ImageManager
    const handleImageChange = (newImageUrl) => {
        setTempImageUrl(newImageUrl);
        const updated = { ...formData, image_url: newImageUrl, image_source: 'upload' };
        setFormData(updated);
        setJsonInput(JSON.stringify(updated, null, 2));
    };

    const handleImageRemove = () => {
        setTempImageUrl(null);
        const updated = { ...formData };
        delete updated.image_url;
        delete updated.image_source;
        delete updated.image_alt;
        setFormData(updated);
        setJsonInput(JSON.stringify(updated, null, 2));
    };

    const handleSave = async () => {
        try {
            let recipeData;
            
            if (jsonMode) {
                recipeData = JSON.parse(jsonInput);
            } else {
                recipeData = formData;
            }
            
            // Validate required fields
            if (!recipeData.recipe_name) {
                toast.error('Recipe name is required');
                return;
            }
            if (!recipeData.origin_country) {
                toast.error('Origin country is required');
                return;
            }

            // Generate slug if not set
            if (!recipeData.slug) {
                recipeData.slug = generateSlug(recipeData.recipe_name, recipeData.origin_country);
            }

            // Include image if set
            if (tempImageUrl) {
                recipeData.image_url = tempImageUrl;
                recipeData.image_source = 'upload';
            }

            setSaving(true);
            const response = await axios.post(
                `${API_URL}/api/admin/recipes/import-json`,
                { recipe_json: recipeData },
                { headers: getAuthHeaders() }
            );

            if (response.data.success) {
                toast.success('Recipe created successfully!');
                navigate(`/admin/recipes/${response.data.slug}/edit`);
            } else {
                toast.error(response.data.message || 'Failed to create recipe');
            }
        } catch (error) {
            if (error instanceof SyntaxError) {
                toast.error('Invalid JSON format');
            } else if (error.response?.status === 401) {
                toast.error('Session expired. Please login again.');
                navigate('/admin/login');
            } else {
                toast.error(error.response?.data?.detail || 'Failed to create recipe');
            }
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-4">
                        <Link to="/admin/recipes">
                            <Button variant="outline" size="sm">
                                <ArrowLeft className="w-4 h-4 mr-2" /> Back
                            </Button>
                        </Link>
                        <h1 className="text-2xl font-bold">New Recipe</h1>
                    </div>
                    <div className="flex gap-2">
                        <Button
                            variant={jsonMode ? "default" : "outline"}
                            size="sm"
                            onClick={() => setJsonMode(!jsonMode)}
                        >
                            {jsonMode ? 'Form Mode' : 'JSON Mode'}
                        </Button>
                    </div>
                </div>

                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Image Manager - Left Column */}
                    <div className="lg:col-span-1">
                        <ImageManager
                            currentImageUrl={tempImageUrl}
                            onImageChange={handleImageChange}
                            onImageRemove={handleImageRemove}
                            entityType="recipe"
                            entitySlug={null}
                            authHeaders={getAuthHeaders()}
                        />
                        <p className="text-sm text-gray-500 mt-2 px-2">
                            Note: Upload an image first, then save the recipe. The image will be linked to the recipe.
                        </p>
                    </div>

                    {/* Form/JSON Editor - Right Column */}
                    <div className="lg:col-span-2">
                        <Card>
                            <CardHeader>
                                <CardTitle>Recipe Details</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {jsonMode ? (
                                    <Textarea
                                        value={jsonInput}
                                        onChange={(e) => handleJsonChange(e.target.value)}
                                        className="font-mono text-sm min-h-[600px]"
                                        placeholder="Paste recipe JSON here..."
                                    />
                                ) : (
                                    <div className="space-y-4">
                                        {/* Basic Info */}
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <Label>Recipe Name *</Label>
                                                <Input
                                                    value={formData.recipe_name}
                                                    onChange={(e) => handleInputChange('recipe_name', e.target.value)}
                                                    placeholder="e.g., Spaghetti Carbonara"
                                                />
                                            </div>
                                            <div>
                                                <Label>Origin Country *</Label>
                                                <Input
                                                    value={formData.origin_country}
                                                    onChange={(e) => handleInputChange('origin_country', e.target.value)}
                                                    placeholder="e.g., Italy"
                                                />
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <Label>Origin Region</Label>
                                                <Input
                                                    value={formData.origin_region}
                                                    onChange={(e) => handleInputChange('origin_region', e.target.value)}
                                                    placeholder="e.g., Lazio"
                                                />
                                            </div>
                                            <div>
                                                <Label>Continent</Label>
                                                <Select
                                                    value={formData.origin_continent}
                                                    onValueChange={(value) => handleInputChange('origin_continent', value)}
                                                >
                                                    <SelectTrigger>
                                                        <SelectValue placeholder="Select continent" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="Europe">Europe</SelectItem>
                                                        <SelectItem value="Asia">Asia</SelectItem>
                                                        <SelectItem value="Africa">Africa</SelectItem>
                                                        <SelectItem value="North America">North America</SelectItem>
                                                        <SelectItem value="South America">South America</SelectItem>
                                                        <SelectItem value="Oceania">Oceania</SelectItem>
                                                        <SelectItem value="Middle East">Middle East</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <Label>Dish Type</Label>
                                                <Input
                                                    value={formData.dish_type}
                                                    onChange={(e) => handleInputChange('dish_type', e.target.value)}
                                                    placeholder="e.g., Pasta, Soup, Dessert"
                                                />
                                            </div>
                                            <div>
                                                <Label>Status</Label>
                                                <Select
                                                    value={formData.status}
                                                    onValueChange={(value) => handleInputChange('status', value)}
                                                >
                                                    <SelectTrigger>
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="draft">Draft</SelectItem>
                                                        <SelectItem value="published">Published</SelectItem>
                                                        <SelectItem value="unpublished">Unpublished</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>

                                        {/* Description */}
                                        <div>
                                            <Label>Description</Label>
                                            <Textarea
                                                value={formData.description}
                                                onChange={(e) => handleInputChange('description', e.target.value)}
                                                placeholder="Brief description of the dish..."
                                                rows={3}
                                            />
                                        </div>

                                        {/* History */}
                                        <div>
                                            <Label>History & Origin</Label>
                                            <Textarea
                                                value={formData.history_and_origin}
                                                onChange={(e) => handleInputChange('history_and_origin', e.target.value)}
                                                placeholder="The history and cultural background of this dish..."
                                                rows={4}
                                            />
                                        </div>

                                        {/* Slug preview */}
                                        {formData.slug && (
                                            <div className="p-3 bg-gray-100 rounded">
                                                <Label className="text-gray-600">Generated Slug</Label>
                                                <p className="font-mono text-sm">{formData.slug}</p>
                                            </div>
                                        )}

                                        <p className="text-sm text-gray-500">
                                            For more detailed editing (ingredients, steps, etc.), switch to JSON Mode or edit after creating.
                                        </p>
                                    </div>
                                )}

                                <div className="flex gap-2 pt-4">
                                    <Button
                                        onClick={handleSave}
                                        disabled={saving}
                                        className="bg-amber-700 hover:bg-amber-800"
                                    >
                                        <Save className="w-4 h-4 mr-2" />
                                        {saving ? 'Creating...' : 'Create Recipe'}
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminNewRecipePage;
