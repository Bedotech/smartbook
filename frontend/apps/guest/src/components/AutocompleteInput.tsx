import { useState, useRef, useEffect } from 'react'
import { Input } from '@smartbook/ui'
import { Loader2, ChevronDown } from 'lucide-react'

interface AutocompleteOption {
  value: string
  label: string
  subtitle?: string
}

interface AutocompleteInputProps {
  label: string
  value: string
  onChange: (value: string, option?: AutocompleteOption) => void
  options: AutocompleteOption[]
  loading?: boolean
  error?: string
  required?: boolean
  placeholder?: string
  helperText?: string
}

export function AutocompleteInput({
  label,
  value,
  onChange,
  options,
  loading = false,
  error,
  required,
  placeholder,
  helperText,
}: AutocompleteInputProps) {
  const [showDropdown, setShowDropdown] = useState(false)
  const [inputValue, setInputValue] = useState(value)
  const containerRef = useRef<HTMLDivElement>(null)

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)
    onChange(newValue)
    setShowDropdown(true)
  }

  const handleSelectOption = (option: AutocompleteOption) => {
    setInputValue(option.label)
    onChange(option.value, option)
    setShowDropdown(false)
  }

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Input
          label={label}
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => setShowDropdown(true)}
          error={error}
          required={required}
          placeholder={placeholder}
          helperText={helperText}
        />
        <div className="absolute right-3 top-9 pointer-events-none">
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </div>

      {showDropdown && options.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-auto">
          {options.map((option, index) => (
            <button
              key={`${option.value}-${index}`}
              type="button"
              className="w-full px-4 py-3 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none touch-target transition-colors first:rounded-t-lg last:rounded-b-lg"
              onClick={() => handleSelectOption(option)}
            >
              <div className="font-medium text-sm text-gray-900">{option.label}</div>
              {option.subtitle && (
                <div className="text-xs text-gray-500 mt-0.5">{option.subtitle}</div>
              )}
            </button>
          ))}
        </div>
      )}

      {showDropdown && !loading && options.length === 0 && inputValue.length >= 2 && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg p-3">
          <p className="text-sm text-gray-500">No results found</p>
        </div>
      )}
    </div>
  )
}
