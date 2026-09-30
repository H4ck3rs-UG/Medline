// Copyright (c) Meta Platforms, Inc. and affiliates.

'use client';

import {useState, type CSSProperties} from 'react';
import {VStack, HStack, StackItem} from '@astryxdesign/core/Layout';
import {Grid} from '@astryxdesign/core/Grid';
import {Center} from '@astryxdesign/core/Center';
import {Card} from '@astryxdesign/core/Card';
import {Section} from '@astryxdesign/core/Section';
import {Text} from '@astryxdesign/core/Text';
import {Icon} from '@astryxdesign/core/Icon';
import {EmptyState} from '@astryxdesign/core/EmptyState';
import {SquaresPlusIcon, CheckCircleIcon} from '@heroicons/react/24/outline';
import {TextInput} from '@astryxdesign/core/TextInput';
import {Button} from '@astryxdesign/core/Button';
import {Link} from '@astryxdesign/core/Link';
import ModeToggle from '../components/mode-toggle';

const COVER_IMAGE_URL = '/assets/login.jpg';
const DEMO_EMAIL = 'demo@medline.ai';
const DEMO_PASSWORD = 'medline-demo-2026';

// Grid emits minmax(MIN, 1fr) where MIN is a hard floor, so MIN plus the
// grid inset and page padding must fit the narrowest phone or the column is
// clipped. 320 − 2×24 (page) − 2×16 (stacked inset) = 240.
const COLUMN_MIN_WIDTH = 240;
// repeat:'fit' (auto-fit) collapses the two columns to one — expanding to fill —
// below 2×MIN + 32(gap) = 512px. The container query reorders the image and
// tightens the inset at that same point, keyed to the card width (not the
// window) so it never desyncs.
// minHeight:100% fills the host so the centered card never leaves an unpainted
// band; Center's padding prop keeps it off the surface edges.
const pageStyle: CSSProperties = {
  minHeight: '100%',
  backgroundColor: 'var(--color-background-body)',
};
const cardWrap: CSSProperties = {
  width: '100%',
  maxWidth: 1000,
  marginInline: 'auto',
};
const coverImage: CSSProperties = {
  width: '100%',
  height: '100%',
  objectFit: 'cover',
};

// The container query lives in a plain <style> tag so it needs NO CSS compiler.
// - Pad the grid, not the Card: the form's Section escapes Card's
//   --container-padding-* vars, which would cancel the inset on the form side.
//   container-type makes the grid the query container for the stack point.
// - repeat:'fit' (auto-fit) collapses the two columns to one below 511px; the
//   query reorders the image (order:-1) and tightens the inset at that point,
//   keyed to the card width (not the window) so it never desyncs.
const LOGIN_SPLIT_CSS = `
.login-split-grid {
  container-type: inline-size;
  container-name: login-split;
  padding: var(--spacing-8);
}
.login-split-image {
  width: 100%;
  order: 0;
}
@container login-split (max-width: 511px) {
  .login-split-grid {
    padding: var(--spacing-4);
  }
  .login-split-image {
    order: -1;
  }
}
`;

