import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

export const SearchBar = ({ className = '' }) => {
    const [searchQuery, setSearchQuery] = useState('');
    const navigate = useNavigate();

    const handleSearch = (e) => {
        e.preventDefault();
        if (searchQuery.trim()) {
            navigate(`/recipes?search=${encodeURIComponent(searchQuery)}`);
        }
    };

    return (
        <form onSubmit={handleSearch} className={`flex gap-2 ${className}`} data-testid="search-form">
            <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-[#1E1E1E]/40" />
                <Input
                    type="text"
                    placeholder="Search authentic recipes..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 bg-white border-[#E5DCC3] focus:border-[#CBA55B] rounded-none h-12"
                    data-testid="search-input"
                />
            </div>
            <Button
                type="submit"
                className="bg-[#6A1F2E] hover:bg-[#8B2840] text-white rounded-none h-12 px-8"
                data-testid="search-button"
            >
                Search
            </Button>
        </form>
    );
};