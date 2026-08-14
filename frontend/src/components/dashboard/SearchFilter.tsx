import Dropdown from '@/components/ui/Dropdown';
import { LESSON_FORMAT_OPTIONS } from '@/lib/types/api';

interface SearchFilterProps {
    format: string;
    onFormatChange: (value: string) => void;
}

const formatOptions = [{ label: 'All formats', value: '' }, ...LESSON_FORMAT_OPTIONS];

export default function SearchFilter({
    format,
    onFormatChange,
}: SearchFilterProps) {
    return (
        <Dropdown
            options={formatOptions}
            value={format}
            onChange={onFormatChange}
            placeholder="All formats"
            variant="search"
        />
    );
}
