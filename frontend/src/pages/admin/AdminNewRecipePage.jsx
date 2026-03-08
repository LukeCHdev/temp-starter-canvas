import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Check, AlertCircle, Copy, FileJson } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = import.meta.env.VITE_BACKEND_URL;

// Example JSON template
const EXAMPLE_JSON = {
    "recipe_name": "Spaghetti alla Carbonara",
    "origin_country": "Italy",
    "origin_region": "Lazio",
    "origin_language": "it",
    "authenticity_level": 1,
    "history_summary": "A Roman pasta dish documented by traditional institutions...",
    "characteristic_profile": "Rich, salty, creamy texture with smoky guanciale and pecorino romano.",
    "no_no_rules": [
        "Never use cream",
        "Never use garlic or onion",
        "Must use guanciale, not pancetta or bacon"
    ],
    "special_techniques": [
        "mantecatura (creaming with pasta water)",
        "tempering eggs off heat"
    ],
    "technique_links": [
        {
            "technique": "mantecatura",
            "url": "https://youtube.com/example",
            "description": "How to cream pasta properly"
        }
    ],
    "ingredients": [
        {"item": "Spaghetti", "amount": "380", "unit": "g", "notes": ""},
        {"item": "Guanciale", "amount": "150", "unit": "g", "notes": "cut into strips"}
    ],
    "instructions": [
        "Cook the guanciale in a cold pan until crispy",
        "Mix egg yolks with pecorino and black pepper",
        "Cook pasta al dente, reserve pasta water",
        "Combine off heat using mantecatura technique"
    ],
    "wine_pairing": {
        "recommended_wines": [
            {"name": "Frascati Superiore DOCG", "region": "Lazio", "reason": "High acidity cuts through richness"}
        ],
        "notes": "Central Italian whites work best"
    }
};

export const AdminNewRecipePage = () => {
    const [jsonInput, setJsonInput] = useState('');
    const [validationResult, setValidationResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const getAuthHeaders = () => {
        const token = localStorage.getItem('admin_token');
        return { Authorization: `Bearer ${token}` };
    };

    const handleValidate = () => {
        try {
            const parsed = JSON.parse(jsonInput);
            
            // Basic validation
            if (!parsed.recipe_name) {
                setValidationResult({ valid: false, error: 'recipe_name is required' });
                return;
            }
            
            setValidationResult({ 
                valid: true, 
                parsed,
                message: `Recipe "${parsed.recipe_name}" is valid!`
            });
            toast.success('JSON is valid!');
        } catch (error) {
            setValidationResult({ valid: false, error: `Invalid JSON: ${error.message}` });
            toast.error('Invalid JSON format');
        }
    };

    const handleSave = async () => {
        if (!validationResult?.valid) {
            toast.error('Please validate JSON first');
            return;
        }

        setLoading(true);
        try {
            const response = await axios.post(
                `${API_URL}/api/admin/import/json`,
                { recipe_json: validationResult.parsed },
                { headers: getAuthHeaders() }
            );

            if (response.data.success) {
                toast.success(`Recipe saved with slug: ${response.data.slug}`);
                navigate('/admin/recipes');
            }
        } catch (error) {
            if (error.response?.status === 401) {
                toast.error('Session expired. Please login again.');
                navigate('/admin/login');
            } else {
                toast.error(error.response?.data?.detail || 'Failed to save recipe');
            }
        } finally {
            setLoading(false);
        }
    };

    const loadExample = () => {
        setJsonInput(JSON.stringify(EXAMPLE_JSON, null, 2));
        setValidationResult(null);
    };

    const copyExample = () => {
        navigator.clipboard.writeText(JSON.stringify(EXAMPLE_JSON, null, 2));
        toast.success('Example JSON copied to clipboard!');
    };

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="flex items-center gap-4 mb-6">
                    <Link to="/admin/recipes">
                        <Button variant="outline" size="sm">
                            <ArrowLeft className="w-4 h-4 mr-2" /> Back
                        </Button>
                    </Link>
                    <h1 className="text-2xl font-bold">Add New Recipe</h1>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                    {/* JSON Input */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <FileJson className="w-5 h-5" /> Paste JSON
                            </CardTitle>
                            <CardDescription>
                                Paste your Sous-Chef Linguine JSON here
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <Textarea
                                placeholder="Paste recipe JSON here..."
                                value={jsonInput}
                                onChange={(e) => {
                                    setJsonInput(e.target.value);
                                    setValidationResult(null);
                                }}
                                className="font-mono text-sm min-h-[400px]"
                            />
                            <div className="flex gap-2">
                                <Button onClick={handleValidate} variant="outline">
                                    Validate JSON
                                </Button>
                                <Button
                                    onClick={handleSave}
                                    disabled={!validationResult?.valid || loading}
                                    className="bg-amber-700 hover:bg-amber-800"
                                >
                                    {loading ? 'Saving...' : 'Save Recipe'}
                                </Button>
                            </div>

                            {validationResult && (
                                <Alert variant={validationResult.valid ? 'default' : 'destructive'}>
                                    {validationResult.valid ? (
                                        <Check className="h-4 w-4" />
                                    ) : (
                                        <AlertCircle className="h-4 w-4" />
                                    )}
                                    <AlertDescription>
                                        {validationResult.valid
                                            ? validationResult.message
                                            : validationResult.error}
                                    </AlertDescription>
                                </Alert>
                            )}
                        </CardContent>
                    </Card>

                    {/* Example Template */}
                    <Card>
                        <CardHeader>
                            <CardTitle>JSON Template</CardTitle>
                            <CardDescription>
                                Use this template as a starting point
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="bg-gray-100 rounded-lg p-4 overflow-auto max-h-[400px]">
                                <pre className="text-xs font-mono text-gray-700 whitespace-pre-wrap">
                                    {JSON.stringify(EXAMPLE_JSON, null, 2)}
                                </pre>
                            </div>
                            <div className="flex gap-2">
                                <Button onClick={loadExample} variant="outline">
                                    Load Example
                                </Button>
                                <Button onClick={copyExample} variant="outline">
                                    <Copy className="w-4 h-4 mr-2" /> Copy
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default AdminNewRecipePage;
