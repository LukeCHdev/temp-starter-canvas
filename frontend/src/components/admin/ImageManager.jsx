import React, { useState, useCallback, useRef } from 'react';
import { Upload, X, RotateCw, RotateCcw, ZoomIn, ZoomOut, Crop, Trash2, Image as ImageIcon, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || import.meta?.env?.VITE_BACKEND_URL || '';

/**
 * ImageManager Component
 * Provides image upload, preview, and basic editing for recipes and techniques
 * 
 * Props:
 * - currentImageUrl: string - URL of the current image
 * - onImageChange: function(imageUrl) - Called when image is uploaded/changed
 * - onImageRemove: function() - Called when image is removed
 * - entityType: 'recipe' | 'technique' - Type of entity for upload endpoint
 * - entitySlug: string - Slug of the entity (for updating existing)
 * - authHeaders: object - Auth headers for API calls
 */
export const ImageManager = ({ 
    currentImageUrl, 
    onImageChange, 
    onImageRemove,
    entityType = 'recipe',
    entitySlug = null,
    authHeaders = {}
}) => {
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [previewUrl, setPreviewUrl] = useState(currentImageUrl || null);
    const [editMode, setEditMode] = useState(false);
    const [rotation, setRotation] = useState(0);
    const [scale, setScale] = useState(100);
    const [selectedFile, setSelectedFile] = useState(null);
    const fileInputRef = useRef(null);
    const canvasRef = useRef(null);

    // Handle drag events
    const handleDragEnter = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        
        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            handleFileSelect(files[0]);
        }
    }, []);

    const handleFileSelect = (file) => {
        if (!file) return;

        // Validate file type
        const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
        if (!validTypes.includes(file.type)) {
            toast.error('Please select a valid image file (JPEG, PNG, WebP, or GIF)');
            return;
        }

        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            toast.error('Image must be less than 10MB');
            return;
        }

        setSelectedFile(file);
        
        // Create preview URL
        const reader = new FileReader();
        reader.onload = (e) => {
            setPreviewUrl(e.target.result);
            setEditMode(true);
            setRotation(0);
            setScale(100);
        };
        reader.readAsDataURL(file);
    };

    const handleFileInputChange = (e) => {
        const file = e.target.files?.[0];
        if (file) {
            handleFileSelect(file);
        }
    };

    // Apply transformations and get final image
    const applyTransformations = useCallback(() => {
        return new Promise((resolve) => {
            if (!previewUrl) {
                resolve(null);
                return;
            }

            const img = new Image();
            img.crossOrigin = 'anonymous';
            img.onload = () => {
                const canvas = canvasRef.current || document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                // Calculate scaled dimensions
                const scaleFactor = scale / 100;
                const scaledWidth = img.width * scaleFactor;
                const scaledHeight = img.height * scaleFactor;
                
                // Handle rotation
                const isRotated = rotation % 180 !== 0;
                canvas.width = isRotated ? scaledHeight : scaledWidth;
                canvas.height = isRotated ? scaledWidth : scaledHeight;
                
                // Clear and transform
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.save();
                ctx.translate(canvas.width / 2, canvas.height / 2);
                ctx.rotate((rotation * Math.PI) / 180);
                ctx.drawImage(img, -scaledWidth / 2, -scaledHeight / 2, scaledWidth, scaledHeight);
                ctx.restore();
                
                canvas.toBlob((blob) => {
                    resolve(blob);
                }, 'image/jpeg', 0.9);
            };
            img.src = previewUrl;
        });
    }, [previewUrl, rotation, scale]);

    // Upload image to server
    const uploadImage = async () => {
        setIsUploading(true);
        setUploadProgress(0);

        try {
            let imageBlob;
            
            if (editMode && (rotation !== 0 || scale !== 100)) {
                // Apply transformations
                imageBlob = await applyTransformations();
            } else if (selectedFile) {
                imageBlob = selectedFile;
            } else {
                toast.error('No image to upload');
                setIsUploading(false);
                return;
            }

            const formData = new FormData();
            formData.append('image', imageBlob, selectedFile?.name || 'image.jpg');
            if (entitySlug) {
                formData.append('slug', entitySlug);
            }

            const endpoint = entityType === 'technique' 
                ? `${API_URL}/api/admin/techniques/upload-image`
                : `${API_URL}/api/admin/recipes/upload-image`;

            const response = await axios.post(endpoint, formData, {
                headers: {
                    ...authHeaders,
                    'Content-Type': 'multipart/form-data'
                },
                onUploadProgress: (progressEvent) => {
                    const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                    setUploadProgress(progress);
                }
            });

            if (response.data.image_url) {
                setPreviewUrl(response.data.image_url);
                setEditMode(false);
                setSelectedFile(null);
                onImageChange?.(response.data.image_url);
                toast.success('Image uploaded successfully!');
            }
        } catch (error) {
            console.error('Upload error:', error);
            toast.error(error.response?.data?.detail || 'Failed to upload image');
        } finally {
            setIsUploading(false);
            setUploadProgress(0);
        }
    };

    // Remove image
    const removeImage = () => {
        if (window.confirm('Are you sure you want to remove this image?')) {
            setPreviewUrl(null);
            setSelectedFile(null);
            setEditMode(false);
            setRotation(0);
            setScale(100);
            onImageRemove?.();
            toast.success('Image removed');
        }
    };

    // Cancel editing
    const cancelEdit = () => {
        setPreviewUrl(currentImageUrl || null);
        setSelectedFile(null);
        setEditMode(false);
        setRotation(0);
        setScale(100);
    };

    return (
        <Card className="w-full">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <ImageIcon className="w-5 h-5" />
                    Image Manager
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Drop Zone / Preview */}
                <div
                    className={`relative border-2 border-dashed rounded-lg transition-colors ${
                        isDragging 
                            ? 'border-amber-500 bg-amber-50' 
                            : 'border-gray-300 hover:border-gray-400'
                    } ${previewUrl ? 'p-2' : 'p-8'}`}
                    onDragEnter={handleDragEnter}
                    onDragLeave={handleDragLeave}
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
                >
                    {previewUrl ? (
                        <div className="relative">
                            <img
                                src={previewUrl}
                                alt="Preview"
                                className="w-full h-auto max-h-80 object-contain rounded-lg"
                                style={{
                                    transform: `rotate(${rotation}deg) scale(${scale / 100})`,
                                    transition: 'transform 0.3s ease'
                                }}
                            />
                            {/* Remove button */}
                            <Button
                                variant="destructive"
                                size="icon"
                                className="absolute top-2 right-2"
                                onClick={removeImage}
                            >
                                <X className="w-4 h-4" />
                            </Button>
                        </div>
                    ) : (
                        <div className="text-center">
                            <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                            <p className="text-gray-600 mb-2">
                                Drag & drop an image here, or click to select
                            </p>
                            <p className="text-sm text-gray-400">
                                Supports: JPEG, PNG, WebP, GIF (max 10MB)
                            </p>
                            <Button
                                variant="outline"
                                className="mt-4"
                                onClick={() => fileInputRef.current?.click()}
                            >
                                Select Image
                            </Button>
                        </div>
                    )}
                </div>

                {/* Hidden file input */}
                <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp,image/gif"
                    className="hidden"
                    onChange={handleFileInputChange}
                />

                {/* Edit Controls (shown when image is selected) */}
                {previewUrl && (
                    <div className="space-y-4 pt-4 border-t">
                        <div className="flex flex-wrap gap-2">
                            {/* Replace button */}
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <Upload className="w-4 h-4 mr-2" /> Replace
                            </Button>
                            
                            {/* Rotation buttons */}
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setRotation((r) => r - 90)}
                            >
                                <RotateCcw className="w-4 h-4" />
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setRotation((r) => r + 90)}
                            >
                                <RotateCw className="w-4 h-4" />
                            </Button>
                            
                            {/* Remove button */}
                            <Button
                                variant="outline"
                                size="sm"
                                className="text-red-600 hover:text-red-700"
                                onClick={removeImage}
                            >
                                <Trash2 className="w-4 h-4 mr-2" /> Remove
                            </Button>
                        </div>

                        {/* Scale slider */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-600">Scale: {scale}%</span>
                                <div className="flex gap-2">
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => setScale((s) => Math.max(25, s - 10))}
                                    >
                                        <ZoomOut className="w-4 h-4" />
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => setScale((s) => Math.min(200, s + 10))}
                                    >
                                        <ZoomIn className="w-4 h-4" />
                                    </Button>
                                </div>
                            </div>
                            <Slider
                                value={[scale]}
                                onValueChange={([val]) => setScale(val)}
                                min={25}
                                max={200}
                                step={5}
                                className="w-full"
                            />
                        </div>

                        {/* Action buttons */}
                        <div className="flex gap-2 pt-2">
                            {editMode && (
                                <Button
                                    variant="outline"
                                    onClick={cancelEdit}
                                    disabled={isUploading}
                                >
                                    Cancel
                                </Button>
                            )}
                            <Button
                                className="bg-amber-700 hover:bg-amber-800"
                                onClick={uploadImage}
                                disabled={isUploading || !selectedFile}
                            >
                                {isUploading ? (
                                    <>
                                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                        Uploading... {uploadProgress}%
                                    </>
                                ) : (
                                    <>
                                        <Upload className="w-4 h-4 mr-2" />
                                        Save Image
                                    </>
                                )}
                            </Button>
                        </div>

                        {/* Upload progress bar */}
                        {isUploading && (
                            <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                    className="bg-amber-600 h-2 rounded-full transition-all duration-300"
                                    style={{ width: `${uploadProgress}%` }}
                                />
                            </div>
                        )}
                    </div>
                )}

                {/* Hidden canvas for transformations */}
                <canvas ref={canvasRef} className="hidden" />
            </CardContent>
        </Card>
    );
};

export default ImageManager;
