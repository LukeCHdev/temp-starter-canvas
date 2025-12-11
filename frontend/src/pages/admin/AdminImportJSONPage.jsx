import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, FileJson, Check, AlertCircle, Copy } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Minimal JSON template for quick import
const MINIMAL_TEMPLATE = {
    "recipe_name": "Recipe Name Here",
    "origin_country": "Italy",
    "origin_region": "Lazio",
    "authenticity_level": 2,
    "history_summary": "Brief history...",
    "characteristic_profile": "Taste and texture description...",
    "no_no_rules": ["Never do this", "Never do that"],
    "special_techniques": ["Technique 1"],
    "ingredients": [
        {"item": "Ingredient 1", "amount": "100", "unit": "g", "notes": ""}
    ],
    "instructions": ["Step 1", "Step 2", "Step 3"],
    "wine_pairing": {
        "recommended_wines": [
            {"name": "Wine Name", "region": "Region", "reason": "Why it pairs well"}
        ],
        "notes": "General notes"
    }
};

export const AdminImportJSONPage = () => {
    const [jsonInput, setJsonInput] = useState('');
    const [validationResult, setValidationResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [importedCount, setImportedCount] = useState(0);
    const navigate = useNavigate();

    const getAuthHeaders = () => {
        const token = localStorage.getItem('admin_token');
        return { Authorization: `Bearer ${token}` };
    };

    const handleValidate = () => {
        try {
            const parsed = JSON.parse(jsonInput);

            // Check if it's an array of recipes
            const recipes = Array.isArray(parsed) ? parsed : [parsed];

            // Validate each recipe
            const errors = [];
            recipes.forEach((recipe, index) => {
                if (!recipe.recipe_name) {
                    errors.push(`Recipe ${index + 1}: Missing recipe_name`);
                }
            });

            if (errors.length > 0) {
                setValidationResult({ valid: false, errors });
                return;
            }

            setValidationResult({
                valid: true,
                recipes,
                message: `${recipes.length} recipe(s) ready to import!`
            });
            toast.success('JSON is valid!');
        } catch (error) {
            setValidationResult({ valid: false, errors: [`Invalid JSON: ${error.message}`] });
            toast.error('Invalid JSON format');
        }
    };

    const handleImport = async () => {
        if (!validationResult?.valid) {
            toast.error('Please validate JSON first');
            return;
        }

        setLoading(true);
        let imported = 0;
        const errors = [];

        try {
            for (const recipe of validationResult.recipes) {
                try {
                    await axios.post(
                        `${API_URL}/api/admin/import/json`,
                        { recipe_json: recipe },
                        { headers: getAuthHeaders() }
                    );
                    imported++;
                } catch (error) {
                    errors.push(`${recipe.recipe_name}: ${error.response?.data?.detail || 'Failed'}`);
                }
            }

            setImportedCount(imported);
            if (imported > 0) {
                toast.success(`Imported ${imported} of ${validationResult.recipes.length} recipes!`);
            }
            if (errors.length > 0) {
                setValidationResult(prev => ({ ...prev, importErrors: errors }));
            }
        } catch (error) {
            if (error.response?.status === 401) {
                toast.error('Session expired. Please login again.');
                navigate('/admin/login');
            } else {
                toast.error('Import failed');
            }
        } finally {
            setLoading(false);
        }
    };

    const loadTemplate = () => {
        setJsonInput(JSON.stringify(MINIMAL_TEMPLATE, null, 2));
        setValidationResult(null);
    };

    const copyTemplate = () => {
        navigator.clipboard.writeText(JSON.stringify(MINIMAL_TEMPLATE, null, 2));
        toast.success('Template copied!');
    };

    const formatJSON = () => {
        try {
            const parsed = JSON.parse(jsonInput);
            setJsonInput(JSON.stringify(parsed, null, 2));
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
                    <h1 className="text-2xl font-bold">Import JSON</h1>
                </div>

                <div className="grid md:grid-cols-3 gap-6">
                    {/* JSON Input */}
                    <div className="md:col-span-2">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center justify-between">
                                    <span className="flex items-center gap-2">
                                        <FileJson className="w-5 h-5" /> Paste JSON
                                    </span>
                                    <Button onClick={formatJSON} variant="outline" size="sm">
                                        Format
                                    </Button>
                                </CardTitle>
                                <CardDescription>
                                    Paste one recipe or an array of recipes generated by ChatGPT / Sous-Chef Linguine
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <Textarea
                                    placeholder='Paste recipe JSON here... You can paste a single object {} or an array of objects [{}]'
                                    value={jsonInput}
                                    onChange={(e) => {
                                        setJsonInput(e.target.value);
                                        setValidationResult(null);
                                    }}
                                    className="font-mono text-sm min-h-[500px]"
                                />
                                <div className="flex gap-2">
                                    <Button onClick={handleValidate} variant="outline">
                                        Validate JSON
                                    </Button>
                                    <Button
                                        onClick={handleImport}
                                        disabled={!validationResult?.valid || loading}
                                        className="bg-amber-700 hover:bg-amber-800"
                                    >
                                        {loading ? 'Importing...' : 'Import Recipes'}
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
                                            {validationResult.valid ? (
                                                <div>
                                                    <p>{validationResult.message}</p>
                                                    {importedCount > 0 && (
                                                        <p className="text-green-600 mt-1">✓ {importedCount} imported successfully</p>
                                                    )}
                                                    {validationResult.importErrors?.length > 0 && (
                                                        <ul className="mt-2 text-red-600 text-sm">
                                                            {validationResult.importErrors.map((err, i) => (
                                                                <li key={i}>• {err}</li>
                                                            ))}
                                                        </ul>
                                                    )}
                                                </div>
                                            ) : (
                                                <ul>
                                                    {validationResult.errors.map((err, i) => (
                                                        <li key={i}>• {err}</li>
                                                    ))}
                                                </ul>
                                            )}
                                        </AlertDescription>
                                    </Alert>
                                )}
                            </CardContent>
                        </Card>
                    </div>

                    {/* Template */}
                    <div>
                        <Card>
                            <CardHeader>
                                <CardTitle>Quick Template</CardTitle>
                                <CardDescription>Minimal required fields</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="bg-gray-100 rounded-lg p-3 overflow-auto max-h-[400px]">
                                    <pre className="text-xs font-mono text-gray-700 whitespace-pre-wrap">
                                        {JSON.stringify(MINIMAL_TEMPLATE, null, 2)}
                                    </pre>
                                </div>
                                <div className="flex gap-2">
                                    <Button onClick={loadTemplate} variant="outline" size="sm" className="flex-1">
                                        Load
                                    </Button>
                                    <Button onClick={copyTemplate} variant="outline" size="sm" className="flex-1">
                                        <Copy className="w-4 h-4 mr-1" /> Copy
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>

                        <Card className="mt-4">
                            <CardHeader>
                                <CardTitle className="text-sm">Tips</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ul className="text-sm text-gray-600 space-y-2">
                                    <li>• Paste output from ChatGPT directly</li>
                                    <li>• Array format: [{`{}`}, {`{}`}]</li>
                                    <li>• Slugs are auto-generated</li>
                                    <li>• Duplicates are rejected</li>
                                </ul>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminImportJSONPage;
