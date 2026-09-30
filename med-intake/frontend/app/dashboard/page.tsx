'use client';

import {useEffect, useMemo, useState, type CSSProperties} from 'react';

import {
  HStack,
  Layout,
  LayoutContent,
  LayoutHeader,
  StackItem,
  VStack,
} from '@astryxdesign/core/Layout';
import {ResizeHandle, useResizable} from '@astryxdesign/core/Resizable';
import {LayoutPanel} from '@astryxdesign/core/Layout';
import {Heading, Text} from '@astryxdesign/core/Text';
import {Button} from '@astryxdesign/core/Button';
import {Icon} from '@astryxdesign/core/Icon';
import {Divider} from '@astryxdesign/core/Divider';
import {EmptyState} from '@astryxdesign/core/EmptyState';
import {List, ListItem} from '@astryxdesign/core/List';
import {MetadataList, MetadataListItem} from '@astryxdesign/core/MetadataList';
import {
  SegmentedControl,
  SegmentedControlItem,
} from '@astryxdesign/core/SegmentedControl';
import {StatusDot} from '@astryxdesign/core/StatusDot';
import {Token} from '@astryxdesign/core/Token';
import {TextArea} from '@astryxdesign/core/TextArea';
import {Collapsible} from '@astryxdesign/core/Collapsible';
import {ProgressBar} from '@astryxdesign/core/ProgressBar';
import {AppShell} from '@astryxdesign/core/AppShell';
import {
  SideNav,
  SideNavHeading,
  SideNavItem,
  SideNavSection,
} from '@astryxdesign/core/SideNav';
import {Card} from '@astryxdesign/core/Card';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {useMediaQuery} from '@astryxdesign/core/hooks';
import {BellAlertIcon, BuildingOfficeIcon, ChartBarIcon, Cog6ToothIcon, InboxIcon} from '@heroicons/react/24/outline';
import ModeToggle from '../components/mode-toggle';
import {
  STRINGS,
  UI_LANGS,
  ageGroupLabel,
  facilityKindLabel,
  callLangLabel,
  fmt,
  sexLabel,
  statusLabel,
  symptomsLabel,
  tierLabel,
  unknownLabel,
  type UiLang,
} from '../i18n';

const API = process.env.NEXT_PUBLIC_API || 'http://localhost:8000';
const LANG_KEY = 'dashboard-lang';

const styles: Record<string, CSSProperties> = {
  contentFill: {height: '100%', minHeight: 0},
  rows: {overflowY: 'auto', minHeight: 0},
  inspector: {padding: 'var(--spacing-4)', height: '100%', overflowY: 'auto'},
  groupHeader: {
    padding: 'var(--spacing-2) var(--spacing-3)',
    backgroundColor: 'var(--color-background-muted)',
  },
};

interface Ticket extends Record<string, unknown> {
  id: number;
  caller: string;
  lang: string;
  symptoms: string;
  tier: 'emergency' | 'urgent' | 'self_care';
  reason: string;
  confidence: number;
  status: string;
  name: string;
  age: number;
  age_band: string;
  sex: string;
  village: string;
  diagnosis: string;
  diagnosed_by: string;
  transcript: string;
  summary: string;
  reference: string;
  parent_id: number;
  facility_id: number;
  queue_pos: number;
  follow_ups?: Ticket[];
}

interface Facility {
  id: number;
  name: string;
  kind: string;
  lat: number;
  lng: number;
  capabilities: string[];
  slots: number;
  load: number;
  free: number;
  wait_min: number;
}

interface QueueEntry {
  id: number;
  reference: string;
  tier: string;
  summary: string;
  position: number;
  wait_min: number;
}

interface Stats {
  total: number;
  open: number;
  by_tier: Record<string, number>;
  by_sex: Record<string, number>;
  by_age_band: Record<string, number>;
  by_lang: Record<string, number>;
  by_village: Record<string, number>;
}

const TIER_DOT = {emergency: 'error', urgent: 'warning', self_care: 'success'} as const;
const TIER_ORDER = ['emergency', 'urgent', 'self_care'] as const;

