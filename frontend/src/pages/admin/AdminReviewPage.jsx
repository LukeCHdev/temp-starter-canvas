import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
    ChefHat, ArrowLeft, Play, Eye, Archive, Check, X, 
    AlertTriangle, Copy, Filter, RefreshCw 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import axios from 'axios';
import { Helmet } from 'react-helmet-async';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Flag colors
const FLAG_COLORS = {
    'MISSING_FIELDS': 'bg-red-100 text-red-700 border-red-300',
    'PLACEHOLDER': 'bg-yellow-100 text-yellow-700 border-yellow-300',
    'POSSIBLE_DUPLICATE': 'bg-orange-100 text-orange-700 border-orange-300',
    'VERY_SHORT': 'bg-blue-100 text-blue-700 border-blue-300',
    'LANGUAGE_MISMATCH': 'bg-purple-100 text-purple-700 border-purple-300'
};

export const AdminReviewPage = () => {
    const [queue, setQueue] = useState([]);
    const [counts, setCounts] = useState({ safe: 0, blocked: 0, duplicates: 0, placeholders: 0 });
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');
    const [dryRunResult, setDryRunResult] = useState(null);
    const [publishing, setPublishing] = useState(false);
    const navigate = useNavigate();

    const getAuthHeaders = () => {
        const token = localStorage.getItem('admin_token');
        if (!token) {
            navigate('/admin/login');
            return {};
        }
        return { Authorization: `Bearer ${token}` };
    };

    const fetchQueue = async () => {
        setLoading(true);
        try {
            const response = await axios.get(`${API_URL}/api/admin/review-queue`, { 
                headers: getAuthHeaders() 
            });
            setQueue(response.data.queue);
            setCounts(response.data.counts);
        } catch (error) {
            if (error.response?.status === 401) {
                toast.error('Session expired. Please login again.');
                navigate('/admin/login');
            } else {
                toast.error('Failed to fetch review queue');
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchQueue();
    }, []);

    const handleDryRun = async () => {
        try {
            const response = await axios.post(
                `${API_URL}/api/admin/recipes/bulk-publish?safe=1&dry_run=1`,
                {},
                { headers: getAuthHeaders() }
            );
            setDryRunResult(response.data);
            toast.success(`Dry run complete: ${response.data.would_publish_count} would be published`);
        } catch (error) {
            toast.error('Dry run failed');
        }
    };

    const handleBulkPublish = async () => {
        if (!window.confirm(`Are you sure you want to publish all SAFE recipes? This cannot be undone.`)) {
            return;
        }
        
        setPublishing(true);
        try {
            const response = await axios.post(
                `${API_URL}/api/admin/recipes/bulk-publish?safe=1&dry_run=0`,
                {},
                { headers: getAuthHeaders() }
            );
            toast.success(`Published ${response.data.published_count} recipes!`);
            setDryRunResult(null);
            fetchQueue(); // Refresh the queue
        } catch (error) {
            toast.error('Bulk publish failed');
        } finally {
            setPublishing(false);
        }
    };

    const handleSingleAction = async (slug, action) => {
        try {
            let updateData = {};
            
            if (action === 'publish') {
                updateData = { status: 'published' };
            } else if (action === 'archive') {
                updateData = { status: 'archived', archived: true };
            } else if (action === 'unpublish') {
                updateData = { status: 'unpublished' };
            }
            
            await axios.patch(
                `${API_URL}/api/admin/recipes/${slug}`,
                updateData,
                { headers: getAuthHeaders() }
            );
            
            toast.success(`Recipe ${action}ed: ${slug}`);
            fetchQueue();
        } catch (error) {
            toast.error(`Failed to ${action} recipe`);
        }
    };

    // Filter queue based on selected filter
    const filteredQueue = queue.filter(item => {
        if (filter === 'all') return true;
        if (filter === 'safe') return item.is_safe_to_publish;
        if (filter === 'blocked') return !item.is_safe_to_publish;
        if (filter === 'duplicates') return item.flags.some(f => f.startsWith('POSSIBLE_DUPLICATE'));
        if (filter === 'placeholders') return item.flags.includes('PLACEHOLDER');
        if (filter === 'needs_review') return item.flags.length > 0 && item.is_safe_to_publish;
        return true;
    });

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
                <title>Review Queue - Admin | Sous Chef Linguine</title>
            </Helmet>
            
            <div className="min-h-screen bg-gray-50">
                {/* Header */}
                <header className="bg-white shadow-sm border-b">
                    <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Link to="/admin/recipes">
                                <Button variant="ghost" size="sm">
                                    <ArrowLeft className="w-4 h-4 mr-2" /> Back
                                </Button>
                            </Link>
                            <ChefHat className="w-8 h-8 text-amber-700" />
                            <h1 className="text-xl font-bold text-gray-800">Review Queue</h1>
                        </div>
                        <Button variant="outline" size="sm" onClick={fetchQueue}>
                            <RefreshCw className="w-4 h-4 mr-2" /> Refresh
                        </Button>
                    </div>
                </header>

                <div className="max-w-7xl mx-auto px-4 py-6">
                    {/* Stats Cards */}
                    <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
                        <Card 
                            className={`cursor-pointer transition-all ${filter === 'all' ? 'ring-2 ring-amber-500' : ''}`}
                            onClick={() => setFilter('all')}
                        >
                            <CardContent className="p-4">
                                <div className="text-2xl font-bold text-gray-700">{queue.length}</div>
                                <div className="text-sm text-gray-500">Total in Queue</div>
                            </CardContent>
                        </Card>
                        <Card 
                            className={`cursor-pointer transition-all ${filter === 'safe' ? 'ring-2 ring-green-500' : ''}`}
                            onClick={() => setFilter('safe')}
                        >
                            <CardContent className="p-4">
                                <div className="text-2xl font-bold text-green-600">{counts.safe}</div>
                                <div className="text-sm text-gray-500">✅ Safe to Publish</div>
                            </CardContent>
                        </Card>
                        <Card 
                            className={`cursor-pointer transition-all ${filter === 'hidden_published' ? 'ring-2 ring-purple-500' : ''}`}
                            onClick={() => setFilter('hidden_published')}
                        >
                            <CardContent className="p-4">
                                <div className="text-2xl font-bold text-purple-600">{counts.hidden_published || 0}</div>
                                <div className="text-sm text-gray-500">👻 Published Hidden</div>
                            </CardContent>
                        </Card>
                        <Card 
                            className={`cursor-pointer transition-all ${filter === 'blocked' ? 'ring-2 ring-red-500' : ''}`}
                            onClick={() => setFilter('blocked')}
                        >
                            <CardContent className="p-4">
                                <div className="text-2xl font-bold text-red-600">{counts.blocked}</div>
                                <div className="text-sm text-gray-500">❌ Blocked</div>
                            </CardContent>
                        </Card>
                        <Card 
                            className={`cursor-pointer transition-all ${filter === 'duplicates' ? 'ring-2 ring-orange-500' : ''}`}
                            onClick={() => setFilter('duplicates')}
                        >
                            <CardContent className="p-4">
                                <div className="text-2xl font-bold text-orange-600">{counts.duplicates}</div>
                                <div className="text-sm text-gray-500">🔄 Duplicates</div>
                            </CardContent>
                        </Card>
                        <Card 
                            className={`cursor-pointer transition-all ${filter === 'placeholders' ? 'ring-2 ring-yellow-500' : ''}`}
                            onClick={() => setFilter('placeholders')}
                        >
                            <CardContent className="p-4">
                                <div className="text-2xl font-bold text-yellow-600">{counts.placeholders}</div>
                                <div className="text-sm text-gray-500">🚫 Placeholders</div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex flex-wrap gap-3 mb-6">
                        <Button 
                            variant="outline" 
                            onClick={handleDryRun}
                            className="border-blue-300 text-blue-700 hover:bg-blue-50"
                        >
                            <Eye className="w-4 h-4 mr-2" /> Dry Run (Preview)
                        </Button>
                        <Button 
                            className="bg-green-600 hover:bg-green-700"
                            onClick={handleBulkPublish}
                            disabled={publishing || counts.safe === 0}
                        >
                            <Play className="w-4 h-4 mr-2" /> 
                            {publishing ? 'Publishing...' : `Publish All SAFE (${counts.safe})`}
                        </Button>
                    </div>

                    {/* Dry Run Results */}
                    {dryRunResult && (
                        <Card className="mb-6 bg-blue-50 border-blue-200">
                            <CardHeader>
                                <CardTitle className="text-blue-800 flex items-center gap-2">
                                    <Eye className="w-5 h-5" /> Dry Run Results
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-2 gap-4 mb-4">
                                    <div>
                                        <span className="text-green-700 font-bold text-xl">
                                            {dryRunResult.would_publish_count}
                                        </span>
                                        <span className="text-gray-600 ml-2">would be published</span>
                                    </div>
                                    <div>
                                        <span className="text-red-700 font-bold text-xl">
                                            {dryRunResult.blocked_count}
                                        </span>
                                        <span className="text-gray-600 ml-2">blocked</span>
                                    </div>
                                </div>
                                {dryRunResult.sample_slugs?.length > 0 && (
                                    <div>
                                        <div className="text-sm font-medium text-gray-600 mb-2">Sample slugs to publish:</div>
                                        <div className="flex flex-wrap gap-1">
                                            {dryRunResult.sample_slugs.slice(0, 10).map(slug => (
                                                <Badge key={slug} variant="outline" className="text-xs">
                                                    {slug}
                                                </Badge>
                                            ))}
                                            {dryRunResult.sample_slugs.length > 10 && (
                                                <Badge variant="outline" className="text-xs">
                                                    +{dryRunResult.sample_slugs.length - 10} more
                                                </Badge>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    )}

                    {/* Current Filter Indicator */}
                    <div className="mb-4 flex items-center gap-2">
                        <Filter className="w-4 h-4 text-gray-500" />
                        <span className="text-sm text-gray-500">Showing:</span>
                        <Badge variant={filter === 'all' ? 'default' : 'outline'}>
                            {filter === 'all' ? 'All' : filter.charAt(0).toUpperCase() + filter.slice(1)}
                        </Badge>
                        <span className="text-sm text-gray-500">({filteredQueue.length} recipes)</span>
                        {filter !== 'all' && (
                            <Button variant="ghost" size="sm" onClick={() => setFilter('all')}>
                                Clear filter
                            </Button>
                        )}
                    </div>

                    {/* Queue Table */}
                    <Card>
                        <CardContent className="p-0">
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead className="bg-gray-50 border-b">
                                        <tr>
                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recipe</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Country</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Flags</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y">
                                        {filteredQueue.map((item) => (
                                            <tr key={item.slug} className={`hover:bg-gray-50 ${!item.is_safe_to_publish ? 'bg-red-50/30' : ''}`}>
                                                <td className="px-4 py-3">
                                                    {item.is_safe_to_publish ? (
                                                        <Badge className="bg-green-100 text-green-700 border-green-300">
                                                            ✅ SAFE
                                                        </Badge>
                                                    ) : (
                                                        <Badge className="bg-red-100 text-red-700 border-red-300">
                                                            ❌ BLOCKED
                                                        </Badge>
                                                    )}
                                                </td>
                                                <td className="px-4 py-3">
                                                    <div className="font-medium text-gray-900">{item.recipe_name || '(no name)'}</div>
                                                    <div className="text-xs text-gray-500 font-mono">{item.slug}</div>
                                                    {item.duplicate_of && (
                                                        <div className="text-xs text-orange-600">
                                                            ↳ Duplicate of: {item.duplicate_of}
                                                        </div>
                                                    )}
                                                </td>
                                                <td className="px-4 py-3 text-sm text-gray-600">
                                                    {item.origin_country || '-'}
                                                </td>
                                                <td className="px-4 py-3">
                                                    <Badge variant="outline" className="text-xs">
                                                        {item.source || 'unknown'}
                                                    </Badge>
                                                </td>
                                                <td className="px-4 py-3">
                                                    <div className="flex flex-wrap gap-1">
                                                        {item.flags.length === 0 ? (
                                                            <span className="text-xs text-gray-400">No issues</span>
                                                        ) : (
                                                            item.flags.map((flag, idx) => {
                                                                const flagType = flag.split(':')[0];
                                                                return (
                                                                    <Badge 
                                                                        key={idx} 
                                                                        variant="outline"
                                                                        className={`text-xs ${FLAG_COLORS[flagType] || 'bg-gray-100 text-gray-700'}`}
                                                                    >
                                                                        {flag}
                                                                    </Badge>
                                                                );
                                                            })
                                                        )}
                                                    </div>
                                                </td>
                                                <td className="px-4 py-3">
                                                    <div className="flex gap-1">
                                                        <Button 
                                                            size="sm" 
                                                            variant="outline"
                                                            className="h-7 px-2 text-green-600 hover:bg-green-50"
                                                            onClick={() => handleSingleAction(item.slug, 'publish')}
                                                            title="Publish"
                                                        >
                                                            <Check className="w-3 h-3" />
                                                        </Button>
                                                        <Button 
                                                            size="sm" 
                                                            variant="outline"
                                                            className="h-7 px-2 text-gray-600 hover:bg-gray-50"
                                                            onClick={() => handleSingleAction(item.slug, 'archive')}
                                                            title="Archive"
                                                        >
                                                            <Archive className="w-3 h-3" />
                                                        </Button>
                                                        <Link to={`/admin/recipes/${item.slug}/edit`}>
                                                            <Button 
                                                                size="sm" 
                                                                variant="outline"
                                                                className="h-7 px-2"
                                                                title="Edit"
                                                            >
                                                                Edit
                                                            </Button>
                                                        </Link>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            
                            {filteredQueue.length === 0 && (
                                <div className="text-center py-12 text-gray-500">
                                    {filter === 'all' 
                                        ? 'No recipes in review queue. All recipes are published!' 
                                        : `No recipes match the "${filter}" filter.`}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </>
    );
};

export default AdminReviewPage;
