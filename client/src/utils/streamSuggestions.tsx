import { baseUrl } from "~/config";
import { streamAsyncIterator } from "./asyncIterator";

async function streamSuggestions({
    url,
    integrator,
    onChunk,
  }: {
    url: string;
    integrator: string;
    onChunk: (chunk: string) => void;
  }) {
    const response = await fetch(`${baseUrl}/api/suggest-articles`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, integrator }),
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
  
export { streamSuggestions };