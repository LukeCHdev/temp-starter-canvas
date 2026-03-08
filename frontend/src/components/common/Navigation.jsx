import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Search, Menu as MenuIcon, X, User, LogOut, Heart } from 'lucide-react';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';
import { LanguageSelector } from '@/components/common/LanguageSelector';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n/translations';
import { toast } from 'sonner';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

export const Navigation = () => {
    const { user, isAuthenticated, logout } = useAuth();
    const { t: i18nT } = useTranslation();
    const { language, getLocalizedPath } = useLanguage();
    const location = useLocation();
    const lang = language || 'en';

    // Feature flag for Menu Builder
    const enableMenuBuilder = process.env.REACT_APP_ENABLE_MENU_BUILDER === 'true';

    const navLinks = [
        { path: '/explore', label: i18nT('nav.explore') },
        { path: '/techniques', label: i18nT('nav.techniques') },
        // Menu Builder is conditionally included based on feature flag
        ...(enableMenuBuilder ? [{ path: '/menu-builder', label: i18nT('nav.menuBuilder') }] : []),
        { path: '/about', label: i18nT('nav.about') },
    ];

    if (user) {
        navLinks.push({ path: '/favorites', label: i18nT('nav.favorites') });
    }

    const handleLogout = async () => {
        await logout();
        toast.success(t('auth.logoutSuccess', lang));
    };

    const currentPath = location.pathname;

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 bg-background/90 backdrop-blur-md border-b border-border" data-testid="main-navigation">
            <div className="container mx-auto flex items-center justify-between h-20 px-6">
                {/* Logo — Elegant Sona style */}
                <Link to={getLocalizedPath('/')} className="flex items-center gap-2 min-w-0 shrink" data-testid="logo-link">
                    <span className="text-2xl sm:text-3xl font-semibold tracking-wider text-foreground" style={{ fontFamily: 'var(--font-heading)' }}>
                        SOUS CHEF <span className="text-primary">LINGUINE</span>
                    </span>
                </Link>

                {/* Desktop Navigation */}
                <div className="hidden md:flex items-center gap-8">
                    {navLinks.map((link) => (
                        <Link
                            key={link.path}
                            to={getLocalizedPath(link.path)}
                            className="text-sm font-medium tracking-wide text-muted-foreground hover:text-primary transition-colors duration-300"
                            style={{ fontFamily: 'var(--font-body)' }}
                            data-testid={`nav-${link.path.replace('/', '')}`}
                        >
                            {link.label}
                        </Link>
                    ))}
                    
                    {/* Language Selector */}
                    <LanguageSelector />
                    
                    {/* Auth Section */}
                    {isAuthenticated && user ? (
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" className="flex items-center gap-2 text-muted-foreground hover:text-primary">
                                    {user.avatar_url ? (
                                        <img 
                                            src={user.avatar_url} 
                                            alt={user.username} 
                                            className="w-7 h-7 rounded-full object-cover"
                                        />
                                    ) : (
                                        <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center">
                                            <span className="text-primary-foreground text-xs font-medium">
                                                {user.username?.[0]?.toUpperCase() || 'U'}
                                            </span>
                                        </div>
                                    )}
                                    <span className="text-sm">{user.username}</span>
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-48">
                                <div className="px-2 py-1.5">
                                    <p className="text-sm font-medium">{user.name || user.username}</p>
                                    <p className="text-xs text-muted-foreground">{user.email}</p>
                                </div>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={handleLogout} className="text-destructive cursor-pointer">
                                    <LogOut className="h-4 w-4 mr-2" />
                                    {t('auth.logout', lang)}
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    ) : (
                        <Link to={getLocalizedPath(`/login?redirect=${encodeURIComponent(currentPath)}`)}>
                            <Button 
                                variant="ghost"
                                size="sm"
                                className="text-muted-foreground hover:text-primary transition-colors"
                                style={{ fontFamily: 'var(--font-body)' }}
                            >
                                {t('auth.login', lang)}
                            </Button>
                        </Link>
                    )}
                </div>

                {/* Mobile Navigation */}
                <Sheet>
                    <SheetTrigger asChild className="md:hidden">
                        <Button variant="ghost" size="icon" className="text-foreground" data-testid="mobile-menu-trigger">
                            <MenuIcon className="h-6 w-6" />
                        </Button>
                    </SheetTrigger>
                    <SheetContent className="bg-background border-border">
                        <div className="flex flex-col space-y-4 mt-8">
                            {navLinks.map((link) => (
                                <Link
                                    key={link.path}
                                    to={getLocalizedPath(link.path)}
                                    className="text-base text-muted-foreground hover:text-primary transition-colors"
                                    style={{ fontFamily: 'var(--font-body)' }}
                                >
                                    {link.label}
                                </Link>
                            ))}
                            
                            {/* Mobile Auth */}
                            {isAuthenticated && user ? (
                                 <div className="pt-4 border-t border-border">
                                    <div className="flex items-center gap-3 mb-4">
                                        {user.avatar_url ? (
                                            <img 
                                                src={user.avatar_url} 
                                                alt={user.username} 
                                                className="w-10 h-10 rounded-full object-cover"
                                            />
                                        ) : (
                                            <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
                                                <span className="text-primary-foreground font-medium">
                                                    {user.username?.[0]?.toUpperCase() || 'U'}
                                                </span>
                                            </div>
                                        )}
                                        <div>
                                            <p className="font-medium text-foreground">{user.name || user.username}</p>
                                            <p className="text-sm text-muted-foreground">{user.email}</p>
                                        </div>
                                    </div>
                                    <Button 
                                        variant="outline" 
                                        className="w-full text-destructive border-destructive/30"
                                        onClick={handleLogout}
                                    >
                                        <LogOut className="h-4 w-4 mr-2" />
                                        {t('auth.logout', lang)}
                                    </Button>
                                </div>
                            ) : (
                                 <div className="pt-4 border-t border-border">
                                    <Link to={getLocalizedPath(`/login?redirect=${encodeURIComponent(currentPath)}`)}>
                                        <Button className="w-full bg-primary hover:bg-primary/90 text-primary-foreground">
                                            {t('auth.login', lang)}
                                        </Button>
                                    </Link>
                                </div>
                            )}
                            
                            {/* Mobile Language Selector */}
                            <div className="pt-4 border-t border-border">
                                <LanguageSelector />
                            </div>
                        </div>
                    </SheetContent>
                </Sheet>
            </div>
        </nav>
    );
};
