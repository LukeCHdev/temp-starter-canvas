import React from 'react';
import { Clock, Thermometer } from 'lucide-react';

export const InstructionSteps = ({ steps, tempSystem = 'C' }) => {
    return (
        <div className="space-y-6" data-testid="instruction-steps">
            {steps.map((step, index) => (
                <div key={index} className="flex gap-4" data-testid={`step-${step.step_number}`}>
                    {/* Step number */}
                    <div className="flex-shrink-0">
                        <div className="w-10 h-10 rounded-full bg-[#6A1F2E] text-white flex items-center justify-center font-semibold">
                            {step.step_number}
                        </div>
                    </div>
                    
                    {/* Step content */}
                    <div className="flex-1">
                        <p className="narrative-text mb-2">{step.instruction}</p>
                        
                        <div className="flex flex-wrap gap-4 text-sm text-[#1E1E1E]/60">
                            {step.timing && (
                                <div className="flex items-center gap-1">
                                    <Clock className="h-4 w-4" />
                                    <span>{step.timing}</span>
                                </div>
                            )}
                            {step.temperature && (
                                <div className="flex items-center gap-1">
                                    <Thermometer className="h-4 w-4" />
                                    <span>
                                        {tempSystem === 'F' 
                                            ? `${step.temperature.fahrenheit}°F` 
                                            : `${step.temperature.celsius}°C`}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
};