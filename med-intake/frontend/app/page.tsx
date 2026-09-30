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
import {TextInput} from '@astryxdesign/core/TextInput';
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
import {BellAlertIcon, ChartBarIcon, Cog6ToothIcon, InboxIcon} from '@heroicons/react/24/outline';
import {STRINGS, UI_LANGS, type UiLang} from './i18n';

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
  sex: string;
  village: string;
  diagnosis: string;
  diagnosed_by: string;
  transcript: string;
  summary: string;
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
const TIER_LABEL: Record<string, string> = {
  emergency: 'Emergency',
  urgent: 'Urgent',
  self_care: 'Self-care',
};

function TicketRows({
  tickets,
  selectedId,
  onSelect,
  emptyLabel,
}: {
  tickets: Ticket[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  emptyLabel: string;
}) {
  const groups = TIER_ORDER.map(tier => ({
    tier,
    items: tickets.filter(t => t.tier === tier),
  })).filter(g => g.items.length > 0);

  if (groups.length === 0) {
    return (
      <EmptyState
        title={emptyLabel}
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
            <StatusDot variant={TIER_DOT[group.tier]} label={TIER_LABEL[group.tier]} />
            <Text type="label" color="secondary">
              {TIER_LABEL[group.tier]}
            </Text>
            <Text type="supporting" color="secondary">
              {group.items.length}
            </Text>
          </HStack>
          <List density="compact" hasDividers>
            {group.items.map(t => (
              <ListItem
                key={t.id}
                label={`#${t.id} · ${t.caller || 'unknown'}`}
                description={`${t.symptoms} · ${t.reason}`}
                startContent={
                  <StatusDot
                    variant={TIER_DOT[t.tier]}
                    label={t.tier}
                    isPulsing={t.tier === 'emergency' && t.status === 'open'}
                  />
                }
                endContent={
                  <Token
                    size="sm"
                    color={t.status === 'open' ? 'blue' : 'gray'}
                    label={t.status}
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
  closeLabel,
  onClose,
  onDiagnose,
}: {
  ticket: Ticket;
  closeLabel: string;
  onClose: (id: number) => void;
  onDiagnose: (id: number, diagnosis: string, by: string, andClose?: boolean) => void;
}) {
  const [diagnosis, setDiagnosis] = useState(ticket.diagnosis || '');
  const [by, setBy] = useState(ticket.diagnosed_by || '');
  useEffect(() => {
    setDiagnosis(ticket.diagnosis || '');
    setBy(ticket.diagnosed_by || '');
  }, [ticket.id]);
  return (
    <VStack gap={4} style={styles.inspector}>
      <VStack gap={2}>
        <HStack gap={2} vAlign="center">
          <StatusDot variant={TIER_DOT[ticket.tier]} label={ticket.tier} />
          <Text type="supporting" color="secondary">
            #{ticket.id}
          </Text>
          <Token
            size="sm"
            color={ticket.status === 'open' ? 'blue' : 'gray'}
            label={ticket.status}
          />
        </HStack>
        <Heading level={2}>{TIER_LABEL[ticket.tier]}</Heading>
      </VStack>

      <Divider />

      <VStack gap={2}>
        <Heading level={3}>Call summary</Heading>
        <Text type="body">
          {ticket.summary ||
            `${TIER_LABEL[ticket.tier]}: ${ticket.symptoms || 'no symptoms captured'}.`}
        </Text>
        {ticket.transcript ? (
          <Collapsible trigger="View full transcript" defaultIsOpen={false}>
            <Text type="body" color="secondary">
              {ticket.transcript}
            </Text>
          </Collapsible>
        ) : (
          <Text type="supporting" color="secondary">
            No transcript captured for this ticket.
          </Text>
        )}
      </VStack>

      <Divider />

      <VStack gap={2}>
        <Heading level={3}>Doctor diagnosis</Heading>
        {ticket.diagnosis ? (
          <VStack gap={1}>
            <Text type="body">{ticket.diagnosis}</Text>
            {ticket.diagnosed_by && (
              <Text type="supporting" color="secondary">
                by {ticket.diagnosed_by}
              </Text>
            )}
          </VStack>
        ) : null}
        {ticket.status === 'open' && (
          <VStack gap={2}>
            <TextArea
              label="Diagnosis"
              placeholder="Clinical findings, prescription, referral…"
              value={diagnosis}
              onChange={setDiagnosis}
            />
            <TextInput
              label="Doctor name"
              placeholder="Dr. …"
              value={by}
              onChange={setBy}
            />
            <HStack gap={2}>
              <Button
                label="Save diagnosis"
                variant="secondary"
                size="sm"
                onClick={() => onDiagnose(ticket.id, diagnosis, by)}
              />
              <Button
                label={`${closeLabel} with diagnosis`}
                size="sm"
                onClick={() => onDiagnose(ticket.id, diagnosis, by, true)}
              />
            </HStack>
          </VStack>
        )}
      </VStack>

      {ticket.status === 'open' && (
        <HStack gap={2}>
          <Button label={closeLabel} variant="secondary" size="sm" onClick={() => onClose(ticket.id)} />
        </HStack>
      )}

      <Divider />

      <VStack gap={2}>
        <Heading level={3}>Health profile</Heading>
      </VStack>
      <MetadataList columns="single" label={{position: 'start', width: 96}}>
        <MetadataListItem label="Name">
          <Text type="body">{ticket.name || '—'}</Text>
        </MetadataListItem>
        <MetadataListItem label="Age">
          <Text type="body">{ticket.age > 0 ? ticket.age : '—'}</Text>
        </MetadataListItem>
        <MetadataListItem label="Sex">
          <Text type="body">{ticket.sex || '—'}</Text>
        </MetadataListItem>
        <MetadataListItem label="Village">
          <Text type="body">{ticket.village || '—'}</Text>
        </MetadataListItem>
        <MetadataListItem label="Caller">
          <Text type="body">{ticket.caller || '—'}</Text>
        </MetadataListItem>
        <MetadataListItem label="Language">
          <Text type="body">{ticket.lang}</Text>
        </MetadataListItem>
        <MetadataListItem label="Symptoms">
          <Text type="body">{ticket.symptoms || '—'}</Text>
        </MetadataListItem>
        <MetadataListItem label="Reason">
          <Text type="body">{ticket.reason}</Text>
        </MetadataListItem>
        <MetadataListItem label="Confidence">
          <Text type="body">{ticket.confidence > 0 ? `${ticket.confidence}%` : '—'}</Text>
        </MetadataListItem>
      </MetadataList>
    </VStack>
  );
}

function StatsSidebar({stats}: {stats: Stats | null}) {
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
    obj?: Record<string, number>,
    variantOf?: (k: string) => 'error' | 'warning' | 'success' | 'accent' | 'neutral',
  ) => (
    <VStack gap={2} key={title}>
      <Text type="label" color="secondary">
        {title}
      </Text>
      {obj && Object.keys(obj).length > 0 ? (
        Object.entries(obj)
          .sort((a, b) => b[1] - a[1])
          .map(([k, v]) => bar(k, v, variantOf?.(k) ?? 'accent'))
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
        <Heading level={3}>Overview</Heading>
        <Text type="supporting" color="secondary">
          {stats ? `${stats.open} open / ${stats.total} total` : 'Loading…'}
        </Text>
      </VStack>
      <Divider />
      {section('By tier', stats?.by_tier, k => TIER_VARIANT[k as keyof typeof TIER_VARIANT] ?? 'accent')}
      <Divider />
      {section('By sex', stats?.by_sex)}
      <Divider />
      {section('By age', stats?.by_age_band)}
      <Divider />
      {section('By language', stats?.by_lang)}
      <Divider />
      {section('By village', stats?.by_village, () => 'neutral')}
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

function KpiRow({stats}: {stats: Stats | null}) {
  const kpis = [
    {label: 'Total tickets', value: stats?.total ?? 0},
    {label: 'Open', value: stats?.open ?? 0},
    {label: 'Emergency', value: stats?.by_tier?.emergency ?? 0},
    {label: 'Urgent', value: stats?.by_tier?.urgent ?? 0},
    {label: 'Self-care', value: stats?.by_tier?.self_care ?? 0},
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

function TierChart({stats}: {stats: Stats | null}) {
  const data = ['emergency', 'urgent', 'self_care'].map(tier => ({
    name: tier,
    count: stats?.by_tier?.[tier] ?? 0,
  }));
  return (
    <Card>
      <VStack gap={3}>
        <Heading level={3}>Tickets by urgency tier</Heading>
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
                <Cell key={d.name} fill={CHART_FILL[d.name]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </VStack>
    </Card>
  );
}

function AgeChart({stats}: {stats: Stats | null}) {
  const data = Object.entries(stats?.by_age_band ?? {})
    .sort((a, b) => b[1] - a[1])
    .map(([name, count]) => ({name, count}));
  return (
    <Card>
      <VStack gap={3}>
        <Heading level={3}>Tickets by age band</Heading>
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

function SexChart({stats}: {stats: Stats | null}) {
  const data = Object.entries(stats?.by_sex ?? {}).map(([name, value]) => ({
    name,
    value,
  }));
  return (
    <Card>
      <VStack gap={3}>
        <Heading level={3}>Tickets by sex</Heading>
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={48} outerRadius={80}>
              {data.map(d => (
                <Cell key={d.name} fill={CHART_FILL[d.name] ?? 'var(--color-neutral)'} />
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

type View = 'dashboard' | 'queue' | 'settings';

export default function Page() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
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

  useEffect(() => {
    load();
    loadStats();
    const i = setInterval(() => {
      load();
      loadStats();
    }, 3000);
    return () => clearInterval(i);
  }, []);

  const close = (id: number) =>
    fetch(`${API}/api/tickets/${id}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({status: 'closed'}),
    }).then(() => {
      load();
      loadStats();
    });

  const diagnose = (id: number, diagnosis: string, by: string, andClose = false) =>
    fetch(`${API}/api/tickets/${id}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        status: andClose ? 'closed' : 'open',
        diagnosis,
        diagnosed_by: by,
      }),
    }).then(() => {
      load();
      loadStats();
    });

  const isNarrow = useMediaQuery('(max-width: 1024px)');
  const inspectorPanel = useResizable({defaultSize: 380, minSize: 320, maxSize: 480});

  const visible = useMemo(
    () => (tierFilter === 'all' ? tickets : tickets.filter(t => t.tier === tierFilter)),
    [tickets, tierFilter],
  );
  const selected = visible.find(t => t.id === selectedId) ?? null;
  const openCount = tickets.filter(t => t.status === 'open').length;
  const s = STRINGS[lang];

  const queue = (
    <Layout
      height="fill"
      start={
        isNarrow || sideCollapsed ? undefined : (
          <LayoutPanel width={280} padding={0} label="Population stats" hasDivider>
            <StatsSidebar stats={stats} />
          </LayoutPanel>
        )
      }
      header={
        <LayoutHeader hasDivider>
          <HStack gap={3} vAlign="center">
            {!isNarrow && (
              <Button
                label={sideCollapsed ? 'Show stats' : 'Hide stats'}
                variant="secondary"
                size="sm"
                onClick={() => setSideCollapsed(v => !v)}
              />
            )}
            <StackItem size="fill">
              <HStack gap={2} vAlign="center">
                <Heading level={1}>{s.title}</Heading>
                <Text type="supporting" color="secondary">
                  {openCount} open
                </Text>
              </HStack>
            </StackItem>
            <SegmentedControl
              label="Filter by tier"
              value={tierFilter}
              onChange={setTierFilter}
              size="sm">
              <SegmentedControlItem label="All" value="all" />
              <SegmentedControlItem label="Emergency" value="emergency" />
              <SegmentedControlItem label="Urgent" value="urgent" />
              <SegmentedControlItem label="Self-care" value="self_care" />
            </SegmentedControl>
            <SegmentedControl
              label={s.language}
              value={lang}
              onChange={v => {
                setLang(v as UiLang);
                try {
                  localStorage.setItem(LANG_KEY, v);
                } catch {}
              }}
              size="sm">
              {(Object.keys(UI_LANGS) as UiLang[]).map(l => (
                <SegmentedControlItem key={l} label={UI_LANGS[l]} value={l} />
              ))}
            </SegmentedControl>
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
                emptyLabel={s.empty}
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
              label="Resize inspector"
            />
            <LayoutPanel width={inspectorPanel.size} padding={0} label="Ticket details">
              {selected ? (
                <TicketInspector ticket={selected} closeLabel={s.close} onClose={close} onDiagnose={diagnose} />
              ) : (
                <EmptyState
                  title="No ticket selected"
                  description="Select a ticket to see details."
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
          aria-label="Primary"
          collapsible={isNarrow ? false : true}
          header={<SideNavHeading heading="Med-Intake" subheading="Triage console" />}
          footer={
            <Text type="supporting" color="secondary">
              {openCount} open
            </Text>
          }>
          <SideNavSection title="Overview">
            <SideNavItem
              label="Dashboard"
              icon={<Icon icon={ChartBarIcon} size="sm" />}
              isSelected={view === 'dashboard'}
              onClick={() => setView('dashboard')}
              endContent={
                <Token size="sm" color="default" label={String(stats?.total ?? 0)} />
              }
            />
          </SideNavSection>
          <SideNavSection title="Operations">
            <SideNavItem
              label="Triage queue"
              icon={<Icon icon={InboxIcon} size="sm" />}
              isSelected={view === 'queue'}
              onClick={() => setView('queue')}
              endContent={
                <Token size="sm" color="red" label={String(openCount)} />
              }
            />
          </SideNavSection>
          <SideNavSection title="Settings">
            <SideNavItem
              label="Display"
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
                <Heading level={1}>Operations dashboard</Heading>
              </StackItem>
              <SegmentedControl
                label={s.language}
                value={lang}
                onChange={v => {
                  setLang(v as UiLang);
                  try {
                    localStorage.setItem(LANG_KEY, v);
                  } catch {}
                }}
                size="sm">
                {(Object.keys(UI_LANGS) as UiLang[]).map(l => (
                  <SegmentedControlItem key={l} label={UI_LANGS[l]} value={l} />
                ))}
              </SegmentedControl>
            </HStack>
            <Text type="supporting" color="secondary">
              {s.subtitle} Live from /api/stats, refreshes every 3s.
            </Text>
            <KpiRow stats={stats} />
            <HStack gap={3}>
              <StackItem size="fill">
                <TierChart stats={stats} />
              </StackItem>
              <StackItem size="fill">
                <SexChart stats={stats} />
              </StackItem>
            </HStack>
            <AgeChart stats={stats} />
          </VStack>
        </LayoutContent>
      )}
      {view === 'queue' && queue}
      {view === 'settings' && (
        <LayoutContent padding={4}>
          <VStack gap={4}>
            <Heading level={1}>Display settings</Heading>
            <Text type="body" color="secondary">
              Dashboard language and stats panel visibility.
            </Text>
            <HStack gap={3} vAlign="center">
              <SegmentedControl
                label={s.language}
                value={lang}
                onChange={v => {
                  setLang(v as UiLang);
                  try {
                    localStorage.setItem(LANG_KEY, v);
                  } catch {}
                }}
                size="sm">
                {(Object.keys(UI_LANGS) as UiLang[]).map(l => (
                  <SegmentedControlItem key={l} label={UI_LANGS[l]} value={l} />
                ))}
              </SegmentedControl>
              <Button
                label={sideCollapsed ? 'Show stats panel' : 'Hide stats panel'}
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
