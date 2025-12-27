import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Plus, Edit, Trash2, Search, Globe, ChefHat, FileJson, FileSpreadsheet, Link as LinkIcon, LogOut, BarChart3, ClipboardList } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import axios from 'axios';
import { Helmet } from 'react-helmet-async';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const AdminRecipesPage = () => {
    const [recipes, setRecipes] = useState([]);
    const [filteredRecipes, setFilteredRecipes] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState(null);
    const [statusFilter, setStatusFilter] = useState('all');
    const [counts, setCounts] = useState({ all: 0, published: 0, unpublished: 0, draft: 0 });
    const navigate = useNavigate();

    const getAuthHeaders = () => {
        const token = localStorage.getItem('admin_token');
        return { Authorization: `Bearer ${token}` };
    };

    const fetchRecipes = async (filter = 'all') => {
        try {
            const url = filter === 'all' 
                ? `${API_URL}/api/admin/recipes`
                : `${API_URL}/api/admin/recipes?status_filter=${filter}`;
            const response = await axios.get(url, { headers: getAuthHeaders() });
            setRecipes(response.data.recipes);
            setFilteredRecipes(response.data.recipes);
            setCounts(response.data.counts || { all: 0, published: 0, unpublished: 0, draft: 0 });
        } catch (error) {
            if (error.response?.status === 401) {
                toast.error('Session expired. Please login again.');
                navigate('/admin/login');
            } else {
                toast.error('Failed to fetch recipes');
            }
        } finally {
            setLoading(false);
        }
    };

    const fetchStats = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/admin/stats`, { headers: getAuthHeaders() });
            setStats(response.data);
        } catch (error) {
            console.error('Failed to fetch stats:', error);
        }
    };

    useEffect(() => {
        fetchRecipes(statusFilter);
        fetchStats();
    }, [statusFilter]);

    useEffect(() => {
        if (searchQuery) {
            const filtered = recipes.filter(r =>
                r.recipe_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                r.origin_country?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                r.slug?.toLowerCase().includes(searchQuery.toLowerCase())
            );
            setFilteredRecipes(filtered);
        } else {
            setFilteredRecipes(recipes);
        }
    }, [searchQuery, recipes]);

    const handleDelete = async (slug) => {
        if (!window.confirm(`Are you sure you want to delete "${slug}"?`)) return;

        try {
            await axios.delete(`${API_URL}/api/admin/recipes/${slug}`, { headers: getAuthHeaders() });
            toast.success('Recipe deleted successfully');
            fetchRecipes();
        } catch (error) {
            toast.error('Failed to delete recipe');
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('admin_token');
        navigate('/admin/login');
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-700"></div>
            </div>
        );
    }

    return (
        <>
        <Helmet>
            <meta name="robots" content="noindex, nofollow" />
            <title>Recipe Management - Admin | Sous Chef Linguine</title>
        </Helmet>
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <ChefHat className="w-8 h-8 text-amber-700" />
                        <h1 className="text-xl font-bold text-gray-800">Admin Panel</h1>
                    </div>
                    <div className="flex items-center gap-3">
                        <Link to="/admin/review">
                            <Button variant="outline" size="sm" className="border-orange-300 text-orange-700 hover:bg-orange-50">
                                <ClipboardList className="w-4 h-4 mr-2" /> Review Queue
                            </Button>
                        </Link>
                        <Link to="/">
                            <Button variant="outline" size="sm">
                                <Globe className="w-4 h-4 mr-2" /> View Site
                            </Button>
                        </Link>
                        <Button variant="outline" size="sm" onClick={handleLogout}>
                            <LogOut className="w-4 h-4 mr-2" /> Logout
                        </Button>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-4 py-6">
                {/* Stats Cards */}
                {stats && (
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                        <Card className={`cursor-pointer transition-all ${statusFilter === 'all' ? 'ring-2 ring-amber-500' : ''}`} onClick={() => setStatusFilter('all')}>
                            <CardContent className="p-4">
                                <div className="text-2xl font-bold text-amber-700">{counts.all}</div>
                                <div className="text-sm text-gray-500">Total Recipes</div>
                            </CardContent>
                        </Card>
                        <Card className={`cursor-pointer transition-all ${statusFilter === 'published' ? 'ring-2 ring-green-500' : ''}`} onClick={() => setStatusFilter('published')}>
                            <CardContent className="p-4">
                                <div className="text-2xl font-bold text-green-600">{counts.published}</div>
                                <div className="text-sm text-gray-500">✅ Published</div>
                                <div className="text-xs text-gray-400">Public site shows</div>
                            </CardContent>
                        </Card>
                        <Card className={`cursor-pointer transition-all ${statusFilter === 'unpublished' ? 'ring-2 ring-red-500' : ''}`} onClick={() => setStatusFilter('unpublished')}>
                            <CardContent className="p-4">
                                <div className="text-2xl font-bold text-red-600">{counts.unpublished}</div>
                                <div className="text-sm text-gray-500">❌ Unpublished</div>
                            </CardContent>
                        </Card>
                        <Card className={`cursor-pointer transition-all ${statusFilter === 'draft' ? 'ring-2 ring-yellow-500' : ''}`} onClick={() => setStatusFilter('draft')}>
                            <CardContent className="p-4">
                                <div className="text-2xl font-bold text-yellow-600">{counts.draft}</div>
                                <div className="text-sm text-gray-500">📝 Draft</div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <div className="text-2xl font-bold text-blue-600">{stats.recipes_by_country?.length || 0}</div>
                                <div className="text-sm text-gray-500">🌍 Countries</div>
                            </CardContent>
                        </Card>
                    </div>
                )}
                
                {/* Database Info Banner */}
                {stats?.db_info && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-6 text-sm">
                        <span className="font-medium">📊 Database:</span> {stats.db_info.database} | 
                        <span className="font-medium ml-2">Collection:</span> recipes | 
                        <span className="text-blue-600 ml-2">{stats.filter_explanation}</span>
                    </div>
                )}
                
                {/* Current Filter Indicator */}
                <div className="mb-4 flex items-center gap-2">
                    <span className="text-sm text-gray-500">Showing:</span>
                    <Badge variant={statusFilter === 'all' ? 'default' : 'outline'}>
                        {statusFilter === 'all' ? 'All Recipes' : statusFilter.charAt(0).toUpperCase() + statusFilter.slice(1)}
                    </Badge>
                    <span className="text-sm text-gray-500">({filteredRecipes.length} recipes)</span>
                    {statusFilter !== 'all' && (
                        <Button variant="ghost" size="sm" onClick={() => setStatusFilter('all')}>
                            Clear filter
                        </Button>
                    )}
                </div>

                {/* Action Buttons */}
                <div className="flex flex-wrap gap-3 mb-6">
                    <Link to="/admin/recipes/new">
                        <Button className="bg-amber-700 hover:bg-amber-800">
                            <Plus className="w-4 h-4 mr-2" /> New Recipe
                        </Button>
                    </Link>
                    <Link to="/admin/import-json">
                        <Button variant="outline">
                            <FileJson className="w-4 h-4 mr-2" /> Import JSON
                        </Button>
                    </Link>
                    <Link to="/admin/import-csv">
                        <Button variant="outline">
                            <FileSpreadsheet className="w-4 h-4 mr-2" /> Import CSV
                        </Button>
                    </Link>
                    <Link to="/admin/import-document">
                        <Button variant="outline">
                            <FileSpreadsheet className="w-4 h-4 mr-2" /> Import PDF/ODF
                        </Button>
                    </Link>
                    <Link to="/admin/import-scrape">
                        <Button variant="outline">
                            <LinkIcon className="w-4 h-4 mr-2" /> Scrape URL
                        </Button>
                    </Link>
                </div>

                {/* Search */}
                <div className="relative mb-6">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <Input
                        placeholder="Search recipes by name, country, or slug..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                    />
                </div>

                {/* Recipes Table */}
                <Card>
                    <CardHeader>
                        <CardTitle>Recipes ({filteredRecipes.length})</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b">
                                        <th className="text-left py-3 px-2">Recipe Name</th>
                                        <th className="text-left py-3 px-2">Country</th>
                                        <th className="text-left py-3 px-2">Continent</th>
                                        <th className="text-left py-3 px-2">Status</th>
                                        <th className="text-left py-3 px-2">Rating</th>
                                        <th className="text-right py-3 px-2">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredRecipes.map((recipe) => (
                                        <tr key={recipe.slug} className="border-b hover:bg-gray-50">
                                            <td className="py-3 px-2">
                                                <div className="font-medium">{recipe.recipe_name || 'Untitled'}</div>
                                                <div className="text-xs text-gray-500">{recipe.slug}</div>
                                            </td>
                                            <td className="py-3 px-2">{recipe.origin_country || '-'}</td>
                                            <td className="py-3 px-2">{recipe.continent || '-'}</td>
                                            <td className="py-3 px-2">
                                                <Badge variant={recipe.status === 'published' ? 'default' : 'secondary'}>
                                                    {recipe.status || 'draft'}
                                                </Badge>
                                            </td>
                                            <td className="py-3 px-2">
                                                {recipe.average_rating > 0 ? `⭐ ${recipe.average_rating}` : '-'}
                                            </td>
                                            <td className="py-3 px-2 text-right">
                                                <div className="flex justify-end gap-2">
                                                    <Link to={`/admin/recipes/${recipe.slug}/edit`}>
                                                        <Button size="sm" variant="outline">
                                                            <Edit className="w-4 h-4" />
                                                        </Button>
                                                    </Link>
                                                    <Button
                                                        size="sm"
                                                        variant="outline"
                                                        className="text-red-600 hover:text-red-700"
                                                        onClick={() => handleDelete(recipe.slug)}
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </Button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {filteredRecipes.length === 0 && (
                                <div className="text-center py-8 text-gray-500">
                                    No recipes found. Start by adding a new recipe!
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default AdminRecipesPage;
