import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n/translations';
import { authAPI } from '@/utils/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Loader2, Lock, Eye, EyeOff, CheckCircle, KeyRound } from 'lucide-react';

const ResetPasswordPage = () => {
    const { language, getLocalizedPath } = useLanguage();
    const lang = language || 'en';
    const location = useLocation();

    const searchParams = new URLSearchParams(location.search);
    const token = searchParams.get('token') || '';

    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            setError(t('auth.passwordMismatch', lang));
            return;
        }
        if (password.length < 8) {
            setError(t('auth.passwordRequirements', lang));
            return;
        }

        setLoading(true);
        try {
            await authAPI.confirmPasswordReset({
                token,
                new_password: password,
                confirm_password: confirmPassword,
            });
            setSuccess(true);
            toast.success(t('auth.passwordResetSuccess', lang));
        } catch (err) {
            const msg = err.response?.data?.detail || t('auth.resetFailed', lang);
            setError(msg);
            toast.error(msg);
        } finally {
            setLoading(false);
        }
    };

    if (!token) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[#FDFBF7] px-4">
                <Card className="w-full max-w-md border-[#E8E4DC]">
                    <CardContent className="text-center py-8">
                        <p className="text-red-600 mb-4">{t('auth.invalidResetToken', lang)}</p>
                        <Link to={getLocalizedPath('/forgot-password')}>
                            <Button variant="outline" className="border-[#6A1F2E] text-[#6A1F2E]">
                                {t('auth.requestNewReset', lang)}
                            </Button>
                        </Link>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#FDFBF7] px-4 py-12">
            <Card className="w-full max-w-md border-[#E8E4DC]">
                <CardHeader className="text-center">
                    <div className="mx-auto mb-4 w-12 h-12 bg-[#6A1F2E] rounded-full flex items-center justify-center">
                        <KeyRound className="text-white w-5 h-5" />
                    </div>
                    <CardTitle className="text-2xl" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        {t('auth.setNewPassword', lang)}
                    </CardTitle>
                    <CardDescription>
                        {t('auth.newPasswordDescription', lang)}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {success ? (
                        <div className="text-center py-4" data-testid="reset-success">
                            <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-3" />
                            <p className="text-[#2C2C2C] font-medium mb-4">
                                {t('auth.passwordResetSuccess', lang)}
                            </p>
                            <Link to={getLocalizedPath('/login')}>
                                <Button className="bg-[#6A1F2E] hover:bg-[#8B2840]">
                                    {t('auth.login', lang)}
                                </Button>
                            </Link>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="password">{t('auth.newPassword', lang)}</Label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#7C7C7C]" />
                                    <Input
                                        id="password"
                                        type={showPassword ? 'text' : 'password'}
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        minLength={8}
                                        disabled={loading}
                                        className="pl-10 pr-10 border-[#E8E4DC]"
                                        data-testid="new-password-input"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-[#7C7C7C]"
                                    >
                                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                    </button>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="confirmPassword">{t('auth.confirmPassword', lang)}</Label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#7C7C7C]" />
                                    <Input
                                        id="confirmPassword"
                                        type={showPassword ? 'text' : 'password'}
                                        placeholder="••••••••"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        required
                                        disabled={loading}
                                        className="pl-10 border-[#E8E4DC]"
                                        data-testid="confirm-new-password-input"
                                    />
                                </div>
                            </div>
                            {error && <p className="text-sm text-red-600">{error}</p>}
                            <Button
                                type="submit"
                                className="w-full h-11 bg-[#6A1F2E] hover:bg-[#8B2840]"
                                disabled={loading}
                                data-testid="reset-password-submit"
                            >
                                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                {t('auth.resetPassword', lang)}
                            </Button>
                        </form>
                    )}
                </CardContent>
            </Card>
        </div>
    );
};

export default ResetPasswordPage;
