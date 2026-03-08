import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Edit, Trash2, Eye, Search, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || import.meta?.env?.VITE_BACKEND_URL || '';

export const AdminTechniquesPage = () => {
    const navigate = useNavigate();
    const [techniques, setTechniques] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    const getAuthHeaders = () => {
        const token = localStorage.getItem('admin_token');
        return { Authorization: `Bearer ${token}` };
    };

    const fetchTechniques = async () => {
        try {
            const response = await axios.get(
                `${API_URL}/api/admin/techniques`,
                { headers: getAuthHeaders() }
            );
            setTechniques(response.data.techniques || []);
        } catch (error) {
            if (error.response?.status === 401) {
                toast.error('Session expired. Please login again.');
                navigate('/admin/login');
            } else {
                toast.error('Failed to fetch techniques');
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTechniques();
    }, []);

    const handleDelete = async (slug, title) => {
        if (!window.confirm(`Are you sure you want to delete "${title}"?`)) {
            return;
        }

        try {
            await axios.delete(
                `${API_URL}/api/admin/techniques/${slug}`,
                { headers: getAuthHeaders() }
            );
            toast.success('Technique deleted');
            fetchTechniques();
        } catch (error) {
            toast.error('Failed to delete technique');
        }
    };

    const filteredTechniques = techniques.filter(t =>
        t.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.category?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const getDifficultyColor = (difficulty) => {
        switch (difficulty?.toLowerCase()) {
            case 'beginner': return 'bg-green-100 text-green-800';
            case 'intermediate': return 'bg-yellow-100 text-yellow-800';
            case 'advanced': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'published': return 'bg-green-100 text-green-800';
            case 'draft': return 'bg-yellow-100 text-yellow-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-amber-700" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-2xl font-bold">Techniques</h1>
                        <p className="text-gray-500">
                            {techniques.length} technique{techniques.length !== 1 ? 's' : ''} total
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Link to="/admin/recipes">
                            <Button variant="outline">Recipes</Button>
                        </Link>
                        <Link to="/admin/techniques/new">
                            <Button className="bg-amber-700 hover:bg-amber-800">
                                <Plus className="w-4 h-4 mr-2" /> New Technique
                            </Button>
                        </Link>
                    </div>
                </div>

                {/* Search */}
                <div className="mb-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                        <Input
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search techniques..."
                            className="pl-10"
                        />
                    </div>
                </div>

                {/* Techniques List */}
                {filteredTechniques.length === 0 ? (
                    <Card>
                        <CardContent className="py-12 text-center">
                            <p className="text-gray-500">
                                {searchQuery ? 'No techniques found matching your search' : 'No techniques yet. Create your first one!'}
                            </p>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="grid gap-4">
                        {filteredTechniques.map((technique) => (
                            <Card key={technique.slug} className="hover:shadow-md transition-shadow">
                                <CardContent className="p-4">
                                    <div className="flex items-start gap-4">
                                        {/* Image thumbnail */}
                                        <div className="w-20 h-20 bg-gray-200 rounded-lg overflow-hidden flex-shrink-0">
                                            {technique.image_url ? (
                                                <img
                                                    src={technique.image_url.startsWith('/') ? `${API_URL}${technique.image_url}` : technique.image_url}
                                                    alt={technique.title}
                                                    className="w-full h-full object-cover"
                                                />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center text-gray-400">
                                                    No img
                                                </div>
                                            )}
                                        </div>

                                        {/* Content */}
                                        <div className="flex-1">
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <h3 className="font-semibold text-lg">{technique.title}</h3>
                                                    <div className="flex gap-2 mt-1">
                                                        <Badge className={getStatusColor(technique.status)}>
                                                            {technique.status || 'draft'}
                                                        </Badge>
                                                        {technique.category && (
                                                            <Badge variant="outline">{technique.category}</Badge>
                                                        )}
                                                        {technique.difficulty && (
                                                            <Badge className={getDifficultyColor(technique.difficulty)}>
                                                                {technique.difficulty}
                                                            </Badge>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="flex gap-2">
                                                    <Link to={`/techniques/${technique.slug}`} target="_blank">
                                                        <Button variant="ghost" size="sm">
                                                            <Eye className="w-4 h-4" />
                                                        </Button>
                                                    </Link>
                                                    <Link to={`/admin/techniques/${technique.slug}/edit`}>
                                                        <Button variant="ghost" size="sm">
                                                            <Edit className="w-4 h-4" />
                                                        </Button>
                                                    </Link>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="text-red-600 hover:text-red-700"
                                                        onClick={() => handleDelete(technique.slug, technique.title)}
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </Button>
                                                </div>
                                            </div>
                                            {technique.introduction && (
                                                <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                                                    {technique.introduction}
                                                </p>
                                            )}
                                            <p className="text-xs text-gray-400 mt-2">
                                                Slug: {technique.slug}
                                                {technique.readTime && ` • ${technique.readTime}`}
                                            </p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default AdminTechniquesPage;
