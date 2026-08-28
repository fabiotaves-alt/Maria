export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface ResourceMetric {
  label: string;
  value: number;
  color?: string;
}

export interface NavItem {
  id: string;
  label: string;
  icon: string;
  active?: boolean;
}

export type Theme = 'light' | 'dark';

export interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}
