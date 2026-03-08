import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Upload, FileSpreadsheet, Download, CheckCircle, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = import.meta.env.VITE_BACKEND_URL;

export const AdminImportCSVPage = () => {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const navigate = useNavigate();

    const getAuthHeaders = () => {
        const token = localStorage.getItem('admin_token');
        return { Authorization: `Bearer ${token}` };
    };

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile && selectedFile.type === 'text/csv') {
            setFile(selectedFile);
            setResult(null);
        } else {
            toast.error('Please select a valid CSV file');
        }
    };

    const handleUpload = async () => {
        if (!file) {
            toast.error('Please select a file first');
            return;
        }

        setLoading(true);
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await axios.post(
                `${API_URL}/api/admin/import/csv`,
                formData,
                {
                    headers: {
                        ...getAuthHeaders(),
                        'Content-Type': 'multipart/form-data'
                    }
                }
            );

            setResult(response.data);
            if (response.data.imported > 0) {
                toast.success(`Successfully imported ${response.data.imported} recipes!`);
            }
        } catch (error) {
            if (error.response?.status === 401) {
                toast.error('Session expired. Please login again.');
                navigate('/admin/login');
            } else {
                toast.error(error.response?.data?.detail || 'Import failed');
            }
        } finally {
            setLoading(false);
        }
    };

    const downloadTemplate = () => {
        const headers = [
            'recipe_name', 'origin_country', 'origin_region', 'origin_language',
            'authenticity_level', 'history_summary', 'characteristic_profile',
            'no_no_rules', 'special_techniques', 'ingredients', 'instructions',
            'wine_name_1', 'wine_region_1', 'wine_reason_1',
            'wine_name_2', 'wine_region_2', 'wine_reason_2',
            'wine_notes', 'photo_url', 'photo_credit',
            'youtube_url', 'youtube_title', 'source_url', 'source_type', 'source_language'
        ];

        const exampleRow = [
            'Spaghetti alla Carbonara', 'Italy', 'Lazio', 'it',
            '1', 'A Roman pasta dish...', 'Rich and creamy texture',
            'Never use cream;Never use garlic', 'mantecatura;tempering eggs',
            'Spaghetti:380:g:;Guanciale:150:g:cut into strips',
            'Cook guanciale;Mix eggs with cheese;Combine off heat',
            'Frascati', 'Lazio', 'High acidity',
            '', '', '',
            'Central Italian whites', '', '',
            '', '', '', '', ''
        ];

        const csv = [headers.join(','), exampleRow.join(',')].join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'sous_chef_recipe_template.csv';
        a.click();
        window.URL.revokeObjectURL(url);
        toast.success('Template downloaded!');
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
                    <h1 className="text-2xl font-bold">Import from CSV</h1>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                    {/* Upload Section */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <FileSpreadsheet className="w-5 h-5" /> Upload CSV
                            </CardTitle>
                            <CardDescription>
                                Upload a CSV file with recipe data
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                                <input
                                    type="file"
                                    accept=".csv"
                                    onChange={handleFileChange}
                                    className="hidden"
                                    id="csv-upload"
                                />
                                <label htmlFor="csv-upload" className="cursor-pointer">
                                    <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                                    <p className="text-gray-600 mb-2">
                                        {file ? file.name : 'Click to select CSV file'}
                                    </p>
                                    <p className="text-sm text-gray-400">
                                        {file ? `${(file.size / 1024).toFixed(1)} KB` : 'or drag and drop'}
                                    </p>
                                </label>
                            </div>

                            <Button
                                onClick={handleUpload}
                                disabled={!file || loading}
                                className="w-full bg-amber-700 hover:bg-amber-800"
                            >
                                {loading ? 'Importing...' : 'Import Recipes'}
                            </Button>

                            {result && (
                                <Alert variant={result.imported > 0 ? 'default' : 'destructive'}>
                                    <AlertDescription>
                                        <div className="space-y-2">
                                            <div className="flex items-center gap-2">
                                                <CheckCircle className="w-4 h-4 text-green-600" />
                                                <span>Imported: {result.imported}</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <XCircle className="w-4 h-4 text-gray-400" />
                                                <span>Skipped: {result.skipped}</span>
                                            </div>
                                            {result.errors?.length > 0 && (
                                                <div className="mt-2 text-sm text-red-600">
                                                    <strong>Errors:</strong>
                                                    <ul className="list-disc list-inside">
                                                        {result.errors.map((err, i) => (
                                                            <li key={i}>{err}</li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}
                                        </div>
                                    </AlertDescription>
                                </Alert>
                            )}
                        </CardContent>
                    </Card>

                    {/* Template Section */}
                    <Card>
                        <CardHeader>
                            <CardTitle>CSV Template</CardTitle>
                            <CardDescription>
                                Download the template to get started
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <Button onClick={downloadTemplate} variant="outline" className="w-full">
                                <Download className="w-4 h-4 mr-2" /> Download Template
                            </Button>

                            <div className="bg-gray-100 rounded-lg p-4">
                                <h4 className="font-medium mb-2">Format Notes:</h4>
                                <ul className="text-sm text-gray-600 space-y-1">
                                    <li>• <strong>no_no_rules</strong>: Semicolon-separated</li>
                                    <li>• <strong>special_techniques</strong>: Semicolon-separated</li>
                                    <li>• <strong>ingredients</strong>: item:amount:unit:notes;...</li>
                                    <li>• <strong>instructions</strong>: Semicolon-separated steps</li>
                                    <li>• <strong>authenticity_level</strong>: 1 (highest) to 5</li>
                                </ul>
                            </div>

                            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                                <h4 className="font-medium text-amber-800 mb-2">Tips:</h4>
                                <ul className="text-sm text-amber-700 space-y-1">
                                    <li>• Duplicate slugs will be skipped</li>
                                    <li>• recipe_name is required</li>
                                    <li>• Use UTF-8 encoding for special characters</li>
                                </ul>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default AdminImportCSVPage;
