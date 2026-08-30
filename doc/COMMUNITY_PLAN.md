# Chalksmith Teacher Community Plan

## Implementation Status

The private lesson-set foundation is implemented. Teachers can create, edit, and delete ordered
sets; add ready lessons from dashboard cards or the set editor; remove and reorder lessons; and
open the selected final revision from each set. Sets are owner-scoped, can contain up to 50 unique
lesson roots, follow final-revision changes automatically, and clean up membership when a lesson is
deleted. Public set publishing, school hubs, and cross-teacher collections remain future phases.

### Folders and Lesson Sets

Folders and lesson sets serve different teacher needs and are presented as separate concepts in the
dashboard:

- **Folders organize storage.** A lesson has one folder location, folders can be nested, and folder
  breadcrumbs show where a lesson is filed.
- **Lesson sets organize instruction.** A lesson can appear in several sets, each set has a deliberate
  teaching order, and set cards preview the sequence rather than a storage location.

The dashboard reinforces this distinction with separate navigation, folder-path labels on lesson
cards, lesson-set membership badges, numbered sequence previews, and purpose-specific empty states.
The list APIs return set previews and membership counts in bounded queries so these signals do not
require one request per card.

## Vision

Chalksmith should become a trusted lesson-sharing community where teachers can create, adapt, review, and reuse interactive lessons within their school or across verified school networks.

The product should be presented as a professional teaching community rather than a social network. Its value is not simply that AI can generate lessons; it is that schools can preserve, improve, and share teacher expertise while retaining control over quality, privacy, and access.

> **Administrator pitch:** Chalksmith helps schools turn individual lesson preparation into a shared, reviewable library of teacher expertise. Teachers save time by adapting proven resources, while administrators retain control over who can access, approve, and publish school content.

## What Chalksmith Already Provides

The existing platform provides a strong foundation for the community concept:

- AI generation and conversational editing of lessons.
- Interactive displays, presentations, and videos.
- Public lesson publishing and discovery.
- Searchable and editable lesson tags.
- Lesson likes and downloads.
- Public teacher profiles.
- Lesson revisions and edit lineage.

The next phase should connect these features through school organizations, curriculum metadata, remixing, and review workflows.

## Core Community Experience

The central teacher workflow should be:

```text
Find a lesson -> Preview it -> Copy it to my workspace -> Adapt it with AI -> Share it with my school
```

The most important community action should be **Copy and adapt**, not Like. Every adapted lesson should preserve:

- The original lesson and author.
- A link back to the source lesson.
- A summary of the changes.
- Version and adaptation history.
- The selected usage license.

This creates a reusable professional knowledge network instead of a gallery of disconnected materials.

## Feature Roadmap

### Phase 1: School Pilot Foundation

#### 1. School and department spaces

Create private organization hubs for schools. Each hub can contain departments, grade-level teams, and curated lesson collections.

Recommended roles:

- **Teacher:** Create, adapt, submit, and share lessons.
- **Department leader:** Review lessons and manage departmental collections.
- **School administrator:** Manage membership, permissions, policies, and school-wide publishing.
- **Network administrator:** Manage collaboration across participating schools.

#### 2. Sharing permissions

Allow a lesson owner to select one of the following visibility levels:

- Only me.
- Selected collaborators.
- Department or grade team.
- Entire school.
- Partner-school network.
- Public Chalksmith community.

#### 3. Copy and adapt

Allow teachers to copy a published or school-shared lesson into their own workspace and edit it without altering the original. Preserve attribution and adaptation lineage automatically.

#### 4. Curriculum metadata

Add structured fields that make lessons easier to discover and evaluate:

- Subject and topic.
- Grade level or grade band.
- Curriculum standards.
- Learning objectives.
- Lesson duration.
- Language.
- Prerequisite knowledge.
- Required materials.
- Lesson format.
- Accessibility information.
- Usage license.

#### 5. Review and approval workflow

Support a simple school-controlled workflow:

```text
Draft -> Submitted for review -> Changes requested or School approved
```

Approved lessons can display a school or department verification badge. Approval should indicate that an educator reviewed the resource, not that Chalksmith guarantees its accuracy.

#### 6. Moderation and quality controls

Include:

- Flags for factual errors, copyright issues, unsafe content, and accessibility problems.
- An AI-generated-content disclosure.
- A teacher review checklist before publishing.
- Administrator removal and restoration controls.
- A moderation audit log.
- A process for authors to correct or appeal reported content.

### Phase 2: Community Collaboration

#### 1. Collections and teaching units

Let teachers and departments organize lessons into sequences such as curriculum units, intervention packs, project resources, or exam-review collections.

#### 2. Structured educator feedback

Prioritize useful professional feedback over generic star ratings. Suggested feedback options include:

- Worked well with my class.
- Needs a factual correction.
- Suggested adaptation.
- Accessibility issue.
- Curriculum alignment note.

#### 3. Co-authoring

Allow teaching teams to jointly maintain lessons and collections with clear ownership and contribution history.

#### 4. Resource requests

Create a request board where educators can ask for resources, such as an interactive Grade 6 fractions lesson, and other teachers can respond with an existing or newly created lesson.

#### 5. Notifications

Notify educators when:

- A lesson they use has been updated.
- Someone adapts their lesson.
- A reviewer requests changes.
- A collaborator comments or contributes.
- A requested resource becomes available.

