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

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" data-testid="language-selector">
                    <Globe className="h-4 w-4 mr-2" />
                    {supportedLanguages[language].flag}
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
                {Object.values(supportedLanguages).map((lang) => (
                    <DropdownMenuItem
                        key={lang.code}
                        onClick={() => changeLanguage(lang.code)}
                        className={language === lang.code ? 'bg-[#F5F2E8]' : ''}
                    >
                        <span className="mr-2">{lang.flag}</span>
                        {lang.name}
                    </DropdownMenuItem>
                ))}
            </DropdownMenuContent>
        </DropdownMenu>
    );
};
