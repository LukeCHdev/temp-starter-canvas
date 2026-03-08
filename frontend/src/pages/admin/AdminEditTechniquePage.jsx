import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Save, Eye, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import axios from 'axios';
import { ImageManager } from '@/components/admin/ImageManager';

const API_URL = process.env.REACT_APP_BACKEND_URL || import.meta?.env?.VITE_BACKEND_URL || '';

export const AdminEditTechniquePage = () => {
    const { slug } = useParams();
    const navigate = useNavigate();
    const [jsonInput, setJsonInput] = useState('');
    const [originalTechnique, setOriginalTechnique] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [currentImageUrl, setCurrentImageUrl] = useState(null);

    const getAuthHeaders = () => {
        const token = localStorage.getItem('admin_token');
        return { Authorization: `Bearer ${token}` };
    };

    const fetchTechnique = async () => {
        try {
            const response = await axios.get(
                `${API_URL}/api/admin/techniques/${slug}`,
                { headers: getAuthHeaders() }
            );
            setOriginalTechnique(response.data.technique);
            setJsonInput(JSON.stringify(response.data.technique, null, 2));
            setCurrentImageUrl(response.data.technique?.image_url || null);
            setError(null);
        } catch (error) {
            if (error.response?.status === 401) {
                toast.error('Session expired. Please login again.');
                navigate('/admin/login');
            } else if (error.response?.status === 404) {
                setError('Technique not found');
            } else {
                setError('Failed to fetch technique');
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTechnique();
    }, [slug]);

    const handleSave = async () => {
        try {
            const parsed = JSON.parse(jsonInput);
            
            setSaving(true);
            const response = await axios.put(
                `${API_URL}/api/admin/techniques/${slug}`,
                { technique_data: parsed },
                { headers: getAuthHeaders() }
            );

            if (response.data.success) {
                toast.success('Technique updated successfully!');
                
                if (response.data.slug !== slug) {
                    navigate(`/admin/techniques/${response.data.slug}/edit`);
                } else {
                    fetchTechnique();
                }
            }
        } catch (error) {
            if (error instanceof SyntaxError) {
                toast.error('Invalid JSON format');
            } else if (error.response?.status === 401) {
                toast.error('Session expired. Please login again.');
                navigate('/admin/login');
            } else {
                toast.error(error.response?.data?.detail || 'Failed to save technique');
            }
        } finally {
            setSaving(false);
        }
    };

    const handleReset = () => {
        if (window.confirm('Reset to original? All changes will be lost.')) {
            setJsonInput(JSON.stringify(originalTechnique, null, 2));
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

    const handleImageChange = (newImageUrl) => {
        setCurrentImageUrl(newImageUrl);
        try {
            const parsed = JSON.parse(jsonInput);
            parsed.image_url = newImageUrl;
            parsed.image_source = 'upload';
            setJsonInput(JSON.stringify(parsed, null, 2));
            toast.success('Image updated');
        } catch (e) {
            // JSON might be invalid
        }
    };

    const handleImageRemove = () => {
        setCurrentImageUrl(null);
        try {
            const parsed = JSON.parse(jsonInput);
            delete parsed.image_url;
            delete parsed.image_source;
            setJsonInput(JSON.stringify(parsed, null, 2));
        } catch (e) {
            // JSON might be invalid
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
                    <Link to="/admin/techniques" className="mt-4 inline-block">
                        <Button variant="outline">Back to Techniques</Button>
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-4">
                        <Link to="/admin/techniques">
                            <Button variant="outline" size="sm">
                                <ArrowLeft className="w-4 h-4 mr-2" /> Back
                            </Button>
                        </Link>
                        <div>
                            <h1 className="text-2xl font-bold">Edit Technique</h1>
                            <p className="text-sm text-gray-500">Slug: {slug}</p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Link to={`/techniques/${slug}`} target="_blank">
                            <Button variant="outline" size="sm">
                                <Eye className="w-4 h-4 mr-2" /> Preview
                            </Button>
                        </Link>
                    </div>
                </div>

                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Image Manager */}
                    <div className="lg:col-span-1">
                        <ImageManager
                            currentImageUrl={currentImageUrl}
                            onImageChange={handleImageChange}
                            onImageRemove={handleImageRemove}
                            entityType="technique"
                            entitySlug={slug}
                            authHeaders={getAuthHeaders()}
                        />
                    </div>

                    {/* JSON Editor */}
                    <div className="lg:col-span-2">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center justify-between">
                                    <span>{originalTechnique?.title || 'Technique'}</span>
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
            </div>
        </div>
    );
};

export default AdminEditTechniquePage;
