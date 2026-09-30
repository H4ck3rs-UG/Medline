'use client';
import { GlobeIcon, MailIcon, MessageCircleIcon, PhoneIcon } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";

export default function Footer() {
    const links = [
        { name: 'Terms of Service', href: '#terms-of-service' },
        { name: 'Privacy Policy', href: '#privacy-policy' },
        { name: 'Security', href: '#security' },
        { name: 'Sitemap', href: '#sitemap' },
    ];
    return (
        <motion.footer className="flex flex-col items-center px-4 md:px-16 lg:px-24 justify-center w-full pt-16 mt-40 glass border-0"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
        >
            <a href="https://prebuiltui.com?utm_source=genesis">
                <Image src='/assets/logo.svg' alt='logo' className='logo-light h-8.5 w-auto' width={205} height={48} />
                <Image src='/assets/logo-dark.svg' alt='logo' className='logo-dark h-8.5 w-auto' width={205} height={48} />
            </a>

            <div className="flex flex-wrap items-center justify-center gap-8 py-8">
                {links.map((link, index) => (
                    <Link key={index} href={link.href} className='transition hover:text-gray-300'>
                        {link.name}
                    </Link>
                ))}
            </div>
            <div className="flex items-center gap-6 pb-6">
                <a href="tel:+256323200717" className="hover:-translate-y-0.5 text-gray-200 transition-all duration-300">
                    <PhoneIcon />
                </a>
                <a href="#" className="hover:-translate-y-0.5 text-gray-200 transition-all duration-300">
                    <MailIcon />
                </a>
                <a href="#" className="hover:-translate-y-0.5 text-gray-200 transition-all duration-300">
                    <MessageCircleIcon />
                </a>
                <a href="#" className="hover:-translate-y-0.5 text-gray-200 transition-all duration-300">
                    <GlobeIcon />
                </a>
            </div>
            <hr className="w-full border-white/20 mt-6" />
            <div className="flex flex-col md:flex-row items-center w-full justify-between gap-4 py-4">
                <p>Build Ai agents for free</p>
                <p>Copyright © 2025 <a href="https://prebuiltui.com?utm_source=genesis">PrebuiltUI</a>. All rights reservered.</p>
            </div>
        </motion.footer>
    );
};