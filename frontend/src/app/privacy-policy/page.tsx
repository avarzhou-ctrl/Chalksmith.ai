import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Privacy Policy | Chalksmith.ai',
  description: 'Read the Chalksmith.ai privacy policy.',
}

const contents = [
  ['What This Privacy Policy Covers', 'what-this-privacy-policy-covers'],
  ['Personal Data', 'personal-data'],
  ['Sources of Personal Data', 'sources-of-personal-data'],
  ['Personal Data of Children', 'personal-data-of-children'],
  ['Cookies', 'cookies'],
  ['Data Security and Retention', 'data-security-and-retention'],
  ['Changes to this Privacy Policy', 'changes-to-this-privacy-policy'],
  ['Contact Us', 'contact-us'],
]

const linkClassName = 'text-stone-50 underline decoration-stone-50 underline-offset-4 hover:decoration-2'

export default function PrivacyPolicyPage() {
  return (
    <main className="min-h-screen bg-primary-bg text-stone-50">
      <article className="mx-auto flex w-full max-w-4xl flex-col gap-8 px-4 py-12 sm:px-6 lg:px-8">
        <header className="border-b border-stone-700 pb-6">
          <h1 className="text-4xl font-bold tracking-normal text-stone-50">Privacy Policy</h1>
          <p className="mt-2 text-sm text-stone-50">Last Updated: June 11, 2026</p>
        </header>

        <nav className="rounded-lg border border-stone-700 p-5" aria-label="Privacy policy contents">
          <h2 className="text-sm font-semibold uppercase tracking-normal text-stone-50">Policy contents</h2>
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
            At Chalksmith.ai, your privacy is critically important to us. Please read this Privacy Policy to learn how
            we treat your personal data. By using or accessing our Services in any manner, you acknowledge that you
            accept the practices and policies outlined below, and you hereby consent that we will collect, use and share
            your information as described in this Privacy Policy.
          </p>
          <p className="leading-8 text-stone-50">
            If you have any concerns, please contact{' '}
            <a className={linkClassName} href="mailto:help@chalksmith.ai">
              help@chalksmith.ai
            </a>
          </p>
        </section>

        <section id="what-this-privacy-policy-covers" className="scroll-mt-28">
          <h2 className="text-2xl font-semibold tracking-normal text-stone-50">What This Privacy Policy Covers</h2>
          <p className="mt-4 leading-8 text-stone-50">
            This Privacy Policy covers how we handle Personal Data collected when you access or use our Services.
            Personal Data refers to any information that identifies or relates to a particular individual. Please note
            that this Privacy Policy does not apply to the practices of companies we do not own or control that have a
            separate privacy policy.
          </p>
        </section>

        <section id="personal-data" className="scroll-mt-28">
          <h2 className="text-2xl font-semibold tracking-normal text-stone-50">Personal Data</h2>
          <p className="mt-4 leading-8 text-stone-50">
            We only collect information about you if we have a reason to do so, for example, to provide our Services, to
            communicate with you, or to make our Services better. The list below details the categories of Personal Data
            we collect.
          </p>

          <div className="mt-6 flex flex-col gap-6">
            <section>
              <h3 className="text-lg font-semibold tracking-normal text-stone-50">Profile Data</h3>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-stone-50">
                <li>First and last name</li>
                <li>Email</li>
                <li>Authentication identifiers provided securely by Clerk</li>
                <li>Shared with service providers</li>
              </ul>
            </section>
          </div>
        </section>

        <section id="sources-of-personal-data" className="scroll-mt-28">
          <h2 className="text-2xl font-semibold tracking-normal text-stone-50">Sources of Personal Data</h2>
          <p className="mt-4 leading-8 text-stone-50">
            We collect Personal Data from the following categories of sources.
          </p>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-stone-50">
            <li>When you create an account or use our interactive tools and Services.</li>
            <li>When you send us an email or contact us.</li>
            <li>When you use the Services and information is collected automatically through Cookies.</li>
          </ul>

          <h3 className="mt-6 text-lg font-semibold tracking-normal text-stone-50">
            Purposes for Collecting Personal Data
          </h3>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-stone-50">
            <li>
              Service Provision: To create and maintain your account and authenticate your
              login sessions securely.
            </li>
            <li>AI Content Generation: To process your design and prompt inputs through our automated animation engines.</li>
            <li>Communication: To send you technical updates, security alerts, and administrative messages.</li>
            <li>Service Improvement: To monitor system performance, fix bugs, and optimize our STEM engine configurations.</li>
          </ul>

          <h3 className="mt-6 text-lg font-semibold tracking-normal text-stone-50">How We Share Your Personal Data</h3>
          <p className="mt-3 leading-8 text-stone-50">
            We do not sell your Personal Data. We only share your data with trusted third-party subprocessors necessary
            to deliver our Services.
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-stone-50">
            <li>
              Authentication Providers:{' '}
              <a className={linkClassName} href="https://clerk.com/" rel="noreferrer" target="_blank">
                Clerk
              </a>{' '}
              securely manages user account creation and login sessions.
            </li>
            <li>
              Database Infrastructure:{' '}
              <a className={linkClassName} href="https://cloud.google.com/sql" rel="noreferrer" target="_blank">
                Google Cloud SQL for PostgreSQL
              </a>{' '}
              hosts and manages lesson metadata and ownership records.
            </li>
            <li>
              AI Engine Partners:{' '}
              <a className={linkClassName} href="https://ai.google.dev/" rel="noreferrer" target="_blank">
                the configured AI provider (Google Gemini or OpenAI)
              </a>{' '}
              receives text prompt inputs to synthesize educational visualizations. We do not share your name, email, or
              profile data with these providers.
            </li>
          </ul>
        </section>

        <section id="personal-data-of-children" className="scroll-mt-28">
          <h2 className="text-2xl font-semibold tracking-normal text-stone-50">Personal Data of Children</h2>
          <p className="mt-4 leading-8 text-stone-50">
            Our Services are primarily designed for educators and students under instructional guidance. We do not
            knowingly collect personal data directly from children under the age of 13 without verifiable parental or
            institutional consent. If you believe a child under 13 has provided us with personal data without proper
            consent, please contact us immediately at{' '}
            <a className={linkClassName} href="mailto:help@chalksmith.ai">
              help@chalksmith.ai
            </a>{' '}
            so we can delete the information.
          </p>
        </section>

        <section id="cookies" className="scroll-mt-28">
          <h2 className="text-2xl font-semibold tracking-normal text-stone-50">Cookies</h2>
          <p className="mt-4 leading-8 text-stone-50">
            We use strictly necessary cookies to keep our Services functioning safely and correctly.
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-stone-50">
            <li>
              Strictly Necessary Storage: Clerk stores essential session data in your browser so the
              platform can remember your login state across pages.
            </li>
            <li>
              Managing Cookies: You can modify your browser settings to decline or clear cookies, but doing so will
              prevent you from logging in and accessing the animation workspace.
            </li>
          </ul>
        </section>

        <section id="data-security-and-retention" className="scroll-mt-28">
          <h2 className="text-2xl font-semibold tracking-normal text-stone-50">Data Security and Retention</h2>
          <p className="mt-4 leading-8 text-stone-50">
            We protect your information using industry-standard technical measures provided by our hosting and database
            networks. We retain your Personal Data only for as long as your account remains active or as needed to
            provide you with our educational tools. You may request the deletion of your account and associated historical
            data at any time by contacting us.
          </p>
        </section>

        <section id="changes-to-this-privacy-policy" className="scroll-mt-28">
          <h2 className="text-2xl font-semibold tracking-normal text-stone-50">Changes to this Privacy Policy</h2>
          <p className="mt-4 leading-8 text-stone-50">
            We may update this Privacy Policy from time to time to reflect changes in our software or regulatory
            guidelines. We will notify you of any material changes by updating the Last Updated date at the top of this
            policy or via an in-app alert.
          </p>
        </section>

        <section id="contact-us" className="scroll-mt-28">
          <h2 className="text-2xl font-semibold tracking-normal text-stone-50">Contact Us</h2>
          <p className="mt-4 leading-8 text-stone-50">
            If you have any questions, data deletion requests, or concerns regarding this policy, please reach out to us
            at{' '}
            <a className={linkClassName} href="mailto:help@chalksmith.ai">
              help@chalksmith.ai
            </a>
          </p>
        </section>
      </article>
    </main>
  );
}
