import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
    ArrowLeft, FileText, Link as LinkIcon, Upload, Loader2, 
    CheckCircle, XCircle, AlertTriangle, Edit, Save, SkipForward,
    Play, Pause, RefreshCw, Trash2, Eye, ChevronDown, ChevronUp
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Status badge component
const StatusBadge = ({ status }) => {
    const statusConfig = {
        pending: { color: 'bg-gray-100 text-gray-700', icon: null, label: 'Pending' },
        processing: { color: 'bg-blue-100 text-blue-700', icon: Loader2, label: 'Processing' },
        ready: { color: 'bg-green-100 text-green-700', icon: CheckCircle, label: 'Ready' },
        duplicate: { color: 'bg-yellow-100 text-yellow-700', icon: AlertTriangle, label: 'Duplicate' },
        saved: { color: 'bg-emerald-100 text-emerald-700', icon: CheckCircle, label: 'Saved' },
        skipped: { color: 'bg-gray-100 text-gray-500', icon: SkipForward, label: 'Skipped' },
        error: { color: 'bg-red-100 text-red-700', icon: XCircle, label: 'Error' },
    };
    
    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;
    
    return (
        <Badge className={`${config.color} flex items-center gap-1`}>
            {Icon && <Icon className={`w-3 h-3 ${status === 'processing' ? 'animate-spin' : ''}`} />}
            {config.label}
        </Badge>
    );
};

