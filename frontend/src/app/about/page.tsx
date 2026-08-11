import Footer from "@/components/home/Footer";
import {
    BookOpen,
    Camera,
    Code2,
    Mail,
    MessageCircle,
    Newspaper,
    Play,
    type LucideIcon,
} from 'lucide-react';

const socialContacts: { icon: LucideIcon; label: string; detail: string; href: string }[] = [
    {
        icon: Mail,
        label: 'Email',
        detail: 'avarzhou@gmail.com',
        href: 'mailto:avarzhou@gmail.com',
    },
    {
        icon: Code2,
        label: 'GitHub',
        detail: '@avarzhou-ctrl',
        href: 'https://github.com/avarzhou-ctrl',
    },
    {
        icon: Play,
        label: 'YouTube',
        detail: '@SquishBJ',
        href: 'https://www.youtube.com/@SquishBJ',
    },
    {
        icon: MessageCircle,
        label: 'X (Twitter)',
        detail: '@SquishBJ',
        href: 'https://x.com/SquishBJ',
    },
    {
        icon: Newspaper,
        label: 'Substack',
        detail: '@squishbj',
        href: 'https://substack.com/@squishbj',
    },
    {
        icon: BookOpen,
        label: 'Medium',
        detail: '@SquishBJ',
        href: 'https://medium.com/@SquishBJ',
    },
    {
        icon: Camera,
        label: 'Instagram',
        detail: '@squishbj',
        href: 'https://www.instagram.com/squishbj',
    }
];

export default function About() {
    return (
        <main className="relative min-h-screen overflow-hidden bg-primary-bg text-primary-text">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(217,119,6,0.16),transparent_32%),radial-gradient(circle_at_80%_0%,rgba(245,158,11,0.1),transparent_26%)]" />
            <section className="relative mx-auto grid w-full max-w-6xl items-stretch gap-12 px-4 py-16 sm:px-6 lg:grid-cols-[0.88fr_1.12fr] lg:px-8 lg:py-24">
                <aside className="lg:h-full">
                    <div className="h-full overflow-hidden rounded-lg border border-stone-800 bg-secondary-bg/80 shadow-2xl shadow-black/30">
                        <div className="h-full min-h-96 rounded-lg border border-stone-700 bg-primary-bg lg:min-h-0">
                            <img src="/headshot.png" alt="Portrait of Ava Zhou" className="h-full w-full object-cover object-center" />
                        </div>
                    </div>
                </aside>

                <div>
                    <h1 className="mt-6 max-w-3xl text-4xl font-bold leading-tight text-primary-text sm:text-5xl">
                        Hi, I&apos;m <span className="text-accent">Ava Zhou</span>, founder of Chalksmith and high schooler at the Western Academy of Beijing.
                    </h1>
                    <div className="mt-8 space-y-5 text-lg leading-8 text-secondary-text">
                        <p>
                            Growing up in a highly diverse international school, I noticed that STEM teachers frequently
                            struggled to personalize learning materials for every student. They spent hours manually
                            creating multiple variations of the same content, spending time that could have been dedicated
                            to supporting students who were falling behind.
                        </p>
                        <p>
                            What started as a school project soon became a deep dive into full-stack software architecture
                            and SaaS development. I built Chalksmith.ai to support my mission of leveraging technology to
                            make engaging, highly accessible education available to students everywhere.
                        </p>
                    </div>
                </div>
            </section>
            <section className="relative mx-auto grid w-full max-w-6xl items-center gap-10 px-4 pb-20 pt-4 sm:px-6 lg:grid-cols-[0.92fr_1.08fr] lg:px-8">
                <div className="lg:-translate-y-8">
                    <h2 className="max-w-xl text-3xl font-bold leading-tight text-primary-text sm:text-5xl">
                        Connect and get in touch.
                    </h2>
                    <p className="mt-5 max-w-lg text-base leading-7 text-secondary-text">
                        Reach out about Chalksmith.ai, classroom use cases, or feedback on generated STEM materials.
                    </p>
                    <ul className="mt-8 space-y-3">
                        {socialContacts.map((contact) => {
                            const ContactIcon = contact.icon;
                            return <li key={contact.label}>
                                <a
                                    href={contact.href}
                                    className="group flex items-center gap-4 rounded-lg border border-stone-800 bg-secondary-bg/80 p-4 transition-colors hover:border-accent/60 hover:bg-stone-800"
                                >
                                    <span className="grid size-11 shrink-0 place-items-center rounded-lg bg-accent/10 text-lg text-accent transition-colors group-hover:bg-accent group-hover:text-primary-text">
                                        <ContactIcon className="size-5" aria-hidden />
                                    </span>
                                    <span>
                                        <span className="block text-sm font-semibold text-stone-50">{contact.label}</span>
                                        <span className="mt-1 block text-sm text-secondary-text">{contact.detail}</span>
                                    </span>
                                </a>
                            </li>;
                        })}
                    </ul>
                </div>
                <div className="overflow-hidden rounded-lg p-4 shadow-2xl shadow-black/30">
                    <div className="rounded-lg bg-primary-bg p-4">
                        <img src="/books.png" alt="Stack of books" className="h-auto w-full object-contain" />
                    </div>
                </div>
            </section>

            <Footer/>
        </main>
    )
}
