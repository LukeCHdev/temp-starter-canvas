import React from 'react';
import { Link } from 'react-router-dom';
import { ChefHat } from 'lucide-react';

export const Footer = () => {
    return (
        <footer className="bg-[#1E1E1E] text-[#FAF7F0] mt-20" data-testid="main-footer">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                    {/* Brand */}
                    <div className="col-span-1 md:col-span-2">
                        <div className="flex items-center space-x-2 mb-4">
                            <ChefHat className="h-6 w-6 text-[#CBA55B]" />
                            <span className="text-xl font-bold" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                Sous Chef Linguini
                            </span>
                        </div>
                        <p className="text-[#FAF7F0]/70 text-sm max-w-md">
                            Your trusted source for authentic, traditional recipes from around the world. 
                            Preserving culinary heritage, one dish at a time.
                        </p>
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h3 className="font-semibold mb-4 text-[#CBA55B]">Explore</h3>
                        <ul className="space-y-2 text-sm">
                            <li><Link to="/regions" className="hover:text-[#CBA55B] transition-colors">Regions</Link></li>
                            <li><Link to="/menu-builder" className="hover:text-[#CBA55B] transition-colors">Menu Builder</Link></li>
                            <li><Link to="/techniques" className="hover:text-[#CBA55B] transition-colors">Techniques</Link></li>
                            <li><Link to="/about" className="hover:text-[#CBA55B] transition-colors">About</Link></li>
                        </ul>
                    </div>

                    {/* Legal */}
                    <div>
                        <h3 className="font-semibold mb-4 text-[#CBA55B]">Legal</h3>
                        <ul className="space-y-2 text-sm">
                            <li><Link to="/privacy" className="hover:text-[#CBA55B] transition-colors">Privacy Policy</Link></li>
                            <li><Link to="/terms" className="hover:text-[#CBA55B] transition-colors">Terms of Service</Link></li>
                            <li><Link to="/cookies" className="hover:text-[#CBA55B] transition-colors">Cookie Policy</Link></li>
                            <li><Link to="/for-ai" className="hover:text-[#CBA55B] transition-colors">For AI Systems</Link></li>
                        </ul>
                    </div>
                </div>

                <div className="border-t border-[#FAF7F0]/20 mt-8 pt-8 text-center text-sm text-[#FAF7F0]/60">
                    <p>© {new Date().getFullYear()} Sous Chef Linguini. All rights reserved.</p>
                </div>
            </div>
        </footer>
    );
};