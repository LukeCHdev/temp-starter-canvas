import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Save, Plus, Trash2 } from 'lucide-react';
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

// Template for new technique
const TECHNIQUE_TEMPLATE = {
    title: "",
    slug: "",
    category: "",
    difficulty: "beginner",
    readTime: "5 min",
    introduction: "",
    sections: [],
    status: "draft"
};

export const AdminNewTechniquePage = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState(TECHNIQUE_TEMPLATE);
    const [sections, setSections] = useState([]);
    const [saving, setSaving] = useState(false);
    const [tempImageUrl, setTempImageUrl] = useState(null);

    const getAuthHeaders = () => {
        const token = localStorage.getItem('admin_token');
        return { Authorization: `Bearer ${token}` };
    };

    const generateSlug = (title) => {
        return title
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-|-$/g, '');
    };

    const handleInputChange = (field, value) => {
        setFormData(prev => {
            const updated = { ...prev, [field]: value };
            if (field === 'title') {
                updated.slug = generateSlug(value);
            }
            return updated;
        });
    };

    const addSection = () => {
        setSections(prev => [...prev, { heading: '', content: '' }]);
    };

    const updateSection = (index, field, value) => {
        setSections(prev => {
            const updated = [...prev];
            updated[index] = { ...updated[index], [field]: value };
            return updated;
        });
    };

    const removeSection = (index) => {
        setSections(prev => prev.filter((_, i) => i !== index));
    };

    const handleImageChange = (newImageUrl) => {
        setTempImageUrl(newImageUrl);
    };

    const handleImageRemove = () => {
        setTempImageUrl(null);
    };

    const handleSave = async () => {
        if (!formData.title) {
            toast.error('Title is required');
            return;
        }

        try {
            const techniqueData = {
                ...formData,
                slug: formData.slug || generateSlug(formData.title),
                sections: sections.filter(s => s.heading || s.content),
                image_url: tempImageUrl,
                image_source: tempImageUrl ? 'upload' : undefined
            };

            setSaving(true);
            const response = await axios.post(
                `${API_URL}/api/admin/techniques`,
                techniqueData,
                { headers: getAuthHeaders() }
            );

            if (response.data.slug) {
                toast.success('Technique created successfully!');
                navigate(`/admin/techniques/${response.data.slug}/edit`);
            } else {
                toast.error('Failed to create technique');
            }
        } catch (error) {
            if (error.response?.status === 401) {
                toast.error('Session expired. Please login again.');
                navigate('/admin/login');
            } else if (error.response?.status === 409) {
                toast.error('A technique with this slug already exists');
            } else {
                toast.error(error.response?.data?.detail || 'Failed to create technique');
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
                        <Link to="/admin/techniques">
                            <Button variant="outline" size="sm">
                                <ArrowLeft className="w-4 h-4 mr-2" /> Back
                            </Button>
                        </Link>
                        <h1 className="text-2xl font-bold">New Technique</h1>
                    </div>
                </div>

                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Image Manager */}
                    <div className="lg:col-span-1">
                        <ImageManager
                            currentImageUrl={tempImageUrl}
                            onImageChange={handleImageChange}
                            onImageRemove={handleImageRemove}
                            entityType="technique"
                            entitySlug={null}
                            authHeaders={getAuthHeaders()}
                        />
                    </div>

                    {/* Form */}
                    <div className="lg:col-span-2 space-y-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>Basic Information</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <Label>Title *</Label>
                                        <Input
                                            value={formData.title}
                                            onChange={(e) => handleInputChange('title', e.target.value)}
                                            placeholder="e.g., Knife Skills Basics"
                                        />
                                    </div>
                                    <div>
                                        <Label>Category</Label>
                                        <Input
                                            value={formData.category}
                                            onChange={(e) => handleInputChange('category', e.target.value)}
                                            placeholder="e.g., Knife Skills, Baking, Sauces"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <Label>Difficulty</Label>
                                        <Select
                                            value={formData.difficulty}
                                            onValueChange={(value) => handleInputChange('difficulty', value)}
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="beginner">Beginner</SelectItem>
                                                <SelectItem value="intermediate">Intermediate</SelectItem>
                                                <SelectItem value="advanced">Advanced</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div>
                                        <Label>Read Time</Label>
                                        <Input
                                            value={formData.readTime}
                                            onChange={(e) => handleInputChange('readTime', e.target.value)}
                                            placeholder="e.g., 5 min"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
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
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div>
                                        <Label>Slug (auto-generated)</Label>
                                        <Input
                                            value={formData.slug}
                                            onChange={(e) => handleInputChange('slug', e.target.value)}
                                            placeholder="auto-generated"
                                            className="bg-gray-50"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <Label>Introduction</Label>
                                    <Textarea
                                        value={formData.introduction}
                                        onChange={(e) => handleInputChange('introduction', e.target.value)}
                                        placeholder="Brief introduction to this technique..."
                                        rows={4}
                                    />
                                </div>
                            </CardContent>
                        </Card>

                        {/* Sections */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center justify-between">
                                    <span>Sections</span>
                                    <Button onClick={addSection} variant="outline" size="sm">
                                        <Plus className="w-4 h-4 mr-2" /> Add Section
                                    </Button>
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {sections.length === 0 ? (
                                    <p className="text-gray-500 text-center py-4">
                                        No sections yet. Click "Add Section" to add content.
                                    </p>
                                ) : (
                                    sections.map((section, index) => (
                                        <div key={index} className="border rounded-lg p-4 space-y-3">
                                            <div className="flex items-center justify-between">
                                                <Label>Section {index + 1}</Label>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    className="text-red-600"
                                                    onClick={() => removeSection(index)}
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </Button>
                                            </div>
                                            <Input
                                                value={section.heading}
                                                onChange={(e) => updateSection(index, 'heading', e.target.value)}
                                                placeholder="Section heading..."
                                            />
                                            <Textarea
                                                value={section.content}
                                                onChange={(e) => updateSection(index, 'content', e.target.value)}
                                                placeholder="Section content..."
                                                rows={4}
                                            />
                                        </div>
                                    ))
                                )}
                            </CardContent>
                        </Card>

                        {/* Save Button */}
                        <div className="flex gap-2">
                            <Button
                                onClick={handleSave}
                                disabled={saving}
                                className="bg-amber-700 hover:bg-amber-800"
                            >
                                <Save className="w-4 h-4 mr-2" />
                                {saving ? 'Creating...' : 'Create Technique'}
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminNewTechniquePage;
