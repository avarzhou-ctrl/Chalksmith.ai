'use client'

import { useState, useRef, DragEvent, ChangeEvent, forwardRef } from "react";
import { Paperclip, X } from "lucide-react";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  topic: string;
  format: string;
  files?: File[];
  onFilesChange?: (files: File[]) => void;
  value: string;
  maxLength: number;
  generationButton: React.ReactNode;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className = "", topic, format, files = [], onFilesChange, value, maxLength, generationButton, ...props }, ref) => {
    const [isDragActive, setIsDragActive] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleFiles = (newFiles: File[]) => {
      const pdfFiles = newFiles.filter((file) => file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf"));
      if (pdfFiles.length) {
        onFilesChange?.([...files, ...pdfFiles]);
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
        `}
      >
        <textarea
          ref={ref}
          className="bg-transparent h-20 focus:outline-none resize-none text-sm text-primary-text placeholder:text-secondary-text"
          value={value}
          maxLength={maxLength}
          {...props}
        />
        <div className="flex justify-between items-center mt-2">
          <div className="flex items-center gap-4">
            <p className="pointer-events-none text-xs text-secondary-text">
              {value.length}/{maxLength}
            </p>
            <div className="flex gap-2 flex-wrap">
              {files.map((file, i) => (
                <div key={i} className="flex items-center gap-2 bg-surface px-2 py-1 rounded-md text-xs">
                  <span>{file.name}</span>
                  <button type="button" onClick={() => removeFile(i)} className="text-secondary-text hover:text-primary-text">
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              ref={inputRef}
              type="file"
              multiple
              accept="application/pdf,.pdf"
              className="hidden"
              onChange={handleChange}
            />
            <button
              type="button"
              onClick={onButtonClick}
              disabled={!topic.trim() || !format}
              className="p-1.5 hover:bg-surface/50 rounded-lg text-accent transition-colors disabled:opacity-40"
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
