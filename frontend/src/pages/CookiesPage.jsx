import React from 'react';
import { Link } from 'react-router-dom';
import { Home, ChevronRight, Cookie } from 'lucide-react';

const CookiesPage = () => {
    return (
        <div className="min-h-screen bg-[#FAF7F0]">
            {/* Header */}
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-12 px-4">
                <div className="max-w-4xl mx-auto">
                    <nav className="flex items-center gap-2 text-sm text-[#1E1E1E]/60 mb-6">
                        <Link to="/" className="hover:text-[#6A1F2E] flex items-center gap-1">
                            <Home className="h-4 w-4" /> Home
                        </Link>
                        <ChevronRight className="h-4 w-4" />
                        <span className="text-[#6A1F2E] font-medium">Cookie Policy</span>
                    </nav>
                    <h1 className="text-4xl sm:text-5xl font-bold text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        Cookie Policy
                    </h1>
                    <p className="text-[#1E1E1E]/70 mt-4">Last updated: December 2024</p>
                </div>
            </section>

            <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="bg-white rounded-xl p-8 shadow-sm space-y-8">
                    
                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            What Are Cookies?
                        </h2>
                        <p className="text-[#1E1E1E]/80 leading-relaxed">
                            Cookies are small text files that are stored on your device when you visit a website. They are widely used to make websites work more efficiently and provide information to website owners.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            How We Use Cookies
                        </h2>
                        <p className="text-[#1E1E1E]/80 leading-relaxed mb-4">
                            Sous Chef Linguine uses cookies for the following purposes:
                        </p>
                        
                        <div className="space-y-4">
                            <div className="bg-[#F5F2E8] rounded-lg p-4">
                                <h3 className="font-semibold text-[#1E1E1E] mb-2">Essential Cookies</h3>
                                <p className="text-[#1E1E1E]/70 text-sm">Required for the website to function. These include authentication cookies that keep you logged in and remember your preferences.</p>
                            </div>
                            
                            <div className="bg-[#F5F2E8] rounded-lg p-4">
                                <h3 className="font-semibold text-[#1E1E1E] mb-2">Preference Cookies</h3>
                                <p className="text-[#1E1E1E]/70 text-sm">Remember your settings such as language preference, measurement units (metric/imperial), and display preferences.</p>
                            </div>
                            
                            <div className="bg-[#F5F2E8] rounded-lg p-4">
                                <h3 className="font-semibold text-[#1E1E1E] mb-2">Analytics Cookies</h3>
                                <p className="text-[#1E1E1E]/70 text-sm">Help us understand how visitors use our website by collecting anonymous statistics about page visits, search queries, and navigation patterns.</p>
                            </div>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            Cookies We Use
                        </h2>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-[#E5DCC3]">
                                        <th className="text-left py-3 px-4 font-semibold">Cookie Name</th>
                                        <th className="text-left py-3 px-4 font-semibold">Purpose</th>
                                        <th className="text-left py-3 px-4 font-semibold">Duration</th>
                                    </tr>
                                </thead>
                                <tbody className="text-[#1E1E1E]/70">
                                    <tr className="border-b border-[#E5DCC3]/50">
                                        <td className="py-3 px-4">auth_token</td>
                                        <td className="py-3 px-4">Authentication</td>
                                        <td className="py-3 px-4">Session</td>
                                    </tr>
                                    <tr className="border-b border-[#E5DCC3]/50">
                                        <td className="py-3 px-4">language</td>
                                        <td className="py-3 px-4">Language preference</td>
                                        <td className="py-3 px-4">1 year</td>
                                    </tr>
                                    <tr className="border-b border-[#E5DCC3]/50">
                                        <td className="py-3 px-4">units</td>
                                        <td className="py-3 px-4">Measurement units</td>
                                        <td className="py-3 px-4">1 year</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            Managing Cookies
                        </h2>
                        <p className="text-[#1E1E1E]/80 leading-relaxed mb-4">
                            You can control and manage cookies in various ways:
                        </p>
                        <ul className="list-disc pl-6 space-y-2 text-[#1E1E1E]/80">
                            <li>Most browsers allow you to refuse or accept cookies</li>
                            <li>You can delete cookies that have already been set</li>
                            <li>You can set your browser to notify you when cookies are being set</li>
                        </ul>
                        <p className="text-[#1E1E1E]/70 text-sm mt-4 italic">
                            Note: Disabling cookies may affect the functionality of our website, particularly features that require you to be logged in.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            Contact Us
                        </h2>
                        <p className="text-[#1E1E1E]/80 leading-relaxed">
                            If you have questions about our use of cookies, please contact us through our <Link to="/contact" className="text-[#6A1F2E] hover:underline">Contact page</Link>.
                        </p>
                    </section>

                </div>
            </section>
        </div>
    );
};

export default CookiesPage;
