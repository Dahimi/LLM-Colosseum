import { useEffect, useState, useRef } from 'react';

interface UseEventSourceOptions<T> {
  onMessage?: (data: T) => void;
  onError?: (error: Event) => void;
  enabled?: boolean;
  maxRetries?: number;
  initialRetryDelay?: number;
  transformer?: (data: any) => T;
}

export function useEventSource<T>(url: string, options: UseEventSourceOptions<T> = {}) {
  const {
    onMessage,
    onError,
    enabled = true,
    maxRetries = 5,
    initialRetryDelay = 1000,
    transformer = (data) => data as T,
  } = options;

  const [error, setError] = useState<Event | null>(null);
  const retryCount = useRef(0);
  const retryTimeout = useRef<NodeJS.Timeout>();
  const eventSourceRef = useRef<EventSource>();

  const connect = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      const eventSource = new EventSource(url, { withCredentials: true });
      eventSourceRef.current = eventSource;

      eventSource.onmessage = (event) => {
        try {
          const rawData = JSON.parse(event.data);
          const data = transformer(rawData);
          onMessage?.(data);
          // Reset retry count on successful message
          retryCount.current = 0;
        } catch (err) {
          console.error('Error parsing SSE data:', err);
        }
      };

      eventSource.onerror = (event) => {
        console.error('SSE connection error:', event);
        eventSource.close();
        setError(event);
        onError?.(event);

        // Implement exponential backoff for retries
        if (retryCount.current < maxRetries) {
          const delay = Math.min(
            initialRetryDelay * Math.pow(2, retryCount.current),
            30000 // Max delay of 30 seconds
          );
          console.log(`Retrying connection in ${delay}ms (attempt ${retryCount.current + 1}/${maxRetries})`);
          
          retryTimeout.current = setTimeout(() => {
            retryCount.current++;
            connect();
          }, delay);
        } else {
          console.error('Max retry attempts reached');
        }
      };

      eventSource.onopen = () => {
        console.log('SSE connection established');
        setError(null);
      };
    } catch (err) {
      console.error('Error creating EventSource:', err);
    }
  };

  useEffect(() => {
    if (!enabled) return;

    connect();

    return () => {
      if (retryTimeout.current) {
        clearTimeout(retryTimeout.current);
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [url, enabled]);

  return { error };
} 