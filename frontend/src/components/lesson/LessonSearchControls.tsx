'use client';

import { Search, X } from 'lucide-react';

import Dropdown from '@/components/ui/Dropdown';
import TagFilterChips from '@/components/ui/TagFilterChips';
import { LESSON_FORMAT_OPTIONS, type PublishedTagItem } from '@/lib/types/api';

const FORMAT_OPTIONS = [{ label: 'All formats', value: '' }, ...LESSON_FORMAT_OPTIONS];

interface LessonSearchControlsProps {
  query: string;
  format: string;
  tags: PublishedTagItem[];
  selectedTags: string[];
  queryPlaceholder: string;
  queryAriaLabel: string;
  tagsAriaLabel: string;
  onQueryChange: (query: string) => void;
  onFormatChange: (format: string) => void;
  onSelectedTagsChange: (tags: string[]) => void;
}

export default function LessonSearchControls({
  query,
  format,
  tags,
  selectedTags,
  queryPlaceholder,
  queryAriaLabel,
  tagsAriaLabel,
  onQueryChange,
  onFormatChange,
  onSelectedTagsChange,
}: LessonSearchControlsProps) {
  const hasFilters = Boolean(query || format || selectedTags.length);

  function toggleTag(value: string) {
    onSelectedTagsChange(
      selectedTags.includes(value)
        ? selectedTags.filter((tag) => tag !== value)
        : [...selectedTags, value],
    );
  }

  return (
    <section className="flex flex-col gap-3">
      <section className="flex flex-col gap-3 lg:flex-row">
        <label className="relative flex min-h-12 flex-1 items-center rounded-lg border border-border bg-secondary-bg text-primary-text focus-within:border-accent">
          <Search className="ml-4 shrink-0 text-secondary-text" size={20} aria-hidden="true" />
          <input
            type="search"
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            aria-label={queryAriaLabel}
            placeholder={queryPlaceholder}
            className="h-12 min-w-0 flex-1 bg-transparent px-3 text-sm text-primary-text outline-none placeholder:text-secondary-text"
          />
          {query && (
            <button
              type="button"
              onClick={() => onQueryChange('')}
              className="mr-3 rounded-md p-1 text-secondary-text transition-colors hover:bg-primary-text/10 hover:text-primary-text focus:outline-none focus:ring-2"
              aria-label="Clear search"
            >
              <X size={18} aria-hidden="true" />
            </button>
          )}
        </label>

        <section className="w-full lg:w-64">
          <Dropdown
            options={FORMAT_OPTIONS}
            value={format}
            onChange={onFormatChange}
            placeholder="All formats"
            variant="search"
          />
        </section>
      </section>

      <TagFilterChips
        tags={tags}
        selected={selectedTags}
        onToggle={toggleTag}
        ariaLabel={tagsAriaLabel}
      />

      {hasFilters && (
        <button
          type="button"
          onClick={() => {
            onQueryChange('');
            onFormatChange('');
            onSelectedTagsChange([]);
          }}
          className="w-fit text-xs font-medium text-accent hover:text-amber-500"
        >
          Clear all filters
        </button>
      )}
    </section>
  );
}
