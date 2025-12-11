import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, ChefHat, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const AdminLoginPage = () => {
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        if (!password.trim()) {
            toast.error('Please enter the admin password');
            return;
        }

        setLoading(true);
        try {
            const response = await axios.post(`${API_URL}/api/admin/login`, { password });
            if (response.data.success) {
                localStorage.setItem('admin_token', response.data.token);
                toast.success('Login successful!');
                navigate('/admin/recipes');
            }
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Invalid password');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-amber-50 to-white flex items-center justify-center p-4">
            <Card className="w-full max-w-md">
                <CardHeader className="text-center">
                    <div className="mx-auto w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mb-4">
                        <ChefHat className="w-8 h-8 text-amber-700" />
                    </div>
                    <CardTitle className="text-2xl">Admin Panel</CardTitle>
                    <CardDescription>Sous Chef Linguine Recipe Management</CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleLogin} className="space-y-4">
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                            <Input
                                type={showPassword ? 'text' : 'password'}
                                placeholder="Enter admin password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="pl-10 pr-10"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                            >
                                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </button>
                        </div>
                        <Button type="submit" className="w-full bg-amber-700 hover:bg-amber-800" disabled={loading}>
                            {loading ? 'Logging in...' : 'Login'}
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
};

export default AdminLoginPage;
