'use client'

export default function LessonCard() {
    return (
        <div className="h-40 rounded-2xl border border-border bg-surface p-4 flex flex-col justify-between">
            <div>
                <h3 className="text-lg font-semibold text-primary-text mb-1">Lesson Title</h3>
                <p className="text-sm text-primary-text/80">Brief description of the lesson content goes here.</p>
            </div>
            <div className="flex items-center justify-end gap-2">
                <button className="text-secondary-text hover:text-primary-text transition-colors text-sm">Edit</button>
                <button className="text-secondary-text hover:text-primary-text transition-colors text-sm">Delete</button>
            </div>
        </div>
    );
}