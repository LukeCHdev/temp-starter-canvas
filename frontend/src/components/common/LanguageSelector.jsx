import React from 'react';
import { Globe } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/context/LanguageContext';

export const LanguageSelector = () => {
    const { language, changeLanguage, supportedLanguages } = useLanguage();
    
    // Get current language info safely
    const currentLangInfo = supportedLanguages[language] || supportedLanguages['es'];

    const handleLanguageChange = (langCode) => {
        if (langCode !== language) {
            changeLanguage(langCode);
        }
    };

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button 
                    variant="ghost" 
                    size="sm" 
                    data-testid="language-selector"
                    className="font-sans text-sm"
                    style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
                >
                    <Globe className="h-4 w-4 mr-2" />
                    <span style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
                        {currentLangInfo.flag}
                    </span>
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="min-w-[140px]">
                {Object.values(supportedLanguages).map((lang) => (
                    <DropdownMenuItem
                        key={lang.code}
                        onSelect={() => handleLanguageChange(lang.code)}
                        className={`cursor-pointer ${language === lang.code ? 'bg-[#F5F2E8]' : ''}`}
                        style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
                    >
                        <span className="mr-2" style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
                            {lang.flag}
                        </span>
                        <span style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
                            {lang.name}
                        </span>
                    </DropdownMenuItem>
                ))}
            </DropdownMenuContent>
        </DropdownMenu>
    );
};
