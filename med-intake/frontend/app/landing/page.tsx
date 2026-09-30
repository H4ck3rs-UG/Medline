'use client';

import {HStack, LayoutContent, StackItem, VStack} from '@astryxdesign/core/Layout';
import {Heading, Text} from '@astryxdesign/core/Text';
import {Button} from '@astryxdesign/core/Button';
import {Card} from '@astryxdesign/core/Card';
import {Badge} from '@astryxdesign/core/Badge';
import {Banner} from '@astryxdesign/core/Banner';
import {Blockquote} from '@astryxdesign/core/Blockquote';
import {Divider} from '@astryxdesign/core/Divider';
import {StatusDot} from '@astryxdesign/core/StatusDot';
import {Token} from '@astryxdesign/core/Token';
import {Collapsible} from '@astryxdesign/core/Collapsible';
import {Center} from '@astryxdesign/core/Center';
import {MedLineWordmark} from './logo';
import {ChwDesk, Clinic, FeaturePhone, Listening, MapPin, Nurse, PersonCalling, Phone} from './art';

function Frame({children, label}: {children: React.ReactNode; label: string}) {
  return (
    <Card>
      <VStack gap={2}>
        <Text type="label" color="secondary">{label}</Text>
        <Center
          axis="both"
          style={{
            aspectRatio: '16/9',
            borderRadius: 'var(--radius-container)',
            backgroundColor: 'var(--color-background-muted)',
            boxShadow: 'var(--shadow-med)',
            overflow: 'hidden',
          }}>
          {children}
        </Center>
      </VStack>
    </Card>
  );
}

function MockIVR() {
  const lines = [
    ['MedLine', 'For English, press 1. Kwa Kiswahili, bonyeza 2…'],
    ['You', '1'],
    ['MedLine', 'Describe symptoms after the beep…'],
    ['You', '“Fever and cough for three days…”'],
    ['MedLine', 'Urgent. Ref MED-42 by SMS. Kawempe Health Centre, queue #3.'],
  ];
  return (
    <VStack gap={2} style={{padding: 'var(--spacing-4)', width: '100%'}}>
      {lines.map(([who, text], i) => (
        <HStack gap={2} vAlign="center" key={i}>
          <Token size="sm" color={who === 'You' ? 'default' : 'blue'} label={who} />
          <Text type="body">{text}</Text>
        </HStack>
      ))}
    </VStack>
  );
}

function MockQueue() {
  const rows = [
    ['error' as const, 'MED-42', 'Urgent · fever + cough', 'Kawempe · #3'],
    ['error' as const, 'MED-41', 'Emergency · chest pain', 'Mulago · #1'],
    ['success' as const, 'MED-40', 'Self-care · headache', 'Advice sent'],
  ];
  return (
    <VStack gap={2} style={{padding: 'var(--spacing-4)', width: '100%'}}>
      {rows.map(([v, ref, what, where]) => (
        <HStack gap={2} vAlign="center" key={ref as string}>
          <StatusDot variant={v as 'error' | 'success'} label={ref as string} />
          <StackItem size="fill">
            <Text type="body">{ref as string} — {what as string}</Text>
          </StackItem>
          <Text type="supporting" color="secondary">{where as string}</Text>
        </HStack>
      ))}
    </VStack>
  );
}

const STEPS = [
  {fig: <PersonCalling />, t: 'Patient calls in', d: 'Any phone — smartphone or feature phone. No app, no data.'},
  {fig: <Phone />, t: 'Picks a language', d: 'Keypress menu: English, Kiswahili, Luganda, Runyankole.'},
  {fig: <Listening />, t: 'Describes symptoms', d: 'Free speech where STT works, keypad menu where it doesn’t.'},
  {fig: <ChwDesk />, t: 'Rules engine tiers', d: 'Deterministic WHO/IMCI-style rules. Emergency, urgent, or self-care.'},
  {fig: <Clinic />, t: 'Routed to care', d: 'Self-care advice, CHW callback, or the nearest capable clinic.'},
  {fig: <Nurse />, t: 'Human closes loop', d: 'A health worker reviews, diagnoses, and closes the ticket.'},
];

