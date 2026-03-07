import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n/translations';
import { authAPI } from '@/utils/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Loader2, Mail, ArrowLeft, CheckCircle } from 'lucide-react';

const ForgotPasswordPage = () => {
    const { language, getLocalizedPath } = useLanguage();
    const lang = language || 'en';

    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [sent, setSent] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await authAPI.requestPasswordReset(email);
            setSent(true);
            toast.success(t('auth.resetEmailSent', lang));
        } catch {
            toast.success(t('auth.resetEmailSent', lang));
            setSent(true);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#FDFBF7] px-4 py-12">
            <Card className="w-full max-w-md border-[#E8E4DC]">
                <CardHeader className="text-center">
                    <div className="mx-auto mb-4 w-12 h-12 bg-[#6A1F2E] rounded-full flex items-center justify-center">
                        <Mail className="text-white w-5 h-5" />
                    </div>
                    <CardTitle className="text-2xl" style={{ fontFamily: 'var(--font-heading)' }}>
                        {t('auth.resetPassword', lang)}
                    </CardTitle>
                    <CardDescription>
                        {t('auth.resetDescription', lang)}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {sent ? (
                        <div className="text-center py-4" data-testid="reset-sent-confirmation">
                            <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-3" />
                            <p className="text-[#2C2C2C] font-medium mb-2">
                                {t('auth.resetEmailSent', lang)}
                            </p>
                            <p className="text-sm text-[#7C7C7C] mb-6">
                                {t('auth.checkInbox', lang)}
                            </p>
                            <Link to={getLocalizedPath('/login')}>
                                <Button variant="outline" className="border-[#6A1F2E] text-[#6A1F2E]">
                                    <ArrowLeft className="w-4 h-4 mr-2" />
                                    {t('auth.backToLogin', lang)}
                                </Button>
                            </Link>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="email">{t('auth.email', lang)}</Label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#7C7C7C]" />
                                    <Input
                                        id="email"
                                        type="email"
                                        placeholder="you@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        disabled={loading}
                                        className="pl-10 border-[#E8E4DC] focus:border-[#6A1F2E] focus:ring-[#6A1F2E]/20"
                                        data-testid="reset-email-input"
                                    />
                                </div>
                            </div>

                            <Button
                                type="submit"
                                className="w-full h-11 bg-[#6A1F2E] hover:bg-[#8B2840]"
                                disabled={loading}
                                data-testid="reset-submit-btn"
                            >
                                {loading ? (
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                ) : null}
                                {t('auth.sendResetLink', lang)}
                            </Button>

                            <p className="text-center text-sm text-[#7C7C7C]">
                                <Link
                                    to={getLocalizedPath('/login')}
                                    className="text-[#6A1F2E] font-medium hover:underline"
                                >
                                    <ArrowLeft className="w-3 h-3 inline mr-1" />
                                    {t('auth.backToLogin', lang)}
                                </Link>
                            </p>
                        </form>
                    )}
                </CardContent>
            </Card>
        </div>
    );
};

export default ForgotPasswordPage;
