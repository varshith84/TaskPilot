import React, { useRef, useState } from 'react'
import { UploadCloud, Loader2 } from 'lucide-react'

interface DocumentUploaderProps {
  onUpload: (file: File) => Promise<void>
}

export function DocumentUploader({ onUpload }: DocumentUploaderProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true)
    } else if (e.type === 'dragleave') {
      setIsDragging(false)
    }
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    
    const files = e.dataTransfer.files
    if (files && files[0]) {
      await processUpload(files[0])
    }
  }

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files[0]) {
      await processUpload(files[0])
    }
    // reset
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const processUpload = async (file: File) => {
    setIsUploading(true)
    try {
      await onUpload(file)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div 
      className={`uploader-dropzone ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => !isUploading && fileInputRef.current?.click()}
    >
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleChange}
        style={{ display: 'none' }}
        accept=".pdf,.txt,.md,.docx"
      />
      {isUploading ? (
        <div className="uploader-content">
          <Loader2 className="spinner" size={24} />
          <span>Uploading...</span>
        </div>
      ) : (
        <div className="uploader-content">
          <UploadCloud size={24} />
          <span>Drop file or click to upload</span>
          <small>PDF, TXT, MD, DOCX</small>
        </div>
      )}
    </div>
  )
}
