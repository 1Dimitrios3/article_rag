import { createFileRoute } from '@tanstack/react-router'
import { QueryClient, dehydrate } from '@tanstack/react-query';
import { AIChat } from '~/components/chat/AiChat';
import ArticleProcess from '~/components/process/ArticleProcess';
import { integratorKey } from '~/config';
import { fetchIntegratorData } from '~/services/fetchers';

const queryClient = new QueryClient();

export const Route = createFileRoute('/')({
  component: Home,
  loader: async () => {
    await queryClient.prefetchQuery({
      queryKey: [integratorKey],
      queryFn: fetchIntegratorData,
    });
    return {
      dehydratedState: dehydrate(queryClient),
    };
  },
});

function Home() {

  return (
  <div className="flex h-screen">
    {/* Left Side Panel */}
    <ArticleProcess />
    {/* Main Panel */}
    <div className="w-3/4 h-full">
      <AIChat />
    </div>
  </div>
  )
}
