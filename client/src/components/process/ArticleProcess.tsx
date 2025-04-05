import React, { useState, useEffect, useMemo } from 'react';
import { z } from 'zod';
import { createServerFn } from '@tanstack/react-start';
import { Input } from '~/components/input';
import { Button } from '~/components/button';
import { Loader2, Cog } from 'lucide-react';
import { baseUrl, chunkSizeOptions, integratorKey, integratorOptions, modelMapper } from '~/config';
import SelectList from '../selectList';
import { useSettings } from '~/contexts/SettingsContext';
import { useQuery } from '@tanstack/react-query';
import { fetchIntegratorData } from '~/services/fetchers';
import { extractErrorMessage } from '~/utils/errorMessageExtractor';

const processArticleSchema = z.object({
    url: z.string({ required_error: 'url is required' }).url("Please enter a valid URL"),
    integrator: z.enum(['together', 'openai'], {
      required_error: 'integrator is required',
    }),
    chunk_size: z.string().optional()
  });

const processArticle = createServerFn({ method: 'POST' })
  .validator((data: z.infer<typeof processArticleSchema>) => {
    return processArticleSchema.parse(data);
  })
  .handler(async ({ data }) => {
    const response = await fetch(`${baseUrl}/api/process-article`, {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorResponse = await response.json();
      console.log('errorResponse', errorResponse)
      throw new Error(errorResponse.error || 'Failed to process article');
    }

    const result = await response.json();
    return result;
});

const ArticleProcess: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [articleImageUrl, setArticleImageUrl] = useState<string | null>(null);
    const { 
        setArticleUrl, 
        articleUrl, 
        setArticleTitle,
        articleTitle,
        setIntegrator, 
        integrator,
        setModel,
        model,
        setChunkSize,
        chunkSize 
    } = useSettings();

    const { data } = useQuery({
        queryKey: [integratorKey],
        queryFn: fetchIntegratorData,
      });

      const availableOptions = useMemo(
        () => integratorOptions.filter(option => data?.[option.value]),
        [data]
      );

    useEffect(() => {
        if (availableOptions.length === 1) {
            setIntegrator(availableOptions[0].value as any)
        }
    }, [availableOptions, setIntegrator])

    useEffect(() => {
        if (error) {
          const timer = setTimeout(() => {
            setError("");
          }, 8000);
          return () => clearTimeout(timer);
        }
      }, [error]);

    const startProcessing = async () => {
      setLoading(true);
      try {
        const data = await processArticle({ data: { url: articleUrl, integrator, chunk_size: chunkSize } });
        setArticleTitle(data.articleTitle);
        setArticleImageUrl(`${baseUrl}/api/article-image?ts=${Date.now()}`);
      } catch (error: any) {
        setError(extractErrorMessage(error));
      } finally {
        setLoading(false);
      }
    };

    const handleIntegratorChange = async (newIntegrator: 'openai' | 'together') => {
        setIntegrator(newIntegrator);
      
        try {
          const response = await fetch(`${baseUrl}/api/clear-cache`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ integrator })
          });
          const data = await response.json();
          console.log("Cache cleared:", data);
        } catch (error) {
          console.error("Error clearing cache:", error);
        }
      };
  
    return (
      <div className="w-1/4 p-4 bg-gray-700 flex flex-col h-screen">
        <div className="flex-grow space-y-4">
        <div className={`${!!articleUrl ? "pointer-events-none opacity-50" : ""}`}>
          <h3 className="text-md font-medium">Integrator</h3>
          <SelectList
            options={availableOptions}
            selectedValue={integrator}
            disabled={!!articleUrl}
            onChange={handleIntegratorChange}
            placeholder="Select integrator"
          />
        </div>
        
        <div>
          <h3 className="text-md font-medium">Add an article</h3>
          <Input
            className="w-full bg-zinc-900 border-gray-700 text-gray-100"
            value={articleUrl}
            disabled={loading}
            placeholder="Place your URL here..."
            onChange={(e) => setArticleUrl(e.target.value)}
          />
        </div>

        <div>
          <h3 className="text-md font-medium">Chunk size <span className="text-sm font-small">(optional)</span></h3>
          <SelectList
            options={chunkSizeOptions}
            selectedValue={chunkSize}
            disabled={loading || !articleUrl}
            onChange={setChunkSize}
            placeholder="Select chunk size"
          />
        </div>
        
        <div>
          <Button
            onClick={startProcessing}
            disabled={loading || !articleUrl}
            className="w-full bg-primary/80 hover:bg-primary/100"
            variant="default"
            size="default"
          >
            {loading ? (
              <>
                <span>Analyzing...</span>
                <Loader2 className="h-4 w-4 animate-spin" />
              </>
            ) : (
              <>
                <span>Analyze</span>
                <Cog className="h-4 w-4" />
              </>
            )}
            <span className="sr-only">Process Url</span>
          </Button>
          {error && <p className="mt-4 text-sm text-red-300">{error}</p>}
        </div>
        
        {articleImageUrl && (
          <img 
            src={articleImageUrl} 
            alt="Scraped Article" 
            className="mt-4 shadow-md border border-gray-400 rounded"
            style={{ maxWidth: '100%' }} 
          />
        )}
        
        <p className="mt-4">{articleTitle}</p>
        </div>
        <div className="mt-auto">
          <h3 className="text-md font-medium">Choose model</h3>
          <SelectList
            className="py-2"
            options={modelMapper[integrator]}
            selectedValue={model}
            disabled={!articleUrl}
            onChange={setModel}
            placeholder="Select model"
          />
        </div>
      </div>
    );
  };
  
export default ArticleProcess;