import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

export const IngredientTable = ({ ingredients, unitSystem = 'metric' }) => {
    return (
        <div className="overflow-x-auto" data-testid="ingredient-table">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead className="w-1/2">Ingredient</TableHead>
                        <TableHead>Amount</TableHead>
                        <TableHead>Notes</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {ingredients.map((ingredient, index) => (
                        <TableRow key={index}>
                            <TableCell className="font-medium">{ingredient.item}</TableCell>
                            <TableCell>
                                {unitSystem === 'imperial' ? ingredient.unit_imperial : ingredient.unit_metric}
                            </TableCell>
                            <TableCell className="text-sm text-[#1E1E1E]/70">{ingredient.notes || '-'}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
};