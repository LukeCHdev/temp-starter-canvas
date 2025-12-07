import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Award, BookOpen, Sparkles } from 'lucide-react';

export const AuthenticityBadge = ({ rank, classification }) => {
    const configs = {
        1: {
            color: 'bg-[#CBA55B] text-white border-[#CBA55B]',
            icon: Award,
            label: 'Official'
        },
        2: {
            color: 'bg-[#3F4A3C] text-white border-[#3F4A3C]',
            icon: BookOpen,
            label: 'Traditional'
        },
        3: {
            color: 'bg-[#6A1F2E] text-white border-[#6A1F2E]',
            icon: Sparkles,
            label: 'Modern'
        }
    };
    
    const config = configs[rank] || configs[2];
    const Icon = config.icon;

    return (
        <div className="inline-flex items-center" data-testid={`authenticity-badge-${rank}`}>
            <Badge className={`${config.color} px-4 py-2 text-sm font-medium flex items-center gap-2`}>
                <Icon className="h-4 w-4" />
                {config.label}: {classification}
            </Badge>
        </div>
    );
};