import {
  Braces,
  FileText,
  MessageSquareText,
  MousePointerClick,
  Presentation,
  Video,
  type LucideIcon,
} from 'lucide-react';

type PipelineNodeProps = {
  icon: LucideIcon;
  label: string;
  detail: string;
};

function PipelineNode({ icon: Icon, label, detail }: PipelineNodeProps) {
  return (
    <div className="relative flex min-w-0 items-center gap-3 rounded-xl border border-stone-700/80 bg-stone-900/85 p-3 text-left shadow-lg shadow-black/20 backdrop-blur-sm">
      <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-stone-800 text-amber-400">
        <Icon className="size-4" aria-hidden="true" />
      </span>
      <span className="min-w-0">
        <span className="block text-sm font-semibold text-stone-100">{label}</span>
        <span className="block truncate text-xs text-stone-400">{detail}</span>
      </span>
    </div>
  );
}

const paths = [
  'M220 73 C350 73 350 144 455 144',
  'M220 215 C350 215 350 144 455 144',
  'M545 144 C650 144 650 62 780 62',
  'M545 144 C650 144 650 144 780 144',
  'M545 144 C650 144 650 226 780 226',
];

export default function LessonPipeline() {
  return (
    <figure aria-label="Lesson source to output pipeline" className="relative mx-auto mt-10 w-full max-w-5xl rounded-3xl border border-stone-800 bg-stone-950/55 p-4 shadow-2xl shadow-black/30 backdrop-blur-sm sm:p-5">
      <div className="relative hidden min-h-72 md:block">
        <svg className="pointer-events-none absolute inset-0 size-full" viewBox="0 0 1000 288" preserveAspectRatio="none" aria-hidden="true">
          {paths.map((path) => (
            <path key={`base-${path}`} d={path} fill="none" pathLength="1" stroke="rgb(68 64 60)" strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
          ))}
          {paths.map((path, index) => (
            <path
              key={path}
              d={path}
              fill="none"
              pathLength="1"
              stroke="rgb(245 158 11)"
              strokeDasharray="0.12 0.88"
              strokeLinecap="round"
              strokeWidth="2"
              vectorEffect="non-scaling-stroke"
              className="animate-pipeline-flow motion-reduce:animate-none"
              style={{ animationDelay: `${index * -0.45}s` }}
            />
          ))}
        </svg>

        <div className="absolute left-0 top-1/2 w-[24%] -translate-y-1/2 space-y-20">
          <PipelineNode icon={FileText} label="Upload a source" detail="Syllabus, notes, or PDF" />
          <PipelineNode icon={MessageSquareText} label="Describe a lesson" detail="Topic, level, and goals" />
        </div>

        <div className="absolute left-1/2 top-1/2 w-[19%] -translate-x-1/2 -translate-y-1/2">
          <div className="animate-forge-pulse rounded-2xl border border-amber-500/50 bg-stone-900 p-4 text-center shadow-xl shadow-amber-950/40 motion-reduce:animate-none">
            <span className="mx-auto grid size-12 place-items-center rounded-xl bg-amber-600 text-stone-950 shadow-lg shadow-amber-600/20">
              <Braces className="size-6" aria-hidden="true" />
            </span>
            <span className="mt-3 block text-sm font-bold text-stone-50">Editable code</span>
            <span className="mt-1 block text-xs text-stone-400">The Chalksmith forge</span>
          </div>
        </div>

        <div className="absolute right-0 top-1/2 w-[24%] -translate-y-1/2 space-y-5">
          <PipelineNode icon={Video} label="Video" detail="Code-driven animation" />
          <PipelineNode icon={MousePointerClick} label="Interactive" detail="Student-controlled display" />
          <PipelineNode icon={Presentation} label="Slides" detail="Classroom presentation" />
        </div>
      </div>

      <div className="grid gap-3 md:hidden">
        <div className="grid gap-3 sm:grid-cols-2">
          <PipelineNode icon={FileText} label="Upload a source" detail="Syllabus, notes, or PDF" />
          <PipelineNode icon={MessageSquareText} label="Describe a lesson" detail="Topic, level, and goals" />
        </div>
        <span aria-hidden="true" className="mx-auto h-6 w-px bg-gradient-to-b from-stone-700 to-amber-500" />
        <div className="mx-auto w-full max-w-48 rounded-2xl border border-amber-500/50 bg-stone-900 p-4 text-center shadow-xl shadow-amber-950/40">
          <Braces className="mx-auto size-6 text-amber-400" aria-hidden="true" />
          <span className="mt-2 block text-sm font-bold text-stone-50">Editable code</span>
          <span className="mt-1 block text-xs text-stone-400">The Chalksmith forge</span>
        </div>
        <span aria-hidden="true" className="mx-auto h-6 w-px bg-gradient-to-b from-amber-500 to-stone-700" />
        <div className="grid gap-3 sm:grid-cols-3">
          <PipelineNode icon={Video} label="Video" detail="Code-driven animation" />
          <PipelineNode icon={MousePointerClick} label="Interactive" detail="Student-controlled display" />
          <PipelineNode icon={Presentation} label="Slides" detail="Classroom presentation" />
        </div>
      </div>
    </figure>
  );
}
