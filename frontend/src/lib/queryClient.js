import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10 * 60 * 1000, // 10 minutes
      gcTime: 30 * 60 * 1000,    // 30 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export { queryClient, QueryClientProvider };