// Recipe card component
const RecipeCard = ({ recipe, onAction, onEdit, expanded, onToggle }) => {
    const [editMode, setEditMode] = useState(false);
    const [editedJson, setEditedJson] = useState('');
    
    const handleEdit = () => {
        setEditedJson(JSON.stringify(recipe.ai_result, null, 2));
        setEditMode(true);
    };
    
    const handleSaveEdit = () => {
        try {
            const parsed = JSON.parse(editedJson);
            onEdit(recipe.index, parsed);
            setEditMode(false);
            toast.success('Changes saved');
        } catch (e) {
            toast.error('Invalid JSON');
        }
    };
    
    return (
        <Card className={`mb-3 ${recipe.status === 'saved' ? 'border-green-300 bg-green-50/30' : ''}`}>
            <CardHeader className="py-3 cursor-pointer" onClick={onToggle}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <span className="text-sm text-gray-500">#{recipe.index + 1}</span>
                        <CardTitle className="text-base">{recipe.title}</CardTitle>
                        <StatusBadge status={recipe.status} />
                    </div>
                    <div className="flex items-center gap-2">
                        {recipe.status === 'saved' && recipe.saved_slug && (
                            <Link to={`/recipe/${recipe.saved_slug}`} target="_blank">
                                <Button size="sm" variant="outline">
                                    <Eye className="w-3 h-3 mr-1" /> View
                                </Button>
                            </Link>
                        )}
                        {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </div>
                </div>
            </CardHeader>
            
            {expanded && (
                <CardContent className="pt-0">
                    {/* Duplicate warning */}
                    {recipe.status === 'duplicate' && recipe.duplicate_match && (
                        <Alert className="mb-3 bg-yellow-50 border-yellow-200">
                            <AlertTriangle className="h-4 w-4 text-yellow-600" />
                            <AlertDescription className="text-yellow-800">
                                <strong>Possible duplicate:</strong> Similar to "{recipe.duplicate_match.name}" 
                                ({recipe.duplicate_match.country}) - Slug: {recipe.duplicate_match.slug}
                            </AlertDescription>
                        </Alert>
                    )}
                    
                    {/* Error message */}
                    {recipe.error_message && (
                        <Alert className="mb-3 bg-red-50 border-red-200">
                            <XCircle className="h-4 w-4 text-red-600" />
                            <AlertDescription className="text-red-800">
                                {recipe.error_message}
                            </AlertDescription>
                        </Alert>
                    )}
                    
                    {/* Raw text preview */}
                    {!editMode && (
                        <div className="mb-3">
                            <h4 className="text-sm font-medium text-gray-700 mb-1">Raw Text (from document)</h4>
                            <div className="bg-gray-50 rounded p-2 text-xs text-gray-600 max-h-32 overflow-y-auto">
                                {recipe.raw_text?.substring(0, 500)}...
                            </div>
                        </div>
                    )}
                    
                    {/* AI Result / Edit mode */}
                    {recipe.ai_result && (
                        <div className="mb-3">
                            <div className="flex items-center justify-between mb-1">
                                <h4 className="text-sm font-medium text-gray-700">
                                    {editMode ? 'Edit Recipe JSON' : 'AI Generated Recipe'}
                                </h4>
                                {!editMode && recipe.status !== 'saved' && recipe.status !== 'skipped' && (
                                    <Button size="sm" variant="outline" onClick={handleEdit}>
                                        <Edit className="w-3 h-3 mr-1" /> Edit
                                    </Button>
                                )}
                            </div>
                            
                            {editMode ? (
                                <div>
                                    <Textarea
                                        value={editedJson}
                                        onChange={(e) => setEditedJson(e.target.value)}
                                        className="font-mono text-xs min-h-[300px]"
                                    />
                                    <div className="flex gap-2 mt-2">
                                        <Button size="sm" onClick={handleSaveEdit}>
                                            <Save className="w-3 h-3 mr-1" /> Save Changes
                                        </Button>
                                        <Button size="sm" variant="outline" onClick={() => setEditMode(false)}>
                                            Cancel
                                        </Button>
                                    </div>
                                </div>
                            ) : (
                                <div className="bg-gray-50 rounded p-2 text-xs font-mono max-h-48 overflow-y-auto">
                                    <pre className="whitespace-pre-wrap">
                                        {JSON.stringify(recipe.ai_result, null, 2).substring(0, 1000)}...
                                    </pre>
                                </div>
                            )}
                        </div>
                    )}
                    
                    {/* Action buttons */}
                    {(recipe.status === 'ready' || recipe.status === 'duplicate') && (
                        <div className="flex gap-2">
                            <Button 
                                size="sm" 
                                className="bg-green-600 hover:bg-green-700"
                                onClick={() => onAction(recipe.index, 'approve')}
                            >
                                <CheckCircle className="w-3 h-3 mr-1" /> Approve & Save
                            </Button>
                            <Button 
                                size="sm" 
                                variant="outline"
                                onClick={() => onAction(recipe.index, 'skip')}
                            >
                                <SkipForward className="w-3 h-3 mr-1" /> Skip
                            </Button>
                        </div>
                    )}
                </CardContent>
            )}
        </Card>
    );
};

// Main component
export const AdminDocumentImportPage = () => {
    const [url, setUrl] = useState('');
    const [country, setCountry] = useState('Chile');
    const [loading, setLoading] = useState(false);
    const [session, setSession] = useState(null);
    const [processing, setProcessing] = useState(false);
    const [expandedRecipe, setExpandedRecipe] = useState(null);
    const navigate = useNavigate();

    const getAuthHeaders = () => {
        const token = localStorage.getItem('admin_token');
        return { Authorization: `Bearer ${token}` };
    };

    // Start import from URL
    const handleImportUrl = async () => {
        if (!url.trim()) {
            toast.error('Please enter a document URL');
            return;
        }

        setLoading(true);
        try {
            const response = await axios.post(
                `${API_URL}/api/admin/import/document-url`,
                { url, country, batch_size: 5 },
                { headers: getAuthHeaders() }
            );

            if (response.data.success) {
                toast.success(`Detected ${response.data.total_recipes} recipes!`);
                setSession(response.data);
                // Fetch full session
                await fetchSession(response.data.session_id);
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

    // Fetch session details
    const fetchSession = async (sessionId) => {
        try {
            const response = await axios.get(
                `${API_URL}/api/admin/import/session/${sessionId}`,
                { headers: getAuthHeaders() }
            );
            setSession(response.data);
        } catch (error) {
            toast.error('Failed to fetch session');
        }
    };

    // Process next batch
    const handleProcessBatch = async () => {
        if (!session?.session_id) return;

        setProcessing(true);
        try {
            const response = await axios.post(
                `${API_URL}/api/admin/import/session/${session.session_id}/process`,
                { batch_size: 5 },
                { headers: getAuthHeaders() }
            );

            if (response.data.success) {
                const processed = response.data.processed || [];
                toast.success(`Processed ${processed.length} recipes`);
                setSession(response.data.session);
            }
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Processing failed');
        } finally {
            setProcessing(false);
        }
    };

    // Recipe action (approve/skip)
    const handleRecipeAction = async (index, action) => {
        try {
            const response = await axios.post(
                `${API_URL}/api/admin/import/session/${session.session_id}/recipe/${index}/action`,
                { action },
                { headers: getAuthHeaders() }
            );

            if (response.data.success) {
                toast.success(action === 'approve' ? 'Recipe saved!' : 'Recipe skipped');
                setSession(response.data.session);
            }
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Action failed');
        }
    };

    // Edit recipe
    const handleEditRecipe = async (index, editedData) => {
        try {
            const response = await axios.post(
                `${API_URL}/api/admin/import/session/${session.session_id}/recipe/${index}/action`,
                { action: 'edit', edited_data: editedData },
                { headers: getAuthHeaders() }
            );

            if (response.data.success) {
                setSession(response.data.session);
            }
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Edit failed');
        }
    };

    // Approve all ready
    const handleApproveAll = async () => {
        if (!session?.session_id) return;

        try {
            const response = await axios.post(
                `${API_URL}/api/admin/import/session/${session.session_id}/approve-all`,
                {},
                { headers: getAuthHeaders() }
            );

            if (response.data.success) {
                toast.success(`Saved ${response.data.saved.length} recipes!`);
                setSession(response.data.session);
            }
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Bulk approve failed');
        }
    };

    // Calculate progress
    const getProgress = () => {
        if (!session?.recipes) return 0;
        const done = session.recipes.filter(r => 
            ['saved', 'skipped', 'error'].includes(r.status)
        ).length;
        return (done / session.total_recipes) * 100;
    };

    const pendingCount = session?.recipes?.filter(r => r.status === 'pending').length || 0;
    const readyCount = session?.recipes?.filter(r => r.status === 'ready' || r.status === 'duplicate').length || 0;

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <div className="max-w-5xl mx-auto">
                {/* Header */}
                <div className="flex items-center gap-4 mb-6">
                    <Link to="/admin/recipes">
                        <Button variant="outline" size="sm">
                            <ArrowLeft className="w-4 h-4 mr-2" /> Back
                        </Button>
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold">Import Document</h1>
                        <p className="text-sm text-gray-500">Extract recipes from PDF/ODF documents</p>
                    </div>
                </div>

                {/* URL Input */}
                {!session && (
                    <Card className="mb-6">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <LinkIcon className="w-5 h-5" /> Import from URL
                            </CardTitle>
                            <CardDescription>
                                Enter a URL to a PDF or ODF document containing recipes
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">Document URL</label>
                                <Input
                                    placeholder="https://example.com/recipes.pdf"
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">Origin Country</label>
                                <Input
                                    placeholder="Chile"
                                    value={country}
                                    onChange={(e) => setCountry(e.target.value)}
                                />
                                <p className="text-xs text-gray-500 mt-1">
                                    The country of origin for recipes in this document
                                </p>
                            </div>
                            <Button 
                                onClick={handleImportUrl} 
                                disabled={loading}
                                className="bg-amber-700 hover:bg-amber-800"
                            >
                                {loading ? (
                                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Parsing...</>
                                ) : (
                                    <><FileText className="w-4 h-4 mr-2" /> Parse Document</>
                                )}
                            </Button>
                        </CardContent>
                    </Card>
                )}

                {/* Session Progress */}
                {session && (
                    <>
                        <Card className="mb-6">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle>Import Session</CardTitle>
                                        <CardDescription>
                                            Language: {session.document_language?.toUpperCase()} | 
                                            Total: {session.total_recipes} recipes
                                        </CardDescription>
                                    </div>
                                    <Button 
                                        variant="outline" 
                                        size="sm"
                                        onClick={() => setSession(null)}
                                    >
                                        <RefreshCw className="w-4 h-4 mr-1" /> New Import
                                    </Button>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    {/* Progress bar */}
                                    <div>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span>Progress</span>
                                            <span>{Math.round(getProgress())}%</span>
                                        </div>
                                        <Progress value={getProgress()} className="h-2" />
                                    </div>
                                    
                                    {/* Stats */}
                                    <div className="grid grid-cols-4 gap-4 text-center">
                                        <div className="bg-gray-100 rounded p-2">
                                            <div className="text-xl font-bold">{pendingCount}</div>
                                            <div className="text-xs text-gray-500">Pending</div>
                                        </div>
                                        <div className="bg-green-100 rounded p-2">
                                            <div className="text-xl font-bold text-green-700">{session.saved_count || 0}</div>
                                            <div className="text-xs text-gray-500">Saved</div>
                                        </div>
                                        <div className="bg-gray-100 rounded p-2">
                                            <div className="text-xl font-bold">{session.skipped_count || 0}</div>
                                            <div className="text-xs text-gray-500">Skipped</div>
                                        </div>
                                        <div className="bg-blue-100 rounded p-2">
                                            <div className="text-xl font-bold text-blue-700">{readyCount}</div>
                                            <div className="text-xs text-gray-500">Ready</div>
                                        </div>
                                    </div>
                                    
                                    {/* Action buttons */}
                                    <div className="flex gap-2">
                                        {pendingCount > 0 && (
                                            <Button 
                                                onClick={handleProcessBatch}
                                                disabled={processing}
                                                className="bg-blue-600 hover:bg-blue-700"
                                            >
                                                {processing ? (
                                                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Processing...</>
                                                ) : (
                                                    <><Play className="w-4 h-4 mr-2" /> Process Next Batch (5)</>
                                                )}
                                            </Button>
                                        )}
                                        {readyCount > 0 && (
                                            <Button 
                                                onClick={handleApproveAll}
                                                className="bg-green-600 hover:bg-green-700"
                                            >
                                                <CheckCircle className="w-4 h-4 mr-2" /> 
                                                Approve All Ready ({readyCount})
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Recipe List */}
                        <div className="space-y-2">
                            <h3 className="font-medium text-gray-700">Recipes</h3>
                            {session.recipes?.map((recipe, idx) => (
                                <RecipeCard
                                    key={recipe.index}
                                    recipe={recipe}
                                    expanded={expandedRecipe === idx}
                                    onToggle={() => setExpandedRecipe(expandedRecipe === idx ? null : idx)}
                                    onAction={handleRecipeAction}
                                    onEdit={handleEditRecipe}
                                />
                            ))}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default AdminDocumentImportPage;
