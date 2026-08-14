import type { ApiClient } from '@/lib/api/client';
import { ApiError, apiErrorFromResponse } from '@/lib/api/client';
import type { GenerationEvent, GenerationRequest } from '@/lib/types/api';

interface StreamGenerationOptions {
  client: ApiClient;
  request: GenerationRequest;
  onEvent: (event: GenerationEvent) => void;
  signal?: AbortSignal;
}

export async function streamGeneration({
  client,
  request,
  onEvent,
  signal,
}: StreamGenerationOptions): Promise<void> {
  const response = await client.requestRaw('/v2/generations', {
    method: 'POST',
    headers: { Accept: 'text/event-stream' },
    body: toFormData(request),
    signal,
  });

  if (!response.ok || !response.body) {
    if (!response.ok) throw await apiErrorFromResponse(response);
    throw new ApiError(
      'Generation stream ended without a response body.',
      response.status,
      'GENERATION_STREAM_FAILED',
    );
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done }).replace(/\r\n/g, '\n');

    const eventBlocks = buffer.split('\n\n');
    buffer = eventBlocks.pop() ?? '';
    eventBlocks.forEach((block) => emitEvent(block, onEvent));

    if (done) break;
  }

  if (buffer.trim()) emitEvent(buffer, onEvent);
}

function toFormData(request: GenerationRequest): FormData {
  const formData = new FormData();
  formData.set('topic', request.topic);
  formData.set('format', request.format);
  if (request.baseLessonId) formData.set('base_lesson_id', request.baseLessonId);
  if (request.editInstruction) formData.set('edit_instruction', request.editInstruction);
  request.sourceFiles?.forEach((file) => formData.append('sources', file, file.name));
  return formData;
}

function emitEvent(block: string, onEvent: (event: GenerationEvent) => void): void {
  const eventType = block
    .split('\n')
    .find((line) => line.startsWith('event:'))
    ?.slice(6)
    .trim();
  const data = block
    .split('\n')
    .filter((line) => line.startsWith('data:'))
    .map((line) => line.slice(5).trimStart())
    .join('\n');

  if (data && eventType) {
    onEvent({ type: eventType, ...JSON.parse(data) } as GenerationEvent);
  }
}
