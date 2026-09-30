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
import {MedLineWordmark} from './logo';
import {ChwDesk, Clinic, FeaturePhone, Listening, MapPin, Nurse, PersonCalling, Phone} from './art';

function Frame({children, ratio = '16/9', label}: {children: React.ReactNode; ratio?: string; label: string}) {
  return (
    <Card>
      <VStack gap={2}>
        <Text type="label" color="secondary">{label}</Text>
        <div
          style={{
            aspectRatio: ratio,
            borderRadius: 'var(--radius-container)',
            backgroundColor: 'var(--color-background-muted)',
            boxShadow: 'var(--shadow-med)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
          }}>
          {children}
        </div>
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

export default function Landing() {
  return (
    <LayoutContent padding={4}>
      <VStack gap={4}>
        <HStack gap={2} vAlign="center">
          <StackItem size="fill"><MedLineWordmark /></StackItem>
          <Badge label="Pilot live in Kampala" variant="success" />
          <Button label="Open dashboard" variant="secondary" size="sm" onClick={() => (window.location.href = '/')} />
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
                  <Button label="See a live demo call" size="sm" onClick={() => (window.location.href = '/')} />
                  <Button label="Read the research" variant="secondary" size="sm" onClick={() => (window.location.href = '/landing#proof')} />
                </HStack>
                <HStack gap={2} vAlign="center">
                  <Token size="sm" color="default" label="Works on feature phones" />
                  <Token size="sm" color="default" label="4 languages" />
                  <Token size="sm" color="default" label="No app needed" />
                </HStack>
              </VStack>
            </StackItem>
            <PersonCalling />
          </HStack>
        </Card>

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
            <Frame label="Live call / IVR flow — 16:9" ratio="16/9"><MockIVR /></Frame>
          </StackItem>
          <StackItem size="fill">
            <Frame label="Clinic dashboard queue — 16:9" ratio="16/9"><MockQueue /></Frame>
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

        {/* 8. Footer CTA + nav */}
        <Card>
          <VStack gap={3}>
            <Heading level={2}>Bring MedLine AI to your district</Heading>
            <Text type="body" color="secondary">Pilot with one facility. Route every call to the right care.</Text>
            <HStack gap={2}>
              <Button label="Start a pilot" size="sm" onClick={() => (window.location.href = '/')} />
              <Button label="Talk to us" variant="secondary" size="sm" onClick={() => (window.location.href = '/')} />
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
