import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Save, Eye, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = import.meta.env.VITE_BACKEND_URL;

export const AdminEditRecipePage = () => {
    const { slug } = useParams();
    const navigate = useNavigate();
    const [jsonInput, setJsonInput] = useState('');
    const [originalRecipe, setOriginalRecipe] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);

    const getAuthHeaders = () => {
        const token = localStorage.getItem('admin_token');
        return { Authorization: `Bearer ${token}` };
    };

    const fetchRecipe = async () => {
        try {
            const response = await axios.get(
                `${API_URL}/api/admin/recipes/${slug}`,
                { headers: getAuthHeaders() }
            );
            setOriginalRecipe(response.data.recipe);
            setJsonInput(JSON.stringify(response.data.recipe, null, 2));
            setError(null);
        } catch (error) {
            if (error.response?.status === 401) {
                toast.error('Session expired. Please login again.');
                navigate('/admin/login');
            } else if (error.response?.status === 404) {
                setError('Recipe not found');
            } else {
                setError('Failed to fetch recipe');
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRecipe();
    }, [slug]);

    const handleSave = async () => {
        try {
            const parsed = JSON.parse(jsonInput);
            
            setSaving(true);
            const response = await axios.put(
                `${API_URL}/api/admin/recipes/${slug}`,
                { recipe_data: parsed },
                { headers: getAuthHeaders() }
            );

            if (response.data.success) {
                toast.success('Recipe updated successfully!');
                
                // If slug changed, navigate to new URL
                if (response.data.slug !== slug) {
                    navigate(`/admin/recipes/${response.data.slug}/edit`);
                } else {
                    fetchRecipe(); // Refresh data
                }
            }
        } catch (error) {
            if (error instanceof SyntaxError) {
                toast.error('Invalid JSON format');
            } else if (error.response?.status === 401) {
                toast.error('Session expired. Please login again.');
                navigate('/admin/login');
            } else {
                toast.error(error.response?.data?.detail || 'Failed to save recipe');
            }
        } finally {
            setSaving(false);
        }
    };

    const handleReset = () => {
        if (window.confirm('Reset to original? All changes will be lost.')) {
            setJsonInput(JSON.stringify(originalRecipe, null, 2));
            toast.info('Reset to original');
        }
    };

    const formatJSON = () => {
        try {
            const parsed = JSON.parse(jsonInput);
            setJsonInput(JSON.stringify(parsed, null, 2));
            toast.success('JSON formatted');
        } catch (error) {
            toast.error('Invalid JSON - cannot format');
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-700"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gray-50 p-4">
                <div className="max-w-4xl mx-auto">
                    <Alert variant="destructive">
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                    <Link to="/admin/recipes" className="mt-4 inline-block">
                        <Button variant="outline">Back to Recipes</Button>
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-4">
                        <Link to="/admin/recipes">
                            <Button variant="outline" size="sm">
                                <ArrowLeft className="w-4 h-4 mr-2" /> Back
                            </Button>
                        </Link>
                        <div>
                            <h1 className="text-2xl font-bold">Edit Recipe</h1>
                            <p className="text-sm text-gray-500">Slug: {slug}</p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Link to={`/recipe/${slug}`} target="_blank">
                            <Button variant="outline" size="sm">
                                <Eye className="w-4 h-4 mr-2" /> Preview
                            </Button>
                        </Link>
                    </div>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                            <span>{originalRecipe?.recipe_name || 'Recipe'}</span>
                            <div className="flex gap-2">
                                <Button onClick={formatJSON} variant="outline" size="sm">
                                    Format JSON
                                </Button>
                                <Button onClick={handleReset} variant="outline" size="sm">
                                    <RefreshCw className="w-4 h-4 mr-2" /> Reset
                                </Button>
                            </div>
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <Textarea
                            value={jsonInput}
                            onChange={(e) => setJsonInput(e.target.value)}
                            className="font-mono text-sm min-h-[600px]"
                        />
                        <div className="flex gap-2">
                            <Button
                                onClick={handleSave}
                                disabled={saving}
                                className="bg-amber-700 hover:bg-amber-800"
                            >
                                <Save className="w-4 h-4 mr-2" />
                                {saving ? 'Saving...' : 'Save Changes'}
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default AdminEditRecipePage;
