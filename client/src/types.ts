export type Integrator = 'together' | 'openai';

export interface SettingsContextType {
    articleUrl: string;
    setArticleUrl: (url: string) => void;
    articleTitle: string;
    setArticleTitle: (title: string) => void;
    integrator: Integrator;
    setIntegrator: (integrator: Integrator) => void;
    userQuery: string;
    setUserQuery: (query: string) => void;
    model: string;
    setModel: (model: string) => void;
    chunkSize: string;
    setChunkSize: (chunk: string) => void;
  }

export type Message = {
    role: "user" | "assistant" | "tool" | "system";
    content: string;
  };
  
export type ConversationCard = {
    user: Message;
    assistant: Message;
  };

interface Option {
    label: string;
    value: string;
    disabled?: boolean;
  }
  
export interface SelectListProps<T extends string> {
    options: Option[];
    selectedValue: T;
    onChange: ((value: T) => void) | undefined;
    placeholder?: string;
    disabled?: boolean;
    className?: string;
  }