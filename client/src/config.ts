const baseUrl = 'http://localhost:8000';

const integratorKey = 'integrators';

const integratorOptions = [
    { label: "OpenAI", value: "openai" },
    { label: "TogetherAI", value: "together" },
  ];

const openAImodelOptions = [
    { label: "GPT-4o-mini", value: "gpt-4o-mini" },
    { label: "GPT-4.1", value: "gpt-4.1" },
    { label: "GPT-4.1-mini", value: "gpt-4.1-mini" },
    { label: "GPT-4o", value: "gpt-4o" },
    { label: "GPT-3.5 Turbo", value: "gpt-3.5-turbo" }
  ];

const togetherAImodelOptions = [
    { label: "Meta llama 3.1 405b instruct turbo", value: "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo" },
    { label: "Meta llama 3.3 70b instruct turbo", value: "meta-llama/Llama-3.3-70B-Instruct-Turbo" },
    { label: "Meta llama 3.3 70b instruct turbo free", value: "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free" },
    { label: "Deepseek v3-0324", value: "deepseek-ai/DeepSeek-V3" },
    { label: "Deepseek r1", value: "deepseek-ai/DeepSeek-R1" },
    { label: "Deepseek r1 distill llama 70b free", value: "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free" },
    { label: "Qwen2.5 72b instruct turbo", value: "Qwen/Qwen2.5-72B-Instruct-Turbo" },
    { label: "Qwen2.5 7b instruct turbo", value: "Qwen/Qwen2.5-7B-Instruct-Turbo" }
  ];

const modelMapper = {
    openai: openAImodelOptions,
    together: togetherAImodelOptions
}

const chunkSizeOptions = [
  { label: "Select chunk size", value: "0" },
  { label: "20 segments", value: "20" },
  { label: "50 segments", value: "50" },
  { label: "100 segments", value: "100" },
  { label: "150 segments", value: "150" },
  { label: "200 segments", value: "200" },
  { label: "300 segments", value: "300" }
]

export { 
  integratorOptions, 
  baseUrl, 
  integratorKey, 
  modelMapper,
  chunkSizeOptions 
};