const STRIP = ['Voice call in', 'AI understands', 'Rules decide', 'Human closes loop'];

const PILOT_TIERS = [
  {
    title: 'Pilot',
    desc: 'One facility, prove routing',
    price: 'Free',
    cta: 'Start a pilot',
    points: ['1 facility + queue', 'Voice intake line', 'EN + Kiswahili', 'Triage audit trail', 'CHW callback queue'],
  },
  {
    title: 'District',
    desc: 'Multi-facility catchment',
    price: 'Custom',
    cta: 'Call Medline AI',
    points: ['Up to 10 facilities', '4 languages + keypad', 'Live catchment map', 'Load + wait times', 'Follow-up chaining'],
  },
  {
    title: 'National',
    desc: 'Scale + oversight',
    price: 'Custom',
    cta: 'Contact us',
    points: ['Unlimited facilities', 'Custom integrations', 'Clinician review board', 'Analytics + reports', 'SLA uptime'],
  },
];

const FAQ = [
  {
    q: 'Does MedLine AI diagnose patients?',
    a: 'No. It tiers (emergency / urgent / self-care) and routes — to self-care advice, a health-worker callback, or the nearest capable clinic. Only qualified health workers diagnose and treat.',
  },
  {
    q: 'What phones does it work on?',
    a: 'Any phone. English and Kiswahili callers speak freely; Luganda and Runyankole callers use a keypress menu. No app, no data needed.',
  },
  {
    q: 'How long does a call take?',
    a: 'About 2.5 minutes on average: danger-sign questions, then duration / pregnancy / severity, then routing with an SMS reference like MED-42.',
  },
  {
    q: 'What happens when speech recognition fails?',
    a: 'Fail-safe: re-ask once, then switch to keypad questions. Three invalid keys means an incomplete report — routed urgent minimum, never self-care.',
  },
  {
    q: 'Can we pilot with one facility?',
    a: 'Yes. Start with one facility and its queue, prove routing, then scale to district level. Call +256 323 200 717.',
  },
];

