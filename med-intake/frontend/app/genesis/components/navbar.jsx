'use client';

import { MenuIcon, XIcon } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { motion } from "framer-motion";
import { Button } from '@astryxdesign/core/Button';
import ThemeToggle from './theme-toggle';

export default function Navbar() {
    const [isOpen, setIsOpen] = useState(false);
    const [isScrolled, setIsScrolled] = useState(false);
    const pathname = usePathname();

    const links = [
        { name: 'How it works', href: '#how-it-works' },
        { name: 'Languages', href: '#languages' },
        { name: 'Pilot', href: '#pilot' },
        { name: 'Call', href: 'tel:+256323200717' }
    ];

    useEffect(() => {
        const handleScroll = () => {
            if (window.scrollY > 50) {
                setIsScrolled(true);
            } else {
                setIsScrolled(false);
            }
        };

        window.addEventListener('scroll', handleScroll);

        return () => {
            window.removeEventListener('scroll', handleScroll);
        };
    }, [pathname]);

    return (
        <>
            <motion.nav className={`sticky top-0 z-50 flex w-full items-center justify-between px-4 py-3.5 md:px-16 lg:px-24 transition-colors ${isScrolled ? 'bg-white/15 backdrop-blur-lg' : ''}`}
                initial={{ y: -100, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ type: "spring", stiffness: 250, damping: 70, mass: 1 }}
            >
                <a href='https://prebuiltui.com?utm_source=genesis'>
                    <Image src='/assets/logo.svg' alt='logo' className='logo-light h-8.5 w-auto' width={205} height={48} />
                    <Image src='/assets/logo-dark.svg' alt='logo' className='logo-dark h-8.5 w-auto' width={205} height={48} />
                </a>

                <div className='hidden items-center space-x-4 md:flex'>
                    {links.map((link) => (
                        <Link key={link.name} href={link.href} className='transition hover:text-[var(--genesis-accent)]'>
                            {link.name}
                        </Link>
                    ))}
                    <ThemeToggle />
                    <Button label='Sign Up' variant='primary' size='lg' href='/login' as='a' />
                </div>

                <button onClick={() => setIsOpen(true)} className='transition active:scale-90 md:hidden'>
                    <MenuIcon className='size-6.5' />
                </button>
            </motion.nav>

            <div className={`fixed inset-0 z-50 flex flex-col items-center justify-center gap-6 bg-black/20 text-lg font-medium backdrop-blur-2xl transition duration-300 md:hidden ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
                {links.map((link) => (
                    <Link key={link.name} href={link.href} onClick={() => setIsOpen(false)}>
                        {link.name}
                    </Link>
                ))}


                <Link href='/' className='btn glass' onClick={() => setIsOpen(false)}>
                    Sign Up
                </Link>

                <button onClick={() => setIsOpen(false)} className='rounded-md p-2 glass'>
                    <XIcon />
                </button>
            </div >
        </>
    );
}
