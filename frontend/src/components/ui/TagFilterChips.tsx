import type { PublishedTagItem } from '@/lib/types/api';

interface TagFilterChipsProps {
  tags: PublishedTagItem[];
  selected: string[];
  onToggle: (value: string) => void;
  ariaLabel: string;
}

export default function TagFilterChips({
  tags,
  selected,
  onToggle,
  ariaLabel,
}: TagFilterChipsProps) {
  if (!tags.length) return null;

  return (
    <section className="flex flex-wrap gap-2" aria-label={ariaLabel}>
      {tags.map((tag) => {
        const isSelected = selected.includes(tag.value);
        return (
          <button
            key={tag.value}
            type="button"
            aria-pressed={isSelected}
            onClick={() => onToggle(tag.value)}
            className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 ${
              isSelected
                ? 'border-accent bg-accent text-primary-text'
                : 'border-border bg-secondary-bg text-secondary-text hover:border-accent hover:text-primary-text'
            }`}
          >
            {tag.label}
            <span className={isSelected ? 'ml-1 text-primary-text/70' : 'ml-1 text-secondary-text'}>
              {tag.lesson_count}
            </span>
          </button>
        );
      })}
    </section>
  );
}