### Phase 3: Adoption and Integration

#### 1. School analytics

Provide administrators with aggregate measures such as:

- Lessons created, approved, reused, and adapted.
- Active teacher contributors.
- Cross-department and cross-school reuse.
- Estimated preparation time saved.
- Reported issues and resolution time.

Avoid individual student tracking during the initial rollout.

#### 2. LMS integration

Support exporting or assigning lessons through systems such as Canvas and Google Classroom after the core community workflow has been validated.

#### 3. Personalized discovery

Recommend lessons based on a teacher's subject, grade, curriculum standards, language, and saved resources. Recommendations should remain explainable and controllable.

## Administrator Requirements

The school proposal should address the following from the beginning:

### Governance

- Role-based permissions.
- School-owned spaces and content-management controls.
- Member invitation and removal.
- Review, approval, and publishing policies.
- Activity and moderation audit logs.

### Privacy and security

- No student names or personal information required for the initial pilot.
- Clear data retention, export, and deletion controls.
- Transparent descriptions of how prompts and files are processed.
- School-level configuration of approved AI features.
- Secure authentication and private-by-default school spaces.
- A documented incident-reporting process.

The U.S. Department of Education's [AI toolkit for education leaders](https://eric.ed.gov/?id=ED661924) emphasizes transparency, privacy, data security, equity, human oversight, and opportunities to opt out. Its [education technology privacy guidance](https://studentprivacy.ed.gov/privacy-and-education-technology) also recommends evaluating how online services collect, use, and transmit information before adoption. These are useful trust principles even for schools outside the United States, subject to local requirements.

### Copyright and attribution

- Require a license selection when sharing beyond a school.
- Preserve source attribution when a lesson is adapted.
- Provide copyright and inappropriate-content reporting.
- Distinguish teacher-provided material from AI-generated material.

### Accessibility

- Keyboard-operable interactives and controls.
- Adequate contrast and visible focus states.
- Captions and transcripts for narrated videos.
- Descriptions of important visual information.
- Reduced-motion options.
- Accessibility checks before approval or public publishing.

The [W3C media accessibility guidance](https://www.w3.org/WAI/media/av/) recommends captions, transcripts, descriptions of important visual information, accessible media controls, and keyboard support.

## Recommended Pilot

Run a six-to-eight-week pilot with one STEM department and approximately 10 to 20 teachers.

### Pilot setup

1. Create one private school hub.
2. Establish teacher, department reviewer, and administrator roles.
3. Require subject, grade, learning objective, and standards metadata.
4. Ask each participant to publish two lessons.
5. Ask each participant to adapt at least one colleague's lesson.
6. Have a department leader approve a small featured collection.
7. Collect teacher feedback at the midpoint and end of the pilot.

### Success measures

- Average lesson-preparation time saved.
- Number and percentage of lessons reused or adapted.
- Percentage of participants who contribute a lesson.
- Number of school-approved resources.
- Weekly active teacher participation.
- Teacher satisfaction and intent to continue using the platform.
- Number of content issues reported and resolved.
- Accessibility, privacy, or security incidents.

### Pilot success criteria

The pilot should be considered successful if teachers demonstrably save preparation time, reuse one another's work, and report that the shared library is more useful than storing isolated files in personal drives.

## Features to Defer

Do not prioritize the following before the school-sharing workflow is proven:

- Public chat rooms.
- Competitive teacher leaderboards.
- Follower counts as a primary success measure.
- Student accounts or student social features.
- A paid lesson marketplace.
- Complex student-level analytics.

These features increase moderation, privacy, and adoption risk without establishing whether educators will create, review, and reuse shared lessons.

## Presentation Structure

Use the following sequence when presenting to a school administrator:

1. **Problem:** Teachers repeatedly spend time building similar resources in isolation.
2. **Current solution:** Chalksmith already creates editable interactive lessons, presentations, and videos.
3. **Community opportunity:** Teachers can share, adapt, and improve those materials within a trusted school network.
4. **Administrative control:** Schools control membership, visibility, review, approval, and moderation.
5. **Pilot proposal:** Begin with one department for six to eight weeks and no required student data.
6. **Evidence:** Measure preparation time saved, lesson reuse, participation, quality, and safety.
7. **Decision requested:** Approve a limited pilot and nominate a department leader to help define the review process.

## One-Sentence Closing

> Chalksmith does not simply generate AI lessons; it helps schools preserve, review, improve, and share teacher expertise while giving administrators control over quality, privacy, and access.

## Product References

- [OER Commons Hubs](https://help.oercommons.org/support/solutions/folders/42000101795): Organization spaces, working groups, roles, and curated collections.
- [Canvas Commons Guide](https://community.canvaslms.com/html/assets/Canvas_Commons_Guide.pdf): Sharing resources with groups, institutions, and the public.
- [U.S. Department of Education AI Toolkit](https://eric.ed.gov/?id=ED661924): Safe, ethical, and equitable AI integration.
- [U.S. Department of Education Privacy and Education Technology](https://studentprivacy.ed.gov/privacy-and-education-technology): Privacy considerations for educational services.
- [W3C Media Accessibility](https://www.w3.org/WAI/media/av/): Accessibility requirements and practices for video and audio.