function TicketRows({
  tickets,
  selectedId,
  onSelect,
  lang,
}: {
  tickets: Ticket[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  lang: UiLang;
}) {
  const s = STRINGS[lang];
  const groups = TIER_ORDER.map(tier => ({
    tier,
    items: tickets.filter(t => t.tier === tier),
  })).filter(g => g.items.length > 0);

  if (groups.length === 0) {
    return (
      <EmptyState
        title={s.empty}
        description=""
        icon={<Icon icon={BellAlertIcon} size="lg" />}
      />
    );
  }

  return (
    <VStack gap={0}>
      {groups.map(group => (
        <VStack gap={0} key={group.tier}>
          <HStack gap={2} vAlign="center" style={styles.groupHeader}>
            <StatusDot variant={TIER_DOT[group.tier]} label={tierLabel(group.tier, lang)} />
            <Text type="label" color="secondary">
              {tierLabel(group.tier, lang)}
            </Text>
            <Text type="supporting" color="secondary">
              {group.items.length}
            </Text>
          </HStack>
          <List density="compact" hasDividers>
            {group.items.map(t => (
              <ListItem
                key={t.id}
                label={`${t.reference || 'MED-' + t.id} · ${t.caller || s.unknownCaller}`}
                description={`${symptomsLabel(t.symptoms, lang) || s.noSymptoms} · ${t.reason}`}
                startContent={
                  <StatusDot
                    variant={TIER_DOT[t.tier]}
                    label={tierLabel(t.tier, lang)}
                    isPulsing={t.tier === 'emergency' && t.status === 'open'}
                  />
                }
                endContent={
                  <Token
                    size="sm"
                    color={t.status === 'open' ? 'blue' : 'gray'}
                    label={statusLabel(t.status, lang)}
                  />
                }
                onClick={() => onSelect(t.id)}
                isSelected={t.id === selectedId}
              />
            ))}
          </List>
        </VStack>
      ))}
    </VStack>
  );
}

function TicketInspector({
  ticket,
  lang,
  onClose,
  onDiagnose,
  facilities,
  tickets,
  onSelect,
}: {
  ticket: Ticket;
  lang: UiLang;
  onClose: (id: number) => void;
  onDiagnose: (id: number, diagnosis: string, andClose?: boolean) => void;
  facilities: Facility[];
  tickets: Ticket[];
  onSelect: (id: number) => void;
}) {
  const s = STRINGS[lang];
  const [diagnosis, setDiagnosis] = useState(ticket.diagnosis || '');
  const [detail, setDetail] = useState<Ticket | null>(null);
  useEffect(() => {
    setDiagnosis(ticket.diagnosis || '');
    setDetail(null);
    fetch(`${API}/api/tickets/ref/${ticket.reference || 'MED-' + ticket.id}`)
      .then(r => (r.ok ? r.json() : null))
      .then(setDetail)
      .catch(() => {});
  }, [ticket.id]);
  const fac = facilities.find(f => f.id === ticket.facility_id);
  const chain = detail?.follow_ups ?? [];
  const shown = detail ?? ticket;
  return (
    <VStack gap={4} style={styles.inspector}>
      <VStack gap={2}>
        <HStack gap={2} vAlign="center">
          <StatusDot variant={TIER_DOT[ticket.tier]} label={tierLabel(ticket.tier, lang)} />
          <Token size="sm" color="purple" label={ticket.reference || `MED-${ticket.id}`} />
          <Token
            size="sm"
            color={ticket.status === 'open' ? 'blue' : 'gray'}
            label={statusLabel(ticket.status, lang)}
          />
        </HStack>
        <Heading level={2}>{tierLabel(ticket.tier, lang)}</Heading>
        <Text type="supporting" color="secondary">
          {fac
            ? fmt(ticket.queue_pos ? s.routedQueue : s.routed, {name: fac.name, n: ticket.queue_pos})
            : s.notRouted}
          {ticket.parent_id > 0 ? fmt(s.followUpOf, {ref: `MED-${ticket.parent_id}`}) : ''}
        </Text>
      </VStack>

      {chain.length > 0 && (
        <>
          <Divider />
          <VStack gap={2}>
            <Heading level={3}>{fmt(s.patientMap, {n: chain.length + 1})}</Heading>
            <List density="compact" hasDividers>
              {[{...ticket, follow_ups: undefined}, ...chain].map(t => (
                <ListItem
                  key={t.id}
                  label={`${t.reference || 'MED-' + t.id} · ${tierLabel(t.tier, lang)}`}
                  description={t.summary || symptomsLabel(t.symptoms, lang)}
                  startContent={
                    <StatusDot
                      variant={TIER_DOT[t.tier as keyof typeof TIER_DOT] ?? 'neutral'}
                      label={tierLabel(t.tier, lang)}
                    />
                  }
                  onClick={() => t.id !== ticket.id && onSelect(t.id)}
                  isSelected={t.id === ticket.id}
                />
              ))}
            </List>
          </VStack>
        </>
      )}

      <Divider />

      <VStack gap={2}>
        <Heading level={3}>{s.callSummary}</Heading>
        <Text type="body">
          {ticket.summary ||
            `${tierLabel(ticket.tier, lang)}: ${symptomsLabel(ticket.symptoms, lang) || s.noSymptoms}.`}
        </Text>
        {ticket.transcript ? (
          <Collapsible trigger={s.viewTranscript} defaultIsOpen={false}>
            <Text type="body" color="secondary">
              {ticket.transcript}
            </Text>
          </Collapsible>
        ) : (
          <Text type="supporting" color="secondary">
            {s.noTranscript}
          </Text>
        )}
      </VStack>

      <Divider />

      <VStack gap={2}>
        <Heading level={3}>{s.doctorDiagnosis}</Heading>
        {ticket.diagnosis ? (
          <VStack gap={1}>
            <Text type="body">{ticket.diagnosis}</Text>
          </VStack>
        ) : null}
        {ticket.status === 'open' && (
          <VStack gap={2}>
            <TextArea
              label={s.diagnosis}
              placeholder={s.diagnosisPlaceholder}
              value={diagnosis}
              onChange={setDiagnosis}
            />
            <HStack gap={2}>
              <Button
                label={s.saveDiagnosis}
                variant="secondary"
                size="sm"
                onClick={() => onDiagnose(ticket.id, diagnosis)}
              />
              <Button
                label={s.closeWithDiagnosis}
                size="sm"
                onClick={() => onDiagnose(ticket.id, diagnosis, true)}
              />
            </HStack>
          </VStack>
        )}
      </VStack>

      {ticket.status === 'open' && (
        <HStack gap={2}>
          <Button label={s.close} variant="secondary" size="sm" onClick={() => onClose(ticket.id)} />
        </HStack>
      )}

      <Divider />

      <VStack gap={2}>
        <Heading level={3}>{s.healthProfile}</Heading>
      </VStack>
      <MetadataList columns="single" label={{position: 'start', width: 96}}>
        <MetadataListItem label={s.name}>
          <Text type="body">{ticket.name || '—'}</Text>
        </MetadataListItem>
        <MetadataListItem label={s.ageGroup}>
          <Text type="body">
            {ticket.age_band && ticket.age_band !== 'unknown' ? ageGroupLabel(ticket.age_band, lang) : '—'}
          </Text>
        </MetadataListItem>
        <MetadataListItem label={s.sex}>
          <Text type="body">{ticket.sex ? sexLabel(ticket.sex, lang) : '—'}</Text>
        </MetadataListItem>
        <MetadataListItem label={s.village}>
          <Text type="body">{ticket.village || '—'}</Text>
        </MetadataListItem>
        <MetadataListItem label={s.caller}>
          <Text type="body">{ticket.caller || '—'}</Text>
        </MetadataListItem>
        <MetadataListItem label={s.language}>
          <Text type="body">{callLangLabel(ticket.lang, lang)}</Text>
        </MetadataListItem>
        <MetadataListItem label={s.symptoms}>
          <Text type="body">{symptomsLabel(ticket.symptoms, lang) || '—'}</Text>
        </MetadataListItem>
        <MetadataListItem label={s.reason}>
          <Text type="body">{ticket.reason}</Text>
          {lang !== 'en' && (
            <Text type="supporting" color="secondary">
              {s.ruleNote}
            </Text>
          )}
        </MetadataListItem>
        <MetadataListItem label={s.confidence}>
          <Text type="body">{ticket.confidence > 0 ? `${ticket.confidence}%` : '—'}</Text>
        </MetadataListItem>
      </MetadataList>
    </VStack>
  );
}

function StatsSidebar({stats, lang}: {stats: Stats | null; lang: UiLang}) {
  const s = STRINGS[lang];
  const total = stats?.total ?? 0;
  const bar = (
    label: string,
    n: number,
    variant: 'error' | 'warning' | 'success' | 'accent' | 'neutral' = 'accent',
  ) => (
    <VStack gap={1} key={label}>
      <HStack gap={2} vAlign="center">
        <StackItem size="fill">
          <Text type="body" color="secondary">
            {label}
          </Text>
        </StackItem>
        <Text type="label">{n}</Text>
      </HStack>
      <ProgressBar
        label={`${label} ${n} of ${total}`}
        value={total > 0 ? n : 0}
        max={Math.max(total, 1)}
        variant={variant}
        isLabelHidden
        hasValueLabel={false}
      />
    </VStack>
  );
  const TIER_VARIANT = {emergency: 'error', urgent: 'warning', self_care: 'success'} as const;
  const section = (
    title: string,
    obj: Record<string, number> | undefined,
    labelOf: (k: string) => string,
    variantOf?: (k: string) => 'error' | 'warning' | 'success' | 'accent' | 'neutral',
  ) => (
    <VStack gap={2} key={title}>
      <Text type="label" color="secondary">
        {title}
      </Text>
      {obj && Object.keys(obj).length > 0 ? (
        Object.entries(obj)
          .sort((a, b) => b[1] - a[1])
          .map(([k, v]) => bar(labelOf(k), v, variantOf?.(k) ?? 'accent'))
      ) : (
        <Text type="supporting" color="secondary">
          —
        </Text>
      )}
    </VStack>
  );
  return (
    <VStack gap={4} style={styles.inspector}>
      <VStack gap={1}>
        <Heading level={3}>{s.overview}</Heading>
        <Text type="supporting" color="secondary">
          {stats ? fmt(s.openOfTotal, {open: stats.open, total: stats.total}) : s.loading}
        </Text>
      </VStack>
      <Divider />
      {section(
        s.byTier,
        stats?.by_tier,
        k => tierLabel(k, lang),
        k => TIER_VARIANT[k as keyof typeof TIER_VARIANT] ?? 'accent',
      )}
      <Divider />
      {section(s.bySex, stats?.by_sex, k => sexLabel(k, lang))}
      <Divider />
      {section(s.byAge, stats?.by_age_band, k => ageGroupLabel(k, lang))}
      <Divider />
      {section(s.byLanguage, stats?.by_lang, k => callLangLabel(k, lang))}
      <Divider />
      {section(s.byVillage, stats?.by_village, k => unknownLabel(k, lang), () => 'neutral')}
    </VStack>
  );
}

const CHART_FILL: Record<string, string> = {
  emergency: 'var(--color-error)',
  urgent: 'var(--color-warning)',
  self_care: 'var(--color-success)',
  M: 'var(--color-text-blue)',
  F: 'var(--color-text-purple)',
};

function KpiRow({stats, lang}: {stats: Stats | null; lang: UiLang}) {
  const s = STRINGS[lang];
  const kpis = [
    {label: s.totalTickets, value: stats?.total ?? 0},
    {label: s.openTickets, value: stats?.open ?? 0},
    ...TIER_ORDER.map(tier => ({label: tierLabel(tier, lang), value: stats?.by_tier?.[tier] ?? 0})),
  ];
  return (
    <HStack gap={3}>
      {kpis.map(k => (
        <StackItem key={k.label} size="fill">
          <Card>
            <VStack gap={1}>
              <Text type="supporting" color="secondary">
                {k.label}
              </Text>
              <Heading level={2}>{k.value}</Heading>
            </VStack>
          </Card>
        </StackItem>
      ))}
    </HStack>
  );
}

function TierChart({stats, lang}: {stats: Stats | null; lang: UiLang}) {
  const data = TIER_ORDER.map(tier => ({
    key: tier,
    name: tierLabel(tier, lang),
    count: stats?.by_tier?.[tier] ?? 0,
  }));
  return (
    <Card>
      <VStack gap={3}>
        <Heading level={3}>{STRINGS[lang].tierChart}</Heading>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data}>
            <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" />
            <XAxis dataKey="name" stroke="var(--color-text-secondary)" tickLine={false} />
            <YAxis
              allowDecimals={false}
              stroke="var(--color-text-secondary)"
              tickLine={false}
              width={32}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--color-background-popover)',
                borderColor: 'var(--color-border)',
                borderRadius: 'var(--radius-element)',
              }}
            />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {data.map(d => (
                <Cell key={d.key} fill={CHART_FILL[d.key]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </VStack>
    </Card>
  );
}

function AgeChart({stats, lang}: {stats: Stats | null; lang: UiLang}) {
  const data = Object.entries(stats?.by_age_band ?? {})
    .sort((a, b) => b[1] - a[1])
    .map(([key, count]) => ({name: ageGroupLabel(key, lang), count}));
  return (
    <Card>
      <VStack gap={3}>
        <Heading level={3}>{STRINGS[lang].ageChart}</Heading>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data}>
            <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" />
            <XAxis dataKey="name" stroke="var(--color-text-secondary)" tickLine={false} />
            <YAxis
              allowDecimals={false}
              stroke="var(--color-text-secondary)"
              tickLine={false}
              width={32}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--color-background-popover)',
                borderColor: 'var(--color-border)',
                borderRadius: 'var(--radius-element)',
              }}
            />
            <Bar dataKey="count" fill="var(--color-accent)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </VStack>
    </Card>
  );
}

