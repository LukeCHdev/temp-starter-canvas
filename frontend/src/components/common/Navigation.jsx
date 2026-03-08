import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ChefHat, Globe, Menu as MenuIcon, User, LogOut, Heart, Flame } from 'lucide-react';
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

    // All navigation links use getLocalizedPath to preserve language
    const navLinks = [
        { path: '/explore', label: i18nT('nav.explore'), icon: Globe },
        { path: '/techniques', label: i18nT('nav.techniques'), icon: Flame },
        { path: '/menu-builder', label: i18nT('nav.menuBuilder'), icon: MenuIcon },
        { path: '/about', label: i18nT('nav.about'), icon: null },
    ];

    // Add favorites link when logged in
    if (user) {
        navLinks.push({ path: '/favorites', label: i18nT('nav.favorites'), icon: Heart });
    }

    const handleLogout = async () => {
        await logout();
        toast.success(t('auth.logoutSuccess', lang));
    };

    // Get current path for redirect after login
    const currentPath = location.pathname;

    return (
        <nav className="bg-card/80 backdrop-blur-md border-b border-border sticky top-0 z-50" data-testid="main-navigation">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-16">
                    {/* Logo */}
                    <Link to={getLocalizedPath('/')} className="flex items-center gap-2 min-w-0 shrink" data-testid="logo-link">
                        <ChefHat className="h-7 w-7 sm:h-8 sm:w-8 text-primary flex-shrink-0" />
                        <span className="text-lg sm:text-2xl font-semibold text-foreground truncate tracking-tight" style={{ fontFamily: 'var(--font-heading)' }}>
                            Sous Chef Linguine
                        </span>
                    </Link>

                    {/* Desktop Navigation */}
                    <div className="hidden md:flex items-center space-x-6">
                        {navLinks.map((link) => (
                            <Link
                                key={link.path}
                                to={getLocalizedPath(link.path)}
                                className="nav-link-elegant flex items-center space-x-1 text-foreground hover:text-primary transition-colors duration-200 text-sm tracking-wide"
                                style={{ fontFamily: 'var(--font-body)' }}
                                data-testid={`nav-${link.path.replace('/', '')}`}
                            >
                                {link.icon && <link.icon className="h-4 w-4" />}
                                <span>{link.label}</span>
                            </Link>
                        ))}
                        
                        {/* Language Selector */}
                        <LanguageSelector />
                        
                        {/* Auth Section */}
                        {isAuthenticated && user ? (
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" className="flex items-center gap-2">
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
                                        <p className="text-xs text-gray-500">{user.email}</p>
                                    </div>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem onClick={handleLogout} className="text-red-600 cursor-pointer">
                                        <LogOut className="h-4 w-4 mr-2" />
                                        {t('auth.logout', lang)}
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        ) : (
                            <Link to={getLocalizedPath(`/login?redirect=${encodeURIComponent(currentPath)}`)}>
                                <Button 
                                    variant="outline"
                                    size="sm"
                                    className="border-primary text-primary hover:bg-primary hover:text-primary-foreground"
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
                            <Button variant="ghost" size="icon" data-testid="mobile-menu-trigger">
                                <MenuIcon className="h-6 w-6" />
                            </Button>
                        </SheetTrigger>
                        <SheetContent>
                            <div className="flex flex-col space-y-4 mt-8">
                                {navLinks.map((link) => (
                                    <Link
                                        key={link.path}
                                        to={getLocalizedPath(link.path)}
                                        className="flex items-center space-x-2 text-lg text-foreground hover:text-primary transition-colors"
                                        style={{ fontFamily: 'var(--font-body)' }}
                                    >
                                        {link.icon && <link.icon className="h-5 w-5" />}
                                        <span>{link.label}</span>
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
                                                <p className="font-medium">{user.name || user.username}</p>
                                                <p className="text-sm text-gray-500">{user.email}</p>
                                            </div>
                                        </div>
                                        <Button 
                                            variant="outline" 
                                            className="w-full text-red-600 border-red-200"
                                            onClick={handleLogout}
                                        >
                                            <LogOut className="h-4 w-4 mr-2" />
                                            {t('auth.logout', lang)}
                                        </Button>
                                    </div>
                                ) : (
                                    <div className="pt-4 border-t border-[#E5DCC3]">
                                        <Link to={getLocalizedPath(`/login?redirect=${encodeURIComponent(currentPath)}`)}>
                                            <Button className="w-full bg-[#6A1F2E] hover:bg-[#8B2840]">
                                                {t('auth.login', lang)}
                                            </Button>
                                        </Link>
                                    </div>
                                )}
                                
                                {/* Mobile Language Selector */}
                                <div className="pt-4 border-t border-[#E5DCC3]">
                                    <LanguageSelector />
                                </div>
                            </div>
                        </SheetContent>
                    </Sheet>
                </div>
            </div>
        </nav>
    );
};
