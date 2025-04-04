import { createContext, PropsWithChildren, useContext, useMemo, useState } from 'react';
import { Integrator, SettingsContextType } from '~/types';

const SettingsContext = createContext({} as SettingsContextType);

export const SettingsProvider = ({ children }: PropsWithChildren) => {
  const [articleUrl, setArticleUrl] = useState('');
  const [articleTitle, setArticleTitle] = useState('');
  const [integrator, setIntegrator] = useState<Integrator>('openai');
  const [chunkSize, setChunkSize] = useState('');
  const [userQuery, setUserQuery] = useState('');
  const [model, setModel] = useState('');

  const value = useMemo(() => ({ 
    articleUrl, 
    setArticleUrl,
    articleTitle,
    setArticleTitle,
    integrator, 
    setIntegrator, 
    userQuery, 
    setUserQuery, 
    model, 
    setModel, 
    chunkSize, 
    setChunkSize 
    }), [articleUrl, articleTitle, integrator, userQuery, model, chunkSize])

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => {
  return useContext(SettingsContext);
};