function SexChart({stats, lang}: {stats: Stats | null; lang: UiLang}) {
  const data = Object.entries(stats?.by_sex ?? {}).map(([key, value]) => ({
    key,
    name: sexLabel(key, lang),
    value,
  }));
  return (
    <Card>
      <VStack gap={3}>
        <Heading level={3}>{STRINGS[lang].sexChart}</Heading>
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={48} outerRadius={80}>
              {data.map(d => (
                <Cell key={d.key} fill={CHART_FILL[d.key] ?? 'var(--color-neutral)'} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--color-background-popover)',
                borderColor: 'var(--color-border)',
                borderRadius: 'var(--radius-element)',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </VStack>
    </Card>
  );
}

type View = 'dashboard' | 'queue' | 'facilities' | 'settings';

const TIER_SVG_FILL: Record<string, string> = {
  emergency: 'var(--color-error)',
  urgent: 'var(--color-warning)',
  self_care: 'var(--color-success)',
};

function FacilityMap({
  facilities,
  tickets,
  lang,
}: {
  facilities: Facility[];
  tickets: Ticket[];
  lang: UiLang;
}) {
  const s = STRINGS[lang];
  const LAT0 = 0.28, LAT1 = 0.39, LNG0 = 32.54, LNG1 = 32.62, W = 600, H = 420;
  const X = (lng: number) => ((lng - LNG0) / (LNG1 - LNG0)) * W;
  const Y = (lat: number) => H - ((lat - LAT0) / (LAT1 - LAT0)) * H;
  const jitter = (id: number, salt: number) => ((id * 37 + salt * 11) % 17) - 8;
  return (
    <Card>
      <VStack gap={3}>
        <HStack gap={2} vAlign="center">
          <StackItem size="fill">
            <Heading level={3}>{s.catchmentMap}</Heading>
          </StackItem>
          <HStack gap={2} vAlign="center">
            {(Object.keys(TIER_SVG_FILL) as string[]).map(t => (
              <HStack gap={1} vAlign="center" key={t}>
                <svg width="10" height="10" aria-hidden="true">
                  <circle cx="5" cy="5" r="4" fill={TIER_SVG_FILL[t]} />
                </svg>
                <Text type="supporting" color="secondary">
                  {tierLabel(t, lang)}
                </Text>
              </HStack>
            ))}
          </HStack>
        </HStack>
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={s.mapLabel}>
          <rect x="0" y="0" width={W} height={H} fill="var(--color-background-muted)" rx="8" />
          {facilities.map(f => (
            <g key={f.id}>
              <rect
                x={X(f.lng) - 8}
                y={Y(f.lat) - 8}
                width="16"
                height="16"
                rx="3"
                fill="var(--color-accent)"
                stroke="var(--color-background-surface)"
                strokeWidth="2"
              />
              <text x={X(f.lng) + 12} y={Y(f.lat) + 4} fontSize="11" fill="var(--color-text-primary)">
                {f.name} ({f.load}/{f.slots})
              </text>
            </g>
          ))}
          {tickets
            .filter(t => t.status === 'open' && t.facility_id > 0)
            .map(t => {
              const f = facilities.find(x => x.id === t.facility_id);
              if (!f) return null;
              return (
                <circle
                  key={t.id}
                  cx={X(f.lng) + jitter(t.id, 1)}
                  cy={Y(f.lat) + jitter(t.id, 2)}
                  r={t.tier === 'emergency' ? 6 : 4}
                  fill={TIER_SVG_FILL[t.tier] ?? 'var(--color-neutral)'}
                >
                  <title>{`${t.reference}: ${t.summary}`}</title>
                </circle>
              );
            })}
        </svg>
        <Text type="supporting" color="secondary">
          {s.mapNote}
        </Text>
      </VStack>
    </Card>
  );
}

function FacilityCards({
  facilities,
  queues,
  onSeed,
  lang,
}: {
  facilities: Facility[];
  queues: Record<string, {facility: Facility; queue: QueueEntry[]}>;
  onSeed: () => void;
  lang: UiLang;
}) {
  const s = STRINGS[lang];
  return (
    <VStack gap={3}>
      <HStack gap={2} vAlign="center">
        <StackItem size="fill">
          <Heading level={3}>{s.facilitiesQueues}</Heading>
        </StackItem>
        <Button label={s.seedSim} variant="secondary" size="sm" onClick={onSeed} />
      </HStack>
      <HStack gap={3}>
        {facilities.map(f => (
          <StackItem size="fill" key={f.id}>
            <Card>
              <VStack gap={2}>
                <HStack gap={2} vAlign="center">
                  <StackItem size="fill">
                    <Text type="label">{f.name}</Text>
                  </StackItem>
                  <Token size="sm" color="default" label={facilityKindLabel(f.kind, lang)} />
                </HStack>
                <Text type="supporting" color="secondary">
                  {fmt(s.queued, {load: f.load, slots: f.slots, wait: f.wait_min})}
                </Text>
                <ProgressBar
                  label={fmt(s.facilityLoad, {name: f.name})}
                  value={f.load}
                  max={Math.max(f.slots, 1)}
                  variant={f.load >= f.slots ? 'error' : f.load / Math.max(f.slots, 1) > 0.7 ? 'warning' : 'success'}
                  isLabelHidden
                />
                <VStack gap={1}>
                  {(queues[String(f.id)]?.queue ?? []).slice(0, 5).map(q => (
                    <HStack gap={2} vAlign="center" key={q.id}>
                      <StatusDot
                        variant={q.tier === 'emergency' ? 'error' : q.tier === 'urgent' ? 'warning' : 'success'}
                        label={tierLabel(q.tier, lang)}
                      />
                      <StackItem size="fill">
                        <Text type="body">
                          #{q.position} {q.reference}
                        </Text>
                      </StackItem>
                      <Text type="supporting" color="secondary">
                        ~{q.wait_min}m
                      </Text>
                    </HStack>
                  ))}
                  {(queues[String(f.id)]?.queue ?? []).length === 0 && (
                    <Text type="supporting" color="secondary">
                      {s.queueEmpty}
                    </Text>
                  )}
                </VStack>
              </VStack>
            </Card>
          </StackItem>
        ))}
      </HStack>
    </VStack>
  );
}

export default function Page() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [queues, setQueues] = useState<Record<string, {facility: Facility; queue: QueueEntry[]}>>({});
  const [tierFilter, setTierFilter] = useState('all');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [lang, setLang] = useState<UiLang>('en');
  const [sideCollapsed, setSideCollapsed] = useState(false);
  const [view, setView] = useState<View>('dashboard');

  useEffect(() => {
    try {
      const v = localStorage.getItem(LANG_KEY);
      if (v === 'en' || v === 'sw') setLang(v);
    } catch {}
  }, []);
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const load = () =>
    fetch(`${API}/api/tickets`)
      .then(r => r.json())
      .then((rows: Ticket[]) => {
        setTickets(rows);
        setSelectedId(prev => prev ?? rows[0]?.id ?? null);
      })
      .catch(() => {});
  const loadStats = () =>
    fetch(`${API}/api/stats`).then(r => r.json()).then(setStats).catch(() => {});
  const loadFacilities = () =>
    fetch(`${API}/api/facilities`).then(r => r.json()).then(setFacilities).catch(() => {});
  const loadQueues = () =>
    fetch(`${API}/api/queues`).then(r => r.json()).then(setQueues).catch(() => {});
  const seedSim = () =>
    fetch(`${API}/api/sim/seed?n=24`, {method: 'POST'})
      .then(() => {
        load();
        loadStats();
        loadFacilities();
        loadQueues();
      })
      .catch(() => {});

  useEffect(() => {
    load();
    loadStats();
    loadFacilities();
    loadQueues();
    const i = setInterval(() => {
      load();
      loadStats();
      loadFacilities();
      loadQueues();
    }, 3000);
    return () => clearInterval(i);
  }, []);

  const refreshAll = () => {
    load();
    loadStats();
    loadFacilities();
    loadQueues();
  };

  const close = (id: number) =>
    fetch(`${API}/api/tickets/${id}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({status: 'closed'}),
    }).then(refreshAll);

  const diagnose = (id: number, diagnosis: string, andClose = false) =>
    fetch(`${API}/api/tickets/${id}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        status: andClose ? 'closed' : 'open',
        diagnosis,
      }),
    }).then(refreshAll);

  const isNarrow = useMediaQuery('(max-width: 1024px)');
  const inspectorPanel = useResizable({defaultSize: 380, minSize: 320, maxSize: 480});

  const visible = useMemo(
    () => (tierFilter === 'all' ? tickets : tickets.filter(t => t.tier === tierFilter)),
    [tickets, tierFilter],
  );
  const selected = visible.find(t => t.id === selectedId) ?? null;
  const openCount = tickets.filter(t => t.status === 'open').length;
  const s = STRINGS[lang];
  const pickLang = (v: string) => {
    setLang(v as UiLang);
    try {
      localStorage.setItem(LANG_KEY, v);
    } catch {}
  };
  const langSwitch = (
    <HStack gap={2} vAlign="center">
      <SegmentedControl label={s.language} value={lang} onChange={pickLang} size="sm">
        {(Object.keys(UI_LANGS) as UiLang[]).map(l => (
          <SegmentedControlItem key={l} label={UI_LANGS[l]} value={l} />
        ))}
      </SegmentedControl>
      <ModeToggle />
    </HStack>
  );

  const queue = (
    <Layout
      height="fill"
      start={
        isNarrow || sideCollapsed ? undefined : (
          <LayoutPanel width={280} padding={0} label={s.populationStats} hasDivider>
            <StatsSidebar stats={stats} lang={lang} />
          </LayoutPanel>
        )
      }
      header={
        <LayoutHeader hasDivider>
          <HStack gap={3} vAlign="center">
            {!isNarrow && (
              <Button
                label={sideCollapsed ? s.showStats : s.hideStats}
                variant="secondary"
                size="sm"
                onClick={() => setSideCollapsed(v => !v)}
              />
            )}
            <StackItem size="fill">
              <HStack gap={2} vAlign="center">
                <Heading level={1}>{s.title}</Heading>
                <Text type="supporting" color="secondary">
                  {fmt(s.openCount, {n: openCount})}
                </Text>
              </HStack>
            </StackItem>
            <SegmentedControl
              label={s.filterByTier}
              value={tierFilter}
              onChange={setTierFilter}
              size="sm">
              <SegmentedControlItem label={s.all} value="all" />
              {TIER_ORDER.map(tier => (
                <SegmentedControlItem key={tier} label={tierLabel(tier, lang)} value={tier} />
              ))}
            </SegmentedControl>
            {langSwitch}
          </HStack>
        </LayoutHeader>
      }
      content={
        <LayoutContent padding={0}>
          <VStack gap={0} style={styles.contentFill}>
            <StackItem size="fill" style={styles.rows}>
              <TicketRows
                tickets={visible}
                selectedId={selected?.id ?? null}
                onSelect={setSelectedId}
                lang={lang}
              />
            </StackItem>
          </VStack>
        </LayoutContent>
      }
      end={
        isNarrow ? undefined : (
          <>
            <ResizeHandle
              direction="horizontal"
              hasDivider
              isAlwaysVisible={false}
              resizable={inspectorPanel.props}
              label={s.resizeInspector}
            />
            <LayoutPanel width={inspectorPanel.size} padding={0} label={s.ticketDetails}>
              {selected ? (
                <TicketInspector ticket={selected} lang={lang} onClose={close} onDiagnose={diagnose} facilities={facilities} tickets={tickets} onSelect={setSelectedId} />
              ) : (
                <EmptyState
                  title={s.noTicketSelected}
                  description={s.selectTicket}
                  icon={<Icon icon={BellAlertIcon} size="lg" />}
                  isCompact
                />
              )}
            </LayoutPanel>
          </>
        )
      }
    />
  );

  return (
    <AppShell
      height="fill"
      contentPadding={0}
      sideNav={
        <SideNav
          aria-label={s.navLabel}
          collapsible={isNarrow ? false : true}
          header={
            <SideNavHeading
              icon={<img src="/assets/slogo.png" alt="MedLine AI" width={32} height={32} />}
              heading="MedLine AI"
              subheading={s.triageConsole}
            />
          }
          footer={
            <Text type="supporting" color="secondary">
              {fmt(s.openCount, {n: openCount})}
            </Text>
          }>
          <SideNavSection title={s.navOverview}>
            <SideNavItem
              label={s.navDashboard}
              icon={<Icon icon={ChartBarIcon} size="sm" />}
              isSelected={view === 'dashboard'}
              onClick={() => setView('dashboard')}
              endContent={
                <Token size="sm" color="default" label={String(stats?.total ?? 0)} />
              }
            />
          </SideNavSection>
          <SideNavSection title={s.navOperations}>
            <SideNavItem
              label={s.navQueue}
              icon={<Icon icon={InboxIcon} size="sm" />}
              isSelected={view === 'queue'}
              onClick={() => setView('queue')}
              endContent={
                <Token size="sm" color="red" label={String(openCount)} />
              }
            />
            <SideNavItem
              label={s.navFacilities}
              icon={<Icon icon={BuildingOfficeIcon} size="sm" />}
              isSelected={view === 'facilities'}
              onClick={() => setView('facilities')}
              endContent={
                <Token size="sm" color="default" label={String(facilities.length)} />
              }
            />
          </SideNavSection>
          <SideNavSection title={s.navSettings}>
            <SideNavItem
              label={s.navDisplay}
              icon={<Icon icon={Cog6ToothIcon} size="sm" />}
              isSelected={view === 'settings'}
              onClick={() => setView('settings')}
            />
          </SideNavSection>
        </SideNav>
      }>
      {view === 'dashboard' && (
        <LayoutContent padding={4}>
          <VStack gap={4}>
            <HStack gap={2} vAlign="center">
              <StackItem size="fill">
                <Heading level={1}>{s.opsDashboard}</Heading>
              </StackItem>
              {langSwitch}
            </HStack>
            <Text type="supporting" color="secondary">
              {s.subtitle} {s.liveNote}
            </Text>
            <KpiRow stats={stats} lang={lang} />
            <HStack gap={3}>
              <StackItem size="fill">
                <TierChart stats={stats} lang={lang} />
              </StackItem>
              <StackItem size="fill">
                <SexChart stats={stats} lang={lang} />
              </StackItem>
            </HStack>
            <AgeChart stats={stats} lang={lang} />
          </VStack>
        </LayoutContent>
      )}
      {view === 'queue' && queue}
      {view === 'facilities' && (
        <LayoutContent padding={4}>
          <VStack gap={4}>
            <HStack gap={2} vAlign="center">
              <StackItem size="fill">
                <Heading level={1}>{s.facilitiesTitle}</Heading>
              </StackItem>
            </HStack>
            <Text type="supporting" color="secondary">
              {s.facilitiesNote}
            </Text>
            <FacilityMap facilities={facilities} tickets={tickets} lang={lang} />
            <FacilityCards facilities={facilities} queues={queues} onSeed={seedSim} lang={lang} />
          </VStack>
        </LayoutContent>
      )}
      {view === 'settings' && (
        <LayoutContent padding={4}>
          <VStack gap={4}>
            <Heading level={1}>{s.displaySettings}</Heading>
            <Text type="body" color="secondary">
              {s.displayNote}
            </Text>
            <HStack gap={3} vAlign="center">
              {langSwitch}
              <Button
                label={sideCollapsed ? s.showStatsPanel : s.hideStatsPanel}
                variant="secondary"
                size="sm"
                onClick={() => setSideCollapsed(v => !v)}
              />
            </HStack>
          </VStack>
        </LayoutContent>
      )}
    </AppShell>
  );
}
