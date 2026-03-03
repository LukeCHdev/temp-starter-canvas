import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useLanguage } from '@/context/LanguageContext';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';

const AuthCallbackPage = () => {
    const { handleGoogleCallback } = useAuth();
    const { getLocalizedPath } = useLanguage();
    const navigate = useNavigate();
    const location = useLocation();
    
    const [status, setStatus] = useState('processing'); // processing, success, error
    const [error, setError] = useState('');

    useEffect(() => {
        const processCallback = async () => {
            try {
                // Get session_id from URL hash fragment (Emergent Auth returns it this way)
                const hash = window.location.hash.substring(1);
                const params = new URLSearchParams(hash);
                const sessionId = params.get('session_id');
                
                // Get redirect URL from query params
                const searchParams = new URLSearchParams(location.search);
                const redirectTo = searchParams.get('redirect') || '/';

                if (!sessionId) {
                    throw new Error('No session ID received from authentication');
                }

                // Exchange session_id for user data
                await handleGoogleCallback(sessionId);
                
                setStatus('success');
                
                // Redirect after a short delay
                setTimeout(() => {
                    navigate(getLocalizedPath(redirectTo), { replace: true });
                }, 1000);
                
            } catch (err) {
                console.error('Auth callback error:', err);
                setStatus('error');
                setError(err.message || 'Authentication failed');
                
                // Redirect to login after error
                setTimeout(() => {
                    navigate(getLocalizedPath('/login'), { replace: true });
                }, 3000);
            }
        };

        processCallback();
    }, [handleGoogleCallback, navigate, location, getLocalizedPath]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#FDFBF7]">
            <div className="text-center">
                {status === 'processing' && (
                    <>
                        <Loader2 className="h-12 w-12 animate-spin text-[#6A1F2E] mx-auto mb-4" />
                        <p className="text-[#5C5C5C]">Completing sign in...</p>
                    </>
                )}
                
                {status === 'success' && (
                    <>
                        <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
                        <p className="text-[#2C2C2C] font-medium">Sign in successful!</p>
                        <p className="text-[#5C5C5C] text-sm mt-1">Redirecting...</p>
                    </>
                )}
                
                {status === 'error' && (
                    <>
                        <XCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
                        <p className="text-[#2C2C2C] font-medium">Sign in failed</p>
                        <p className="text-red-600 text-sm mt-1">{error}</p>
                        <p className="text-[#5C5C5C] text-sm mt-2">Redirecting to login...</p>
                    </>
                )}
            </div>
        </div>
    );
};

export default AuthCallbackPage;
