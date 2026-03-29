import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X } from 'lucide-react';

interface FileUploadZoneProps {
  onUpload: (files: File[]) => void;
  files?: File[];
  onRemove?: (index: number) => void;
}

const FileUploadZone: React.FC<FileUploadZoneProps> = ({ onUpload, files = [], onRemove }) => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    onUpload(acceptedFiles);
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxSize: 10 * 1024 * 1024,
    maxFiles: 5,
  });

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-all ${
          isDragActive ? 'border-cyan-500 bg-cyan-50' : 'border-slate-300 hover:border-cyan-400/60 bg-slate-50/50'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="w-6 h-6 text-slate-400 mx-auto mb-2" />
        <p className="text-sm text-slate-600">
          {isDragActive ? 'Drop files here...' : 'Drag & drop PDFs or click to upload'}
        </p>
        <p className="text-xs text-slate-400 mt-1">Max 10MB per file</p>
      </div>

      {files.length > 0 && (
        <div className="space-y-1">
          {files.map((file, i) => (
            <div key={i} className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg shadow-sm">
              <FileText className="w-4 h-4 text-cyan-600" />
              <span className="text-sm text-slate-700 flex-1 truncate">{file.name}</span>
              <span className="text-xs text-slate-400">{(file.size / 1024).toFixed(0)}KB</span>
              {onRemove && (
                <button type="button" onClick={() => onRemove(i)} className="text-slate-400 hover:text-red-600"><X className="w-3.5 h-3.5" /></button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUploadZone;
