'use client'

import { useState, useRef, DragEvent, ChangeEvent, forwardRef } from "react";
import { FileImage, FileText, Paperclip, X } from "lucide-react";

const SUPPORTED_SOURCE_TYPES = new Set([
  'application/pdf',
  'image/jpeg',
  'image/png',
  'image/webp',
]);
const SUPPORTED_SOURCE_EXTENSION = /\.(?:pdf|png|jpe?g|webp)$/i;

function isImageFile(file: File) {
  return (
    (SUPPORTED_SOURCE_TYPES.has(file.type) && file.type !== 'application/pdf')
    || /\.(?:png|jpe?g|webp)$/i.test(file.name)
  );
}

export interface TextareaProps extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, 'value' | 'maxLength'> {
  files?: File[];
  onFilesChange?: (files: File[]) => void;
  value: string;
  maxLength: number;
  fileUploadDisabled?: boolean;
  generationButton: React.ReactNode;
  containerClassName?: string;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className = "", containerClassName = "", files = [], onFilesChange, value, maxLength, fileUploadDisabled = false, generationButton, ...props }, ref) => {
    const [isDragActive, setIsDragActive] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleFiles = (newFiles: File[]) => {
      if (fileUploadDisabled) return;
      const sourceFiles = newFiles.filter((file) => (
        SUPPORTED_SOURCE_TYPES.has(file.type) || SUPPORTED_SOURCE_EXTENSION.test(file.name)
      ));
      if (sourceFiles.length) {
        onFilesChange?.([...files, ...sourceFiles]);
      }
    };

    const handleDrag = (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (e.type === "dragenter" || e.type === "dragover") {
        setIsDragActive(true);
      } else if (e.type === "dragleave") {
        setIsDragActive(false);
      }
    };

    const handleDrop = (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFiles(Array.from(e.dataTransfer.files));
      }
    };

    const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
      e.preventDefault();
      if (e.target.files && e.target.files[0]) {
        handleFiles(Array.from(e.target.files));
        e.target.value = "";
      }
    };

    const onButtonClick = () => {
      inputRef.current?.click();
    };

    const removeFile = (index: number) => {
      onFilesChange?.(files.filter((_, i) => i !== index));
    };

    return (
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`
          relative flex flex-col w-full rounded-xl border px-4 py-3
          focus-within:ring-2 focus-within:ring-accent focus-within:border-transparent
          transition-all duration-200
          ${isDragActive ? "border-accent bg-accent/20" : "border-surface bg-secondary-bg"}
          ${containerClassName}
        `}
      >
        <textarea
          ref={ref}
          className={`min-h-20 resize-none bg-transparent text-sm text-primary-text placeholder:text-secondary-text focus:outline-none ${className}`}
          value={value}
          maxLength={maxLength}
          {...props}
        />
        {/* -mb/-mr cancel the icon buttons' hit-area padding so glyphs sit on the container's px-4/py-3 inset */}
        <div className="flex justify-between items-end mt-2 -mb-1.5">
          <div className="flex items-center gap-4 pb-1.5">
            <p className="pointer-events-none text-xs text-secondary-text">
              {value.length}/{maxLength}
            </p>
            <div className="flex gap-2 flex-wrap">
              {files.map((file, i) => (
                <div key={`${file.name}-${i}`} className="flex max-w-48 items-center gap-2 rounded-md bg-surface px-2 py-1 text-xs">
                  {isImageFile(file) ? <FileImage className="shrink-0 text-accent" size={14} /> : <FileText className="shrink-0 text-accent" size={14} />}
                  <span className="truncate" title={file.name}>{file.name}</span>
                  <button type="button" onClick={() => removeFile(i)} className="shrink-0 text-secondary-text hover:text-primary-text" title={`Remove ${file.name}`}>
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2 -mr-1.5">
            <input
              ref={inputRef}
              type="file"
              multiple
              accept="application/pdf,image/png,image/jpeg,image/webp,.pdf,.png,.jpg,.jpeg,.webp"
              className="hidden"
              onChange={handleChange}
            />
            <button
              type="button"
              onClick={onButtonClick}
              disabled={fileUploadDisabled}
              className="p-1.5 hover:bg-surface/50 rounded-lg text-accent transition-colors disabled:opacity-40"
              title="Attach PDF or image"
            >
              <Paperclip size={20} />
            </button>
            {generationButton}
          </div>
        </div>
      </div>
    );
  }
);

Textarea.displayName = "Textarea";

export default Textarea;