export default function Landing() {
  return (
    <LayoutContent padding={4}>
      <VStack gap={4}>
        <HStack gap={2} vAlign="center">
          <StackItem size="fill"><MedLineWordmark /></StackItem>
          <Button label="Staff login" variant="secondary" size="sm" onClick={() => (window.location.href = '/login')} />
          <Button label="Open dashboard" variant="secondary" size="sm" onClick={() => (window.location.href = '/dashboard')} />
        </HStack>

        {/* 1. Hero */}
        <Card>
          <HStack gap={4} vAlign="center">
            <StackItem size="fill">
              <VStack gap={3}>
                <Heading level={1}>Every phone. Every language. The right care, every time.</Heading>
                <Text type="body" color="secondary">
                  MedLine AI is a voice-first medical intake and triage agent for Africa.
                  Patients call from any phone, describe symptoms in their language, and
                  get routed — like a support ticket — to self-care advice, a health-worker
                  callback, or the nearest clinic. Triage and routing, never diagnosis.
                </Text>
                <HStack gap={2}>
                  <Button label="See a live demo call" size="sm" onClick={() => (window.location.href = '/dashboard')} />
                  <Button label="Call MedLine AI" variant="secondary" size="sm" onClick={() => (window.location.href = 'tel:+256323200717')} />
                  <Button label="Read the research" variant="secondary" size="sm" onClick={() => (window.location.href = '/landing#proof')} />
                </HStack>
                <HStack gap={2} vAlign="center">
                  <Token size="sm" color="default" label="Works on feature phones" />
                  <Token size="sm" color="default" label="4 languages" />
                  <Token size="sm" color="default" label="No app needed" />
                </HStack>
                <Heading level={1}>
                  <a href="tel:+256323200717" style={{color: 'var(--color-accent)', textDecoration: 'none'}}>
                    +256 323 200 717
                  </a>
                </Heading>
              </VStack>
            </StackItem>
            <PersonCalling />
          </HStack>
        </Card>

        {/* Logo strip (ported from genesis trusted-companies) */}
        <Center axis="horizontal">
          <VStack gap={1} hAlign="center">
            <MedLineWordmark size={44} />
            <Text type="supporting" color="secondary">MedLine AI — voice-first triage for Africa</Text>
          </VStack>
        </Center>

        {/* 2. Problem */}
        <Heading level={2}>Clinics are full. Phones are everywhere.</Heading>
        <HStack gap={3}>
          {[
            {fig: <Nurse />, stat: '1 : 25,000', desc: 'Doctor-to-patient ratios in parts of sub-Saharan Africa fall far below the WHO benchmark of 1 : 1,000.'},
            {fig: <Phone />, stat: '90% mobile, ~40% smart', desc: 'Almost everyone can be reached by voice call. Smartphone-only health apps leave most patients out.'},
            {fig: <MapPin />, stat: 'Hours away', desc: 'Distance decides outcomes. Sending a patient to the wrong facility costs a day — or a life.'},
          ].map(c => (
            <StackItem size="fill" key={c.stat}>
              <Card>
                <VStack gap={2}>
                  {c.fig}
                  <Heading level={3}>{c.stat}</Heading>
                  <Text type="body" color="secondary">{c.desc}</Text>
                </VStack>
              </Card>
            </StackItem>
          ))}
        </HStack>

        {/* 3. Patient flow */}
        <Heading level={2}>From first ring to closed ticket</Heading>
        <HStack gap={3}>
          {STEPS.map((s, i) => (
            <StackItem size="fill" key={s.t}>
              <Card>
                <VStack gap={2}>
                  {s.fig}
                  <Text type="label" color="accent">Step {i + 1}</Text>
                  <Text type="label">{s.t}</Text>
                  <Text type="supporting" color="secondary">{s.d}</Text>
                </VStack>
              </Card>
            </StackItem>
          ))}
        </HStack>

        {/* 4. Screenshots */}
        <Heading level={2}>Built for the call and the clinic</Heading>
        <HStack gap={3}>
          <StackItem size="fill">
            <Frame label="Live call / IVR flow — 16:9"><MockIVR /></Frame>
          </StackItem>
          <StackItem size="fill">
            <Frame label="Clinic dashboard queue — 16:9"><MockQueue /></Frame>
          </StackItem>
        </HStack>

        {/* 5. How it works strip */}
        <Card>
          <VStack gap={2}>
            <Heading level={3}>How it works</Heading>
            <HStack gap={2} vAlign="center">
              {STRIP.map((s, i) => (
                <HStack gap={2} vAlign="center" key={s}>
                  <StackItem size="fill">
                    <Text type="label">{i + 1}. {s}</Text>
                  </StackItem>
                </HStack>
              ))}
            </HStack>
            <Banner status="info" title="Triage and routing — not diagnosis">
              MedLine AI sorts and routes patients. Only qualified health workers diagnose and treat.
            </Banner>
          </VStack>
        </Card>

        {/* 6. Languages */}
        <Card>
          <HStack gap={4} vAlign="center">
            <FeaturePhone />
            <StackItem size="fill">
              <VStack gap={2}>
                <Heading level={2}>Speaks your patient’s language</Heading>
                <Text type="body" color="secondary">
                  English and Kiswahili callers speak freely. Luganda and Runyankole
                  callers use a keypress menu — built for languages where speech
                  recognition isn’t reliable yet. Nobody gets a beep-and-hangup.
                </Text>
                <HStack gap={2}>
                  <Badge label="English" variant="info" />
                  <Badge label="Kiswahili" variant="info" />
                  <Badge label="Luganda · keypad" variant="neutral" />
                  <Badge label="Runyankole · keypad" variant="neutral" />
                </HStack>
              </VStack>
            </StackItem>
          </HStack>
        </Card>

        {/* 7. Social proof */}
        <Heading level={2} id="proof">Why now</Heading>
        <Blockquote cite="World Health Organization">
          Africa carries 24% of the global disease burden with 3% of the world’s health workers.
        </Blockquote>
        <HStack gap={3}>
          <StackItem size="fill">
            <Card>
              <VStack gap={1}>
                <Heading level={3}>Mobile-first by necessity</Heading>
                <Text type="body" color="secondary">Voice calls reach patients that apps never will — including every feature phone.</Text>
              </VStack>
            </Card>
          </StackItem>
          <StackItem size="fill">
            <Card>
              <VStack gap={1}>
                <Heading level={3}>Category momentum</Heading>
                <Text type="body" color="secondary">Major funders back AI triage for African clinics — including a $50M Gates Foundation + OpenAI clinic-AI initiative. MedLine AI is an independent product in that same category (no affiliation claimed).</Text>
              </VStack>
            </Card>
          </StackItem>
        </HStack>

        {/* 8. Pilot pricing (ported from genesis pricing-plans) */}
        <Heading level={2}>Pilot pricing</Heading>
        <Text type="body" color="secondary">Start with one facility. Scale when routing proves out.</Text>
        <HStack gap={3}>
          {PILOT_TIERS.map(t => (
            <StackItem size="fill" key={t.title}>
              <Card>
                <VStack gap={2}>
                  <Token size="sm" color="default" label={t.title} />
                  <Heading level={3}>{t.price}</Heading>
                  <Text type="body" color="secondary">{t.desc}</Text>
                  <Divider />
                  <VStack gap={1}>
                    {t.points.map(p => (
                      <Text type="body" key={p}>· {p}</Text>
                    ))}
                  </VStack>
                  <Button
                    label={t.cta}
                    size="sm"
                    variant={t.title === 'District' ? 'primary' : 'secondary'}
                    onClick={() => (window.location.href = t.title === 'District' ? 'tel:+256323200717' : '/dashboard')}
                  />
                </VStack>
              </Card>
            </StackItem>
          ))}
        </HStack>

        {/* 9. FAQ (ported from genesis faq-section, Medline content) */}
        <Heading level={2}>FAQ</Heading>
        <VStack gap={2}>
          {FAQ.map(f => (
            <Collapsible key={f.q} trigger={f.q} defaultIsOpen={false}>
              <Text type="body" color="secondary">{f.a}</Text>
            </Collapsible>
          ))}
        </VStack>

        {/* 10. Footer CTA + nav */}
        <Card>
          <VStack gap={3}>
            <Heading level={2}>Bring MedLine AI to your district</Heading>
            <Text type="body" color="secondary">Pilot with one facility. Route every call to the right care.</Text>
            <Heading level={1}>
              <a href="tel:+256323200717" style={{color: 'var(--color-accent)', textDecoration: 'none'}}>
                +256 323 200 717
              </a>
            </Heading>
            <HStack gap={2}>
              <Button label="Start a pilot" size="sm" onClick={() => (window.location.href = '/dashboard')} />
              <Button label="Call +256 323 200 717" variant="secondary" size="sm" onClick={() => (window.location.href = 'tel:+256323200717')} />
            </HStack>
          </VStack>
        </Card>
        <Divider />
        <HStack gap={3} vAlign="center">
          <StackItem size="fill"><MedLineWordmark size={28} /></StackItem>
          <Text type="supporting" color="secondary">Dashboard</Text>
          <Text type="supporting" color="secondary">Research</Text>
          <Text type="supporting" color="secondary">Contact</Text>
          <Text type="supporting" color="secondary">Demo content — clinician approval required before real-world use.</Text>
        </HStack>
      </VStack>
    </LayoutContent>
  );
}
