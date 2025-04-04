import { baseUrl } from "~/config";
import { streamAsyncIterator } from "./asyncIterator";

interface StreamChatParams {
  url: string;
  query: string;
  integrator: string;
  model?: string;
  onChunk: (chunk: string) => void;
}

async function streamChat({ url, query, integrator, model, onChunk }: StreamChatParams) {
    const response = await fetch(`${baseUrl}/api/retrieve-chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, query, integrator, model }),
  });
  if (!response.body) {
    throw new Error("No streaming body in response");
  }
  const reader = response.body.getReader();
  let fullResponse = "";
  for await (const chunk of streamAsyncIterator(reader)) {
    fullResponse += chunk;
    onChunk(fullResponse);
  }
  return fullResponse;
}

export { streamChat };