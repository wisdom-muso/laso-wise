import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check } from 'lucide-react';
import { cn } from '../../lib/utils';

interface SelectProps {
  value: string;
  onValueChange: (value: string) => void;
  children: React.ReactNode;
}

interface SelectTriggerProps {
  children: React.ReactNode;
  className?: string;
}

interface SelectContentProps {
  children: React.ReactNode;
  className?: string;
}

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

interface SelectValueProps {
  placeholder?: string;
  className?: string;
}

const SelectContext = React.createContext<{
  value: string;
  onValueChange: (value: string) => void;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
} | null>(null);

export const Select: React.FC<SelectProps> = ({ value, onValueChange, children }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <SelectContext.Provider value={{ value, onValueChange, isOpen, setIsOpen }}>
      <div className="relative">
        {children}
      </div>
    </SelectContext.Provider>
  );
};

export const SelectTrigger: React.FC<SelectTriggerProps> = ({ children, className }) => {
  const context = React.useContext(SelectContext);
  if (!context) throw new Error('SelectTrigger must be used within Select');

  const { isOpen, setIsOpen } = context;

  return (
    <button
      type="button"
      onClick={() => setIsOpen(!isOpen)}
      className={cn(
        "flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
    >
      {children}
      <ChevronDown className={cn("h-4 w-4 opacity-50 transition-transform", isOpen && "rotate-180")} />
    </button>
  );
};

export const SelectValue: React.FC<SelectValueProps> = ({ placeholder, className }) => {
  const context = React.useContext(SelectContext);
  if (!context) throw new Error('SelectValue must be used within Select');

  const { value } = context;

  return (
    <span className={cn("truncate", className)}>
      {value || placeholder}
    </span>
  );
};

export const SelectContent: React.FC<SelectContentProps> = ({ children, className }) => {
  const context = React.useContext(SelectContext);
  if (!context) throw new Error('SelectContent must be used within Select');

  const { isOpen, setIsOpen } = context;
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (contentRef.current && !contentRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, setIsOpen]);

  if (!isOpen) return null;

  return (
    <div
      ref={contentRef}
      className={cn(
        "absolute top-full z-50 mt-1 max-h-60 w-full overflow-auto rounded-md border bg-popover p-1 text-popover-foreground shadow-md",
        className
      )}
    >
      {children}
    </div>
  );
};

export const SelectItem: React.FC<SelectItemProps> = ({ value, children, className }) => {
  const context = React.useContext(SelectContext);
  if (!context) throw new Error('SelectItem must be used within Select');

  const { value: selectedValue, onValueChange, setIsOpen } = context;
  const isSelected = selectedValue === value;

  const handleSelect = () => {
    onValueChange(value);
    setIsOpen(false);
  };

  return (
    <div
      onClick={handleSelect}
      className={cn(
        "relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
        className
      )}
    >
      {isSelected && (
        <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
          <Check className="h-4 w-4" />
        </span>
      )}
      {children}
    </div>
  );
};