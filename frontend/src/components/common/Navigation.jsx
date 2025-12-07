import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ChefHat, Globe, BookOpen, Menu as MenuIcon, Heart, User, LogOut } from 'lucide-react';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';
import { AuthModal } from '@/components/auth/AuthModal';
import { LanguageSelector } from '@/components/common/LanguageSelector';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export const Navigation = () => {
    const { user, logout } = useAuth();
    const [showAuthModal, setShowAuthModal] = useState(false);

    const navLinks = [
        { to: '/regions', label: 'Regions', icon: Globe },
        { to: '/menu-builder', label: 'Menu Builder', icon: MenuIcon },
        { to: '/techniques', label: 'Techniques', icon: BookOpen },
        { to: '/about', label: 'About', icon: null },
    ];

    return (
        <>
            <nav className="bg-white border-b border-[#E5DCC3] sticky top-0 z-50" data-testid="main-navigation">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        {/* Logo */}
                        <Link to="/" className="flex items-center space-x-2" data-testid="logo-link">
                            <ChefHat className="h-8 w-8 text-[#6A1F2E]" />
                            <span className="text-2xl font-bold text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                Sous Chef Linguine
                            </span>
                        </Link>

                        {/* Desktop Navigation */}
                        <div className="hidden md:flex items-center space-x-6">
                            {navLinks.map((link) => (
                                <Link
                                    key={link.to}
                                    to={link.to}
                                    className="flex items-center space-x-1 text-[#1E1E1E] hover:text-[#6A1F2E] transition-colors duration-200"
                                    data-testid={`nav-${link.label.toLowerCase().replace(' ', '-')}`}
                                >
                                    {link.icon && <link.icon className="h-4 w-4" />}
                                    <span>{link.label}</span>
                                </Link>
                            ))}
                            
                            {/* Language Selector */}
                            <LanguageSelector />
                            
                            {/* Auth Section */}
                            {user ? (
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button variant="ghost" size="icon">
                                            <User className="h-5 w-5" />
                                        </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent>
                                        <DropdownMenuItem asChild>
                                            <Link to="/favorites" className="flex items-center">
                                                <Heart className="h-4 w-4 mr-2" />
                                                Favorites
                                            </Link>
                                        </DropdownMenuItem>
                                        <DropdownMenuItem onClick={logout}>
                                            <LogOut className="h-4 w-4 mr-2" />
                                            Logout
                                        </DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            ) : (
                                <Button 
                                    onClick={() => setShowAuthModal(true)}
                                    variant="outline"
                                    size="sm"
                                >
                                    Login
                                </Button>
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
                                            key={link.to}
                                            to={link.to}
                                            className="flex items-center space-x-2 text-lg text-[#1E1E1E] hover:text-[#6A1F2E] transition-colors"
                                        >
                                            {link.icon && <link.icon className="h-5 w-5" />}
                                            <span>{link.label}</span>
                                        </Link>
                                    ))}
                                    {user && (
                                        <Link to="/favorites" className="flex items-center space-x-2 text-lg text-[#1E1E1E] hover:text-[#6A1F2E] transition-colors">
                                            <Heart className="h-5 w-5" />
                                            <span>Favorites</span>
                                        </Link>
                                    )}
                                </div>
                            </SheetContent>
                        </Sheet>
                    </div>
                </div>
            </nav>
            
            <AuthModal open={showAuthModal} onClose={() => setShowAuthModal(false)} />
        </>
    );
};