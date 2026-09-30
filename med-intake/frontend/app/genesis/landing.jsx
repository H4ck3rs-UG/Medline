'use client';

import './genesis.css';
import Navbar from './components/navbar';
import Footer from './components/footer';
import LenisScroll from './components/lenis-scroll';
import CallToAction from './sections/call-to-action';
import FaqSection from './sections/faq-section';
import Features from './sections/features';
import HeroSection from './sections/hero-section';
import PricingPlans from './sections/pricing-plans';
import TrustedCompanies from './sections/trusted-companies';
import WorkflowSteps from './sections/workflow-steps';

export default function GenesisLanding() {
  return (
    <div className="genesis-scope">
      <LenisScroll />
      <Navbar />
      <main className="px-4">
        <HeroSection />
        <TrustedCompanies />
        <Features />
        <WorkflowSteps />
        <FaqSection />
        <PricingPlans />
        <CallToAction />
      </main>
      <Footer />
    </div>
  );
}
