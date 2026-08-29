const faqs = [
  {
    question: 'Is Chalksmith free to try?',
    answer:
      'Yes. Teachers can create an account and try the lesson generation workflow before deciding whether Chalksmith fits their classroom planning needs.',
  },
  {
    question: 'What can Chalksmith generate?',
    answer:
      'Chalksmith can generate code-driven STEM videos, interactive p5.js demonstrations, and Reveal.js-style slides from a prompt or uploaded lesson source.',
  },
  {
    question: 'Can I edit the generated materials?',
    answer:
      'Yes. Chalksmith is built around editable source, so teachers can review and adjust the code behind generated lessons instead of being locked into a black-box output.',
  },
  {
    question: 'Who is Chalksmith designed for?',
    answer:
      'Chalksmith is designed for elementary and middle school STEM teachers who need visual, reusable teaching materials without spending hours building every asset from scratch.',
  },
  {
    question: 'Can I use my own curriculum materials?',
    answer:
      'Yes. You can start from syllabus notes, readings, or lesson goals so the generated lesson stays closer to your classroom context.',
  },
  {
    question: 'What makes Chalksmith different from slide or worksheet tools?',
    answer:
      'Chalksmith focuses on code-driven visual learning materials: animations, interactives, and slides that can be inspected, reused, and adapted across lessons.',
  },
];

export default function FaqSection() {
  return (
    <section id="faq" className="mx-auto w-full max-w-4xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
      <div className="text-center">
        <h2 className="text-4xl font-bold text-primary-text sm:text-5xl">FAQ</h2>
        <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-secondary-text">
          A few practical answers for teachers trying Chalksmith for the first time.
        </p>
      </div>
   
      <div className="mt-10 space-y-3">
        {faqs.map((faq) => (
          <details
            key={faq.question}
            className="group rounded-lg border border-secondary-bg bg-secondary-bg p-5 text-left transition-colors open:border-accent/60"
          >
            <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-base font-semibold text-primary-text marker:hidden">
              <span>{faq.question}</span>
              <span className="grid size-8 shrink-0 place-items-center rounded-lg border border-border text-accent transition-transform">
                <svg 
                    className="size-4 shrink-0 transition-transform duration-300 group-open:rotate-180"
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </span>
            </summary>
            <p className="mt-4 max-w-3xl text-sm leading-6 text-secondary-text sm:text-base sm:leading-7">
              {faq.answer}
            </p>
          </details>
        ))}
      </div>
    </section>
  );
}
