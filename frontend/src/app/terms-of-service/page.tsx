import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Terms of Service | Chalksmith.ai',
  description: 'Read the Chalksmith.ai terms of service.',
}

const contents = [
  ['Account Creation and Authentication', 'account-creation-and-authentication'],
  ['User Content and AI Generations', 'user-content-and-ai-generations'],
  ['Acceptable Use Policy', 'acceptable-use-policy'],
  ['Termination of Service', 'termination-of-service'],
  ['Disclaimers and Limitation of Liability', 'disclaimers-and-limitation-of-liability'],
  ['Changes to These Terms', 'changes-to-these-terms'],
  ['Contact', 'contact'],
]

const linkClassName = 'text-stone-50 underline decoration-stone-50 underline-offset-4 hover:decoration-2'

export default function TermsOfServicePage() {
  return (
    <main className="min-h-screen bg-primary-bg text-stone-50">
      <article className="mx-auto flex w-full max-w-4xl flex-col gap-8 px-4 py-12 sm:px-6 lg:px-8">
        <header className="border-b border-stone-700 pb-6">
          <h1 className="text-4xl font-bold tracking-normal text-stone-50">Terms of Service</h1>
          <p className="mt-2 text-sm text-stone-50">Last Updated: June 11, 2026</p>
        </header>

        <nav className="rounded-lg border border-stone-700 p-5" aria-label="Terms of service contents">
          <h2 className="text-sm font-semibold uppercase tracking-normal text-stone-50">Terms contents</h2>
          <ul className="mt-4 grid gap-3 sm:grid-cols-2">
            {contents.map(([label, href]) => (
              <li key={href}>
                <a className={linkClassName} href={`#${href}`}>
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <section className="flex flex-col gap-5">
          <p className="leading-8 text-stone-50">
            Welcome to Chalksmith.ai (&quot;we,&quot; &quot;our,&quot; or &quot;us&quot;). Please read these Terms of
            Service carefully before using our website, tools, and automated animation generation engine.
          </p>
          <p className="leading-8 text-stone-50">
            By creating an account, clicking an &quot;I Agree&quot; checkbox, or accessing the Service in any capacity,
            you agree to be bound by these Terms. If you are entering into these Terms on behalf of a school,
            educational institution, or company, you represent that you have the legal authority to bind that entity to
            these rules.
          </p>
          <p className="leading-8 text-stone-50">
            If you have any questions or feedback regarding these terms, please contact us at{' '}
            <a className={linkClassName} href="mailto:help@chalksmith.ai">
              help@chalksmith.ai
            </a>
          </p>
        </section>

        <section id="account-creation-and-authentication" className="scroll-mt-28">
          <h2 className="text-2xl font-semibold tracking-normal text-stone-50">
            Account Creation and Authentication
          </h2>
          <p className="mt-4 leading-8 text-stone-50">To access our STEM workspace, you must register for an account.</p>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-stone-50">
            <li>
              Authentication Providers: We utilize Google Cloud Identity Platform to handle user registration, identity verification, and login
              sessions securely.
            </li>
            <li>
              Account Responsibility: You are entirely responsible for maintaining the confidentiality of your session
              keys and account data. You agree to notify us immediately of any unauthorized access or security breach.
            </li>
            <li>
              Accurate Information: You must provide us with a valid email address and accurate profiling information so
              we can manage your service access correctly.
            </li>
          </ul>
        </section>

        <section id="user-content-and-ai-generations" className="scroll-mt-28">
          <h2 className="text-2xl font-semibold tracking-normal text-stone-50">User Content and AI Generations</h2>

          <h3 className="mt-6 text-lg font-semibold tracking-normal text-stone-50">Inputs and Outputs</h3>
          <p className="mt-3 leading-8 text-stone-50">
            Our Service allows you to submit text descriptions, parameters, and curriculum concepts (&quot;Inputs&quot;)
            to generate interactive visualizations, animations, and lesson blueprints (&quot;Outputs&quot;).
          </p>

          <h3 className="mt-6 text-lg font-semibold tracking-normal text-stone-50">Content Ownership</h3>
          <p className="mt-3 leading-8 text-stone-50">
            As between you and Chalksmith, you maintain full ownership over all your raw Inputs. Subject to your
            continuous compliance with these Terms, Chalksmith hereby grants you a perpetual, worldwide, non-exclusive,
            royalty-free, fully transferable license to use, project, display, modify, and distribute the generated
            Outputs for any personal, commercial, or classroom instructional purposes.
          </p>

          <h3 className="mt-6 text-lg font-semibold tracking-normal text-stone-50">System Operational License</h3>
          <p className="mt-3 leading-8 text-stone-50">
            To operate the platform effectively, you grant Chalksmith a limited, worldwide, non-exclusive, royalty-free
            license to host, store, replicate, and stream your Inputs and Outputs solely to maintain your account
            history, populate your user dashboard, and optimize backend model configurations.
          </p>

          <h3 className="mt-6 text-lg font-semibold tracking-normal text-stone-50">
            AI Accuracy and Integrity Disclaimer
          </h3>
          <p className="mt-3 leading-8 text-stone-50">
            Outputs are generated utilizing advanced artificial intelligence configurations, including upstream partners
            like Google Gemini. Because machine learning systems are probabilistic, Chalksmith cannot guarantee the
            absolute scientific correctness, mathematical accuracy, or pedagogical validity of any generated animation or
            code block. You assume all risk and responsibility for validating the correctness of any generated Outputs
            before presenting them to students or utilizing them in an academic setting.
          </p>
        </section>

        <section id="acceptable-use-policy" className="scroll-mt-28">
          <h2 className="text-2xl font-semibold tracking-normal text-stone-50">Acceptable Use Policy</h2>
          <p className="mt-4 leading-8 text-stone-50">
            We want to keep Chalksmith safe, reliable, and functional for educators everywhere. You agree not to misuse
            the Service, including but not limited to:
          </p>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-stone-50">
            <li>
              Attempting to reverse-engineer, scrape, decompile, or extract the underlying code or prompt frameworks of
              our STEM animation engines.
            </li>
            <li>
              Utilizing automated scripts, bots, or custom headless scrapers to execute generations beyond the
              designated UI limits.
            </li>
            <li>
              Generating inputs or content that is illegal, defamatory, harmful, or infringes on the intellectual
              property rights of others.
            </li>
          </ul>
        </section>

        <section id="termination-of-service" className="scroll-mt-28">
          <h2 className="text-2xl font-semibold tracking-normal text-stone-50">Termination of Service</h2>
          <p className="mt-4 leading-8 text-stone-50">
            We reserve the right to suspend or terminate your access to the Service immediately, without prior notice, if
            we determine in our sole discretion that you have violated these Terms, engaged in fraudulent activity, or
            caused structural strain to our infrastructure or API integrations. You may delete your account and
            associated database history at any time by contacting support.
          </p>
        </section>

        <section id="disclaimers-and-limitation-of-liability" className="scroll-mt-28">
          <h2 className="text-2xl font-semibold tracking-normal text-stone-50">
            Disclaimers and Limitation of Liability
          </h2>
          <p className="mt-4 leading-8 text-stone-50">
            THE SERVICE IS PROVIDED ON AN &quot;AS-IS&quot; AND &quot;AS-AVAILABLE&quot; BASIS, WITHOUT WARRANTIES OF ANY
            KIND, EITHER EXPRESS OR IMPLIED. CHALKSMITH DISCLAIMS ALL WARRANTIES, INCLUDING IMPLIED WARRANTIES OF
            MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
          </p>
          <p className="mt-4 leading-8 text-stone-50">
            IN NO EVENT SHALL CHALKSMITH, ITS DEVELOPERS, OR ITS UPSTREAM INFRASTRUCTURE PARTNERS BE LIABLE FOR ANY
            INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES ARISING OUT OF OR RELATING TO YOUR USE OF
            OR INABILITY TO ACCESS THE ANIMATION ENGINE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
          </p>
        </section>

        <section id="changes-to-these-terms" className="scroll-mt-28">
          <h2 className="text-2xl font-semibold tracking-normal text-stone-50">Changes to These Terms</h2>
          <p className="mt-4 leading-8 text-stone-50">
            We may update these Terms from time to time to accommodate new engineering features, software expansions, or
            updated regulatory frameworks. We will notify you of any material changes by updating the Last Updated
            timestamp at the top of this document or by providing a notification directly inside your workspace
            dashboard. Continued use of the platform after changes go live constitutes complete acceptance of the updated
            Terms.
          </p>
        </section>

        <section id="contact" className="scroll-mt-28">
          <h2 className="text-2xl font-semibold tracking-normal text-stone-50">Contact</h2>
          <p className="mt-4 leading-8 text-stone-50">
            If you have any questions, legal inquiries, or compliance notes regarding these Terms, please reach out to us
            at{' '}
            <a className={linkClassName} href="mailto:help@chalksmith.ai">
              help@chalksmith.ai
            </a>
          </p>
        </section>
      </article>
    </main>
  )
}
