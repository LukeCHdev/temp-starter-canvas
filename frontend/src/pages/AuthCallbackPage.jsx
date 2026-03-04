import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n/translations';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';

const AuthCallbackPage = () => {
    const { login } = useAuth();
    const { language, getLocalizedPath } = useLanguage();
    const lang = language || 'en';
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [status, setStatus] = useState('loading');
    const [error, setError] = useState('');

    useEffect(() => {
        const handleCallback = async () => {
            const sessionId = searchParams.get('session_id');
            const errorParam = searchParams.get('error');

            if (errorParam) {
                setStatus('error');
                setError(errorParam);
                return;
            }

            if (!sessionId) {
                setStatus('error');
                setError(t('auth.invalidCallback', lang));
                return;
            }

            try {
                await login(null, null, sessionId);
                setStatus('success');

                const returnTo = localStorage.getItem('auth_return_to');
                localStorage.removeItem('auth_return_to');

                setTimeout(() => {
                    navigate(returnTo || getLocalizedPath('/'), { replace: true });
                }, 1000);
            } catch (err) {
                setStatus('error');
                setError(err.message || t('auth.loginFailed', lang));
            }
        };
        handleCallback();
    }, [searchParams, login, navigate, getLocalizedPath, lang]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#FDFBF7]" data-testid="auth-callback-page">
            <div className="text-center p-8 max-w-sm">
                {status === 'loading' && (
                    <div data-testid="auth-callback-loading">
                        <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-[#6A1F2E]" />
                        <p className="text-lg text-[#2C2C2C]">{t('auth.completingSignIn', lang)}</p>
                    </div>
                )}
                {status === 'success' && (
                    <div data-testid="auth-callback-success">
                        <CheckCircle className="h-8 w-8 mx-auto mb-4 text-green-600" />
                        <p className="text-lg text-[#2C2C2C] font-medium">{t('auth.loginSuccess', lang)}</p>
                        <p className="text-sm text-[#7C7C7C] mt-2">{t('auth.redirecting', lang)}</p>
                    </div>
                )}
                {status === 'error' && (
                    <div data-testid="auth-callback-error">
                        <XCircle className="h-8 w-8 mx-auto mb-4 text-red-500" />
                        <p className="text-lg text-[#2C2C2C] font-medium">{t('auth.loginFailed', lang)}</p>
                        <p className="text-sm text-red-500 mt-2">{error}</p>
                        <button
                            className="mt-4 text-sm text-[#6A1F2E] font-medium hover:underline"
                            onClick={() => navigate(getLocalizedPath('/login'), { replace: true })}
                        >
                            {t('auth.backToLogin', lang)}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AuthCallbackPage;