export default function LoginTwoColumn() {
  const [email, setEmail] = useState(DEMO_EMAIL);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [loginFailed, setLoginFailed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const fillDemo = () => {
    setEmail(DEMO_EMAIL);
    setPassword(DEMO_PASSWORD);
    setLoginFailed(false);
  };

  const handleLogin = () => {
    if (email !== DEMO_EMAIL || password !== DEMO_PASSWORD) {
      setLoginFailed(true);
      return;
    }
    setIsLoading(true);
    setLoginFailed(false);
    setTimeout(() => {
      setIsLoading(false);
      setIsSuccess(true);
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 800);
    }, 1200);
  };

  return (
    <Center axis="both" padding={6} style={pageStyle}>
      <style>{LOGIN_SPLIT_CSS}</style>
      <VStack gap={4} width="100%">
        <div style={cardWrap}>
          <Card padding={0} width="100%">
            <Grid
              columns={{minWidth: COLUMN_MIN_WIDTH, repeat: 'fit'}}
              gap={8}
              align="stretch"
              className="login-split-grid">
              {/* Form */}
              <Section variant="transparent" padding={0} height="100%">
                <VStack gap={4} height="100%">
                  <HStack gap={2} vAlign="center">
                    <StackItem size="fill">
                      <HStack gap={2} vAlign="center">
                        <img src="/assets/logo.svg" alt="MedLine AI" className="logo-light" style={{height: 34, width: 'auto'}} />
                        <img src="/assets/logo-dark.svg" alt="MedLine AI" className="logo-dark" style={{height: 34, width: 'auto'}} />
                      </HStack>
                    </StackItem>
                    <ModeToggle />
                  </HStack>

                  <StackItem size="fill">
                    <Center axis="vertical" height="100%">
                      {isSuccess ? (
                        <EmptyState
                          title="You're signed in"
                          description="Redirecting to your dashboard…"
                          icon={<Icon icon={CheckCircleIcon} size="lg" />}
                        />
                      ) : (
                        <VStack gap={4} hAlign="stretch" width="100%">
                          <VStack gap={1}>
                            <Text type="display-1" as="h2">
                              Staff login
                            </Text>
                            <Text type="body" color="secondary" size="sm">
                              Medline AI triage console — demo build
                            </Text>
                          </VStack>

                          <Card padding={3} width="100%">
                            <VStack gap={1}>
                              <Text type="label">Sample login</Text>
                              <Text type="body" size="sm">Email: demo@medline.ai</Text>
                              <Text type="body" size="sm">Password: medline-demo-2026</Text>
                              <Button
                                label="Autofill demo credentials"
                                variant="secondary"
                                size="sm"
                                onClick={fillDemo}
                              />
                            </VStack>
                          </Card>

                          <VStack gap={2}>
                            <TextInput
                              label="Email"
                              isLabelHidden
                              type="email"
                              placeholder="name@company.com"
                              value={email}
                              onChange={setEmail}
                              size="lg"
                            />
                            <VStack gap={1}>
                              <TextInput
                                label="Password"
                                isLabelHidden
                                placeholder="Enter your password"
                                type="password"
                                value={password}
                                onChange={(v: string) => {
                                  setPassword(v);
                                  setLoginFailed(false);
                                }}
                                size="lg"
                                status={
                                  loginFailed
                                    ? {
                                        type: 'error',
                                        message:
                                          'Incorrect password. Try again.',
                                      }
                                    : undefined
                                }
                              />
                              {loginFailed && (
                                <VStack hAlign="end">
                                  <Link
                                    href="#"
                                    size="sm"
                                    color="secondary"
                                    type="supporting">
                                    Forgot your password?
                                  </Link>
                                </VStack>
                              )}
                            </VStack>
                          </VStack>

                          <Button
                            label="Login"
                            variant="primary"
                            size="lg"
                            isLoading={isLoading}
                            onClick={handleLogin}
                          />
                        </VStack>
                      )}
                    </Center>
                  </StackItem>

                  {!isSuccess && (
                    <Text type="supporting" color="secondary">
                      Don&apos;t have an account?{' '}
                      <Link href="#" type="supporting">
                        Sign up
                      </Link>
                    </Text>
                  )}
                </VStack>
              </Section>

              {/* Cover image — the transparent Card clips it to rounded
                  corners (overflow:clip + radius), so the image needs no radius. */}
              <div className="login-split-image">
                <Card
                  variant="transparent"
                  padding={0}
                  width="100%"
                  height="100%">
                  <img
                    style={coverImage}
                    src={COVER_IMAGE_URL}
                    alt="Health worker with patient"
                  />
                </Card>
              </div>
            </Grid>
          </Card>
        </div>

        <VStack hAlign="center">
          <Text type="supporting" color="secondary">
            By clicking continue, you agree to our{' '}
            <Link href="#" type="supporting">
              Terms of Service
            </Link>{' '}
            and{' '}
            <Link href="#" type="supporting">
              Privacy Policy
            </Link>
            .
          </Text>
        </VStack>
      </VStack>
    </Center>
  );
}
