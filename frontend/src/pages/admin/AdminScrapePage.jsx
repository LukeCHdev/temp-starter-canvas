import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Link as LinkIcon, Loader2, Eye, Save, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const AdminScrapePage = () => {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [scrapedRecipe, setScrapedRecipe] = useState(null);
    const [editedJson, setEditedJson] = useState('');
    const navigate = useNavigate();

    const getAuthHeaders = () => {
        const token = localStorage.getItem('admin_token');
        return { Authorization: `Bearer ${token}` };
    };

    const handleScrape = async () => {
        if (!url.trim()) {
            toast.error('Please enter a URL');
            return;
        }

        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            toast.error('Please enter a valid URL (http:// or https://)');
            return;
        }

        setLoading(true);
        setScrapedRecipe(null);

        try {
            const response = await axios.post(
                `${API_URL}/api/admin/import/scrape`,
                { url },
                { headers: getAuthHeaders() }
            );

            if (response.data.success) {
                setScrapedRecipe(response.data.recipe_json);
                setEditedJson(JSON.stringify(response.data.recipe_json, null, 2));
                toast.success('Recipe extracted! Review and save.');
            }
        } catch (error) {
            if (error.response?.status === 401) {
                toast.error('Session expired. Please login again.');
                navigate('/admin/login');
            } else {
                toast.error(error.response?.data?.detail || 'Failed to scrape URL');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        try {
            const parsed = JSON.parse(editedJson);

            if (!parsed.recipe_name) {
                toast.error('recipe_name is required');
                return;
            }

            setSaving(true);
            const response = await axios.post(
                `${API_URL}/api/admin/import/json`,
                { recipe_json: parsed },
                { headers: getAuthHeaders() }
            );

            if (response.data.success) {
                toast.success(`Recipe saved with slug: ${response.data.slug}`);
                navigate('/admin/recipes');
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
        if (scrapedRecipe) {
            setEditedJson(JSON.stringify(scrapedRecipe, null, 2));
            toast.info('Reset to scraped version');
        }
    };

    const formatJSON = () => {
        try {
            const parsed = JSON.parse(editedJson);
            setEditedJson(JSON.stringify(parsed, null, 2));
            toast.success('JSON formatted');
        } catch {
            toast.error('Cannot format invalid JSON');
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center gap-4 mb-6">
                    <Link to="/admin/recipes">
                        <Button variant="outline" size="sm">
                            <ArrowLeft className="w-4 h-4 mr-2" /> Back
                        </Button>
                    </Link>
                    <h1 className="text-2xl font-bold">Scrape Recipe from URL</h1>
                </div>

                {/* URL Input */}
                <Card className="mb-6">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <LinkIcon className="w-5 h-5" /> Enter Recipe URL
                        </CardTitle>
                        <CardDescription>
                            Paste a URL from an authentic recipe source. The AI will extract and normalize the recipe.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex gap-2">
                            <Input
                                placeholder="https://example.com/recipe/..."
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                className="flex-1"
                            />
                            <Button
                                onClick={handleScrape}
                                disabled={loading}
                                className="bg-amber-700 hover:bg-amber-800"
                            >
                                {loading ? (
                                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Scraping...</>
                                ) : (
                                    'Scrape & Generate'
                                )}
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {/* Scraped Result */}
                {scrapedRecipe && (
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center justify-between">
                                <span>Review Extracted Recipe</span>
                                <div className="flex gap-2">
                                    <Button onClick={formatJSON} variant="outline" size="sm">
                                        Format
                                    </Button>
                                    <Button onClick={handleReset} variant="outline" size="sm">
                                        <RefreshCw className="w-4 h-4 mr-2" /> Reset
                                    </Button>
                                </div>
                            </CardTitle>
                            <CardDescription>
                                Review and edit the extracted recipe before saving
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <Alert>
                                <AlertDescription>
                                    <strong>Source:</strong> {url}
                                </AlertDescription>
                            </Alert>

                            <Textarea
                                value={editedJson}
                                onChange={(e) => setEditedJson(e.target.value)}
                                className="font-mono text-sm min-h-[500px]"
                            />

                            <div className="flex gap-2">
                                <Button
                                    onClick={handleSave}
                                    disabled={saving}
                                    className="bg-amber-700 hover:bg-amber-800"
                                >
                                    <Save className="w-4 h-4 mr-2" />
                                    {saving ? 'Saving...' : 'Save Recipe'}
                                </Button>
                                <Link to={`/recipe/${scrapedRecipe.slug || 'preview'}`} target="_blank">
                                    <Button variant="outline" disabled={!scrapedRecipe.slug}>
                                        <Eye className="w-4 h-4 mr-2" /> Preview
                                    </Button>
                                </Link>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Tips */}
                {!scrapedRecipe && (
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-sm">Tips for Best Results</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ul className="text-sm text-gray-600 space-y-2">
                                <li>• Use URLs from official culinary institutions (e.g., Accademia Italiana della Cucina)</li>
                                <li>• Recipe pages with structured data work best</li>
                                <li>• The AI will attempt to identify authenticity level and origin</li>
                                <li>• Always review and edit the result before saving</li>
                                <li>• Add technique_links manually for instructional videos</li>
                            </ul>
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    );
};

export default AdminScrapePage;
