export default function Footer() {
    return (
        <div className="mx-auto grid w-full max-w-7xl gap-8 px-4 py-10 text-sm text-secondary-text sm:px-6 md:grid-cols-[1fr_auto] lg:px-8">
            <div>
                <div className="flex items-center gap-3 text-primary-text">
                    <span className="grid size-9 place-items-center rounded-lg text-primary-bg">
                        <img src="/logo.png" alt="Logo" className="h-8 w-8 object-contain" />
                    </span>
                    <span className="font-semibold">Chalksmith.ai</span>
                </div>
                <p className="mt-4 max-w-md leading-6">
                    Classroom-focused AI tools for creating, reviewing, and presenting STEM teaching materials.
                </p>
                <p className="mt-4">Copyright © 2026 Chalksmith.ai. All rights reserved.</p>
            </div>
            <div className="grid gap-8 sm:grid-cols-2 sm:gap-12 md:justify-self-end">
                <div>
                    <h3 className="font-semibold text-stone-50">Legal</h3>
                    <ul className="mt-4 space-y-3">
                        <li><a className="hover:text-accent" href="/privacy-policy">Privacy Policy</a></li>
                        <li><a className="hover:text-accent" href="/terms-of-service">Terms of Service</a></li>
                    </ul>
                </div>
                <div>
                    <h3 className="font-semibold text-stone-50">Contact</h3>
                    <ul className="mt-4 space-y-3">
                        <li><a className="hover:text-accent" href="mailto:help@chalksmith.ai">help@chalksmith.ai</a></li>
                        <li><a className="hover:text-accent" href="https://github.com/avarzhou-ctrl/Chalksmith.ai/">GitHub</a></li>
                    </ul>
                </div>
            </div>
        </div>
    )
}
