/**
 * Utility functions for Kurtosis
 */

// Truncate addresses for display
export const shortKey = (key?: string) => {
  if (!key) return '???';
  const str = key?.toString();
  return `${str.substring(0, 4)}...${str.substring(str.length - 5, str.length)}`;
};

// Truncate transaction hashes
export const shortSignature = (sig?: string, length: number = 8) => {
  if (!sig) return '???';
  return `${sig.substring(0, length)}...`;
};

// Debounce function for search/input
export function debounce<T extends any[]>(
  callback: (...args: T) => Promise<void>,
  delay: number,
): (...args: T) => Promise<void> {
  let timerId: NodeJS.Timeout;
  return async (...args: T) => {
    if (timerId) {
      clearTimeout(timerId);
    }
    timerId = setTimeout(() => {
      callback(...args);
    }, delay);
  };
}

// Get decimal count of a number
export const getDecimalCount = (value: number) => {
  if (!value) {
    return 0;
  }
  let splitString = value.toString().split('.');
  if (splitString.length === 1) {
    splitString = value.toString().split('e-');
    return Number(splitString[1]);
  }
  if (splitString.length > 1) {
    return splitString[1].length;
  }
  return 0;
};

// Convert to scientific notation
export const toScientificNotation = (number: number, decimalPlaces: number) =>
  number.toExponential(decimalPlaces);

// Format large numbers (123,000,000 becomes 123M)
export const toCompactNumber = (number: any) => {
  const value = Number(number);
  if (Number.isNaN(value)) return Number(0.0);
  return new Intl.NumberFormat('en', { notation: 'compact', maximumSignificantDigits: 4 }).format(value);
};

// Format currency
export const formatCurrency = (value: number, decimals: number = 2): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

// Format percentage
export const formatPercentage = (value: number, decimals: number = 2): string => {
  return `${(value * 100).toFixed(decimals)}%`;
};

// Convert timestamp to readable date
export const formatDate = (timestamp: number): string => {
  return new Date(timestamp * 1000).toLocaleString();
};

// Calculate time remaining
export const timeRemaining = (deadline: number): string => {
  const now = Date.now() / 1000;
  const remaining = deadline - now;
  
  if (remaining <= 0) return 'Ended';
  
  const days = Math.floor(remaining / 86400);
  const hours = Math.floor((remaining % 86400) / 3600);
  const minutes = Math.floor((remaining % 3600) / 60);
  
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
};

// Validate Ethereum address
export const isValidAddress = (address: string): boolean => {
  return /^0x[a-fA-F0-9]{40}$/.test(address);
